import re
import sys
import nltk
import json
import emoji
import numpy as np
from collections import Counter, defaultdict
from nltk.corpus import stopwords, words
from itertools import dropwhile, combinations

from datetime import datetime

from reddit import startup, grab


def posts(R, SUB, LIMIT=500):
    return [s for s in R.subreddit(SUB).new(limit=LIMIT)]


def ldict():
    fname = '/usr/share/dict/words'
    with open(fname) as f:
        read_data = f.read()
    return [w.lower() for w in read_data.split('\n')]


def wdict():
    fname = 'words_dictionary.json'
    with open(fname) as rfp:
        data = json.load(rfp)
    return data


def read_tdict():
    fname = 'training.json'
    with open(fname) as rfp:
        data = json.load(rfp)
    return data


def save_tdict(tdict):
    fname = 'training.json'
    with open(fname, 'w') as wfp:
        json.dump(tdict, wfp)


def update_tdict(tdict):
    data = read_tdict()
    data['targets'] += tdict['targets']
    data['labels'] += tdict['labels']
    data['shape'] = [2, len(data['targets'])]

    save_tdict(data)


def author(postObject):
    try:
        a = postObject.author.name
    except:
        a = '[Deleted]'

    return a


def text(postObject):
    return postObject.selftext


def title(postObject):
    return postObject.title


def scName(postObject):

    pTitle = title(postObject)
    pText = text(postObject)

    post = ' '.join([pTitle, pText])
    stop = stopwords.words('english')

    post = ' '.join([i for i in post.split() if i not in stop])
    post = ' '.join(set(post.split()))
    post = ' '.join([emoji.get_emoji_regexp().sub(u'', i) for i in post.split()])

    sentences = nltk.sent_tokenize(post)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]

    entities = []

    for i in sentences:
        for j in i:
            if j[1] == 'NN' or j[1] == 'NNP':
                entities.append(j[0])

    return entities


def flatten(S):
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])


def usrDict(posts):
    a = datetime.now()
    users = {}
    word_list = ldict()
    word_dict = wdict()

    spec_0 = re.compile('[\\\\]+|\++|[/]+')

    i = 0
    j = len(posts)
    for p in posts:
        sys.stdout.write('\rPROCESSING:\t{0:.2f}%'.format((i/float(j))*100))
        sys.stdout.flush()

        auth = author(p)
        t = np.setdiff1d([spec_0.sub('', w.lower()) for w in set(scName(p)) if len(w) > 3], word_list).tolist()
        try:
            users[auth]['text'].append(t)
            users[auth]['post'].append(p)
        except KeyError as e:
            users[auth] = {
                'text': [t],
                'post': [p]
            }
        i += 1
    q = Counter(flatten([users[u]['text'] for u in users.keys()]))
    for key, count in dropwhile(lambda key_count: key_count[1] >= 2, q.most_common()):
        del q[key]

    spec_1 = re.compile('[\W_]+')

    l = list(q.keys())

    i = 0
    j = len(l)
    for t in l:
        sys.stdout.write('\rPRUNING:\t{0:.2f}%'.format((i/float(j))*100))
        sys.stdout.flush()
        if len(t) <= 3:
            del q[t]
        if spec_1.match(t):
            del q[t]
        try:
            x = word_dict[t]
            del q[t]
        except KeyError as e:
            pass
        if t in words.words():
            del q[t]
        i += 1

    b = datetime.now()
    s = 24 * 60 * 60
    d = b - a
    dt = divmod(d.days * s + d.seconds, 60)
    print('\rPRE PROCESSING COMPLETED: {}m {}s'.format(dt[0], dt[1]))
    return dict(q), users


def findUsr(username, users):
    fUsers = []
    fPosts = []
    for user, d in users.items():
        for i in range(0, len(d['text'])):
            if username in flatten(d['text'][i]):
                fUsers.append(user)
                fPosts.append(d['post'][i])
    return fUsers, fPosts


def hPrint(data):
    k = list(data.keys())
    for i in range(0, len(data)):
        print("[{}]: {},\t{}".format(i, k[i], data[k[i]]))


