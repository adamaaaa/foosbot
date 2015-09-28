import numpy

diffest = {1: 0.1,  # Note this top number was made up...
           2: 0.20910457648873165,
           3: 0.36334036902537986,
           4: 0.51804560036712499,
           5: 0.70330207824055102,
           6: 0.93288696252689385,
           7: 1.2193649155654196,
           8: 1.6151220275410325,
           9: 2.2344370998155201,
           10: 3.4282444625620343}

alpha = 0.3


def getDiffEst(sd):
    if sd < 0:
        return -diffest[-sd]
    else:
        return diffest[sd]


def getRankChange(r1, r2, s1, s2):

    rd = r2 - r1
    sd = s2 - s1

    de = getDiffEst(sd)

    change = de - rd

    return change * alpha


def getAllUids(matches):
    allu = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allu for x in y]))


def getRankShift(rankguess, m, uids, u):
    gamescore = getDiffEst(m.score2 - m.score1)
    rd = 0.0
    # print m.players1, m.players2, u, gamescore

    for p in m.players1:
        if p != u:
            rd -= rankguess[uids.index(p)] / float(len(m.players1))

    for p in m.players2:
        if p != u:
            rd += rankguess[uids.index(p)] / float(len(m.players1))

    # print rd

    if u in m.players2:
        nteam = len(m.players2)
        return nteam*(gamescore - rd)
    elif u in m.players1:
        nteam = len(m.players1)
        return nteam*(rd - gamescore)
    else:
        raise Exception("User didn't play?")


def updateSingle(rankguess, matches, uids, i, alpha):
    u = uids[i]
    goal = 0.0
    count = 0
    for m in matches:
        if u in m.players1 or u in m.players2:
            goal += getRankShift(rankguess, m, uids, u)
            count += 1

    if count == 0:
        return 0.0

    targ = goal / float(count)

    before = rankguess[i]
    after = alpha*targ + (1-alpha)*rankguess[i]
    diff = after - before
    # print "%s: %f => %f" % (u, before, after)
    return after, diff


def updateAll(rankguess, matches, uids, alpha):
    totmove = 0.0
    newranks = numpy.zeros_like(rankguess)
    for i in range(len(uids)):
        after, diff = updateSingle(rankguess, matches, uids, i, alpha)
        newranks[i] = after
        totmove += abs(diff)
    return newranks, totmove / float(len(uids))


def getRankings(matches):
    uids = getAllUids(matches)
    rankguess = numpy.zeros(len(uids))

    last = 1.0
    alpha = 1.0
    for i in range(100):
        rankguess, move = updateAll(rankguess, matches, uids, alpha)
        print alpha, move
        if move > last * 0.999:
            alpha /= 2.0
        if move < 1e-20:
            break
        last = move

    return {k: v for k, v in zip(uids, rankguess)}
