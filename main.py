import operator
from datetime import datetime
from reddit import startup, subs

def time_convert(EPOCH):
    return datetime.fromtimestamp(submission.created_utc).strftime('%c')

def dow_time(POSTS):
    Days = {0:"Monday",
            1:"Tuesday",
            2:"Wednesday",
            3:"Thursday",
            4:"Friday",
            5:"Saturday",
            6:"Sunday"}
    week = {0:[0]*24,
            1:[0]*24,
            2:[0]*24,
            3:[0]*24,
            4:[0]*24,
            5:[0]*24,
            6:[0]*24}
    for p in POSTS:
        week[datetime.fromtimestamp(p.created_utc).weekday()][datetime.fromtimestamp(p.created_utc).hour] += 1
    wk = list()

    for i in range(168):
        order = {0:sum(week[0]),
                 1:sum(week[1]),
                 2:sum(week[2]),
                 3:sum(week[3]),
                 4:sum(week[4]),
                 5:sum(week[5]),
                 6:sum(week[6]),
                }
        x = max(order.items(), key=operator.itemgetter(1))[0]
        y = week[x].index(max(week[x]))
        wk.append([x,y])
        week[x][y] = 0

    wk = ["{0} at {1}".format(Days[k[0]], k[1]) for k in wk[:10]]
    return wk


def posts(R, SUB):
    return [s for s in R.subreddit(SUB).hot(limit=1000)]


def week_dict(R):
    my_dict = dict()
    SUBS, SHORTS = subs()
    for i in range(0, len(SUBS)):
        my_dict[SHORTS[i]] = dow_time(posts(R, SUBS[i]))
    return my_dict


def week_sched(WEEK_DICT):
    my_dict = {
        'SUN': {k:list() for k in range(0, 24)},
        'MON': {k:list() for k in range(0, 24)},
        'TUE': {k:list() for k in range(0, 24)},
        'WED': {k:list() for k in range(0, 24)},
        'THU': {k:list() for k in range(0, 24)},
        'FRI': {k:list() for k in range(0, 24)},
        'SAT': {k:list() for k in range(0, 24)},
    }
    Days = {
        "Sunday": "SUN",
        "Monday" : "MON",
        "Tuesday": "TUE",
        "Wednesday": "WED",
        "Thursday": "THU",
        "Friday": "FRI",
        "Saturday": "SAT",
    }
    for sub in WEEK_DICT:
        for i in WEEK_DICT[sub]:
            d = i.split(' at ')[0]
            t = int(i.split(' at ')[1])
            my_dict[Days[d]][t].append(sub)
    return my_dict


def print_sched(SCHED):
    header = list(SCHED.keys())
    lines = []
    for hour in range(0, 24):
        line = []
        for day in header:
            line.append(SCHED[day][hour])
        lines.append(line)
    format_row = "{:<20}" * 8
    print(format_row.format("", *header))

    # for line in lines:
    #     print(format_row.format("", *[" ".join(i) for i in line]))

    for hour, line in zip(range(0, 25), lines):
        print(format_row.format(hour, *[" ".join(i) for i in line]))



def main():
    r = startup()
    week = week_dict(r)
    sched = week_sched(week)
    print_sched(sched)
