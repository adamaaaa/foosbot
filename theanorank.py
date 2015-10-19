from theano import tensor as T
# import theano
import datetime
import math
import numpy


def _getModel():
    s1, s2 = T.dvectors('s1', 's2')
    t1, t2 = T.dmatrices('t1', 't2')
    gw = T.dvector('gw')
    prank = T.dvector('prank')

    r1 = T.dot(t1, prank)
    r2 = T.dot(t2, prank)

    erd = T.exp(r2 - r1)
    p = erd / (erd + 1)

    loglterms = gw * ((s1 * T.log(1 - p)) + (s2 * T.log(p)))

    logl = -T.sum(loglterms)

    gradf = T.grad(logl, prank)

    return s1, s2, t1, t2, gw, prank, loglterms, logl, gradf


_modelcache = None


def getModel():
    global _modelcache
    if _modelcache is None:
        _modelcache = _getModel()

    return _modelcache


def getAllUids(matches):
    allu = [m.players1 + m.players2 for m in matches]
    return list(set([x for y in allu for x in y]))


def getRanking(matches):

    uids = getAllUids(matches)

    s1, s2, t1, t2, gw, prank, loglterms, logl, gradf = getModel()

    s1_r = numpy.zeros(len(matches))
    s2_r = numpy.zeros(len(matches))
    t1_r = numpy.zeros((len(matches), len(uids)))
    t2_r = numpy.zeros((len(matches), len(uids)))
    gw_r = numpy.zeros(len(matches))
    now = datetime.datetime.now()
    w_coeff = - math.log(0.5) / (60*60*24*7.0)

    for i, m in enumerate(matches):
        s1_r[i] = m.score1
        s2_r[i] = m.score2
        p1 = m.players1
        p2 = m.players2
        diff = (now - m.when).total_seconds()
        gw_r[i] = math.exp(-diff * w_coeff)

        for p in p1:
            t1_r[i][uids.index(p)] = 1.0/len(p1)

        for p in p2:
            t2_r[i][uids.index(p)] = 1.0/len(p2)

    prank_r = numpy.array(numpy.random.normal(0.0, 0.01, len(uids)))
    last = 1e100
    alpha = 0.25
    for i in range(10000):
        prev = numpy.copy(prank_r)
        prank_r -= alpha*gradf.eval({gw: gw_r, s1: s1_r, s2: s2_r, t1: t1_r, t2: t2_r, prank: prank_r})
        prank_r -= numpy.mean(prank_r)
        score = logl.eval({gw: gw_r, s1: s1_r, s2: s2_r, t1: t1_r, t2: t2_r, prank: prank_r})
        if score > last or numpy.isnan(score):
            alpha /= 2.0
    #         print prev[:2], prank_r[:2]
            prank_r = prev
        else:
            if abs(score - last) < 1e-20:
                break
            last = score
        if i % 100 == 0:
            print i, prank_r[:2], prev[:2], score, alpha

    return {k: v for k, v in zip(uids, prank_r)}
