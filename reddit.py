import praw
import json
from configparser import ConfigParser


def startup():
    config = ConfigParser()
    config.read('config.cfg')

    ID = config.get('info', 'ID')
    SECRET = config.get('info', 'SECRET')
    AGENT = config.get('info', 'AGENT')

    return praw.Reddit(client_id = ID,
                     client_secret = SECRET,
                     user_agent = AGENT)


def subs():
    config = ConfigParser()
    config.read('config.cfg')

    ss = json.loads(config.get('reddit', 'SUBS'))
    sh = json.loads(config.get('reddit', 'SHORT'))

    return ss, sh


def grab(thing):
    config = ConfigParser()
    config.read('config.cfg')

    data = json.loads(config.get('reddit', thing))
    return data


def main():
    startup()


if __name__ == '__main__':
    main()