def report(analysis):
    for sc in analysis.keys():
        print('SC: {}'.format(sc))
        for i in range(0, len(analysis[sc]['accounts'])):
            print("\t/u/{} ({})".format(analysis[sc]['accounts'][i], analysis[sc]['posts'][i].shortlink))
        print("")


def temporalize(analysis, hours):
    h = hours * 60 * 60
    r = {}
    for sc in analysis:
        t = [datetime.fromtimestamp(p.created_utc) for p in analysis[sc]['posts']]
        if (t[0] - t[-1]).seconds <= h:             # all posts violate
            r[sc] = dict(analysis[sc])
        else:                                       # only some do (...fuck)
            r[sc] = {
                'accounts': [],
                'posts': []
            }

            i = [x for x in range(0, len(t))]
            l = list(combinations(i, 2))
            bad = set()

            for pair in sorted(l):
                if (t[pair[1]] - t[pair[0]]).seconds <= h:
                    bad.add(pair[1])
                    bad.add(pair[2])

            for b in bad:
                r[sc]['accounts'].append(analysis['accounts'][b])
                r[sc]['posts'].append(analysis['posts'][b])

            if not r[sc]['accounts']:
                del r[sc]

    return r


def analyze(indices, data, users):
    l = list(data.keys())
    r = {}

    for index in indices:
        r[l[index]] = {
            'accounts': [],
            'posts': []
        }
        u, p = findUsr(l[index], users)
        for ui in u:
            r[l[index]]['accounts'].append(ui)
        for pi in p:
            r[l[index]]['posts'].append(pi)

    return r


def double_agent(indices, data, users, myposts, hours):
    r = analyze(indices, data, users)
    r = temporalize(r, hours)
    period(myposts)
    report(r)


def period(myposts):
    newest = datetime.fromtimestamp(myposts[0].created_utc)
    oldest = datetime.fromtimestamp(myposts[-1].created_utc)
    # delta = newest - oldest
    # s = 24 * 60 * 60
    # dt = divmod(delta.days * s + d.seconds, 60)
    print('FOR TIME BETWEEN {} -- {}'.format(oldest.strftime('%c'), newest.strftime('%c')))


def train_format(vals, user_indices):
    targets = list(vals)
    labels =  list()
    for i in range(0, len(targets)):
        if i in user_indices:
            labels.append(1)
        else:
            labels.append(0)

    return targets, labels




def main():
    r = startup()
    sub = grab('DOUBLE')
    p = posts(r, sub[0], LIMIT=1000)
    data, users = usrDict(p)

    hPrint(data)


def xf(t):
    f= {}
    f['length'] = len(t)
    f['numbers'] = sum(c.isdigit() for c in t)
    f['letters'] = sum(c.isalpha() for c in t)
    f['others'] = f['length'] - f['letters'] - f['numbers']
    f['word'] = t

    return f


def xform(targets, labels):
    return [(xf(targets[i]), labels[i]) for i in range(0, len(targets))]


def testClass(classifier, data, indices):
    q = []

    l = list(data.keys())
    for i in range(0, len(l)):
        if i in indices:
            q.append(1)
        else:
            q.append(0)

    test = xform(l, q)

    predict = []

    for k in data.keys():
        v = classifier.classify(xf(k))
        if v:
            predict.append(1)
        else:
            predict.append(0)

    predicted = xform(l, predict)

    print(nltk.classify.accuracy(classifier, test))
    return predicted, test

def fp(p, t):
    fp = 0
    fn = 0
    tp = 0
    tn = 0
    for i in range(0, len(p)):
        if p[i][1] < t[i][1]:
            fn += 1
        elif p[i][1] > t[i][1]:
            fp += 1
        elif p[i][1] == 1 and t[i][1] == 1:
            tp += 1
        else:
            tn += 1

    print("{}:\t{}".format("True Positive", tp / float(len(p))))
    print("{}:\t{}".format("True Negative", tn / float(len(p))))
    print("{}:\t{}".format("False Positive", fp / float(len(p))))
    print("{}:\t{}".format("False Negative", fn / float(len(p))))
