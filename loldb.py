import pickle
import ranking
import numpy
import collections
import datetime


_dbfile = 'foosdb.pickle'
_dbhandle = None


def _getdb():
    global _dbhandle
    if _dbhandle is None:
        try:
            _dbhandle = pickle.load(open(_dbfile))
        except:
            print "Unable to load database, creating new one"
            _dbhandle = _newdb()
    return _dbhandle


def _commitback():
    if _dbhandle is None:
        raise Exception("Handle is None?")
    pickle.dump(_dbhandle, open(_dbfile, 'w'))


def _newdb():
    return {'matches': {}}


def getrankings():
    return ranking.getRankings(_getdb()['matches'].values())


def getmatches():
    return _getdb()['matches'].values()


def getrecent(n=3):
    return sorted(_getdb()['matches'].values(),
                  key=lambda x: x.when, reverse=True)[:n]


def getgamecounts():
    matches = getmatches()
    r = collections.defaultdict(int)
    for m in matches:
        for p in m.players1 + m.players2:
            r[p] += 1
    return r


def getlastgame(uid):
    matches = getmatches()
    times = []
    for m in matches:
        if uid in m.players1 + m.players2:
            times.append(m)
    return sorted(times, key=lambda x: x.when)[-1]


def getlastgameall():
    matches = getmatches()
    latest = collections.defaultdict(lambda: datetime.datetime(1900, 1, 1))
    for m in matches:
        for uid in m.players1 + m.players2:
            if m.when > latest[uid]:
                latest[uid] = m.when
    return latest


def _newid():
    return ''.join(numpy.random.choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'], 8))


def addmatch(m):
    mid = None
    while mid is None or mid in _getdb()['matches']:
        mid = _newid()

    _getdb()['matches'][mid] = m
    _commitback()
    return mid


def deletematch(mid):
    del _getdb()['matches'][mid]
    _commitback()
