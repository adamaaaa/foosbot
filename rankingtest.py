#!/usr/bin/env python

import ranking
import datetime
import core


def getMatch(p1a, p1b, p2a, p2b, s1, s2):
    return core.Match([p1a, p1b], [p2a, p2b], s1, s2, datetime.datetime.now())

matches = []
matches.append(getMatch("1", "2", "3", "4", 6, 10))
matches.append(getMatch("1", "2", "3", "4", 10, 8))
matches.append(getMatch("1", "2", "3", "4", 8, 10))
matches.append(getMatch("1", "3", "5", "6", 2, 10))

print ranking.getRankings(matches)
