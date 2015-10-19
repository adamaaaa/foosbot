import json
import traceback
import sys
import core
import datetime
import loldb
import numpy
import ranking
import theanorank


_fooschan = 'C0BCN8XD4'
_adminuser = 'U02AYNXND'
_nextid = 1


def simpleMsg(text):
    global _nextid
    m = {'type': 'message', 'channel': _fooschan, 'id': _nextid, 'text': text}
    _nextid += 1
    return m


def simpleResp(text):
    return [simpleMsg(text)]


def processSubmit(args):
    p1 = []
    p2 = []

    try:
        a1 = args.pop(0)
        if not a1.startswith("<@"):
            return simpleResp("Didn't recognise user %s" % (a1))
        p1.append(a1[2:-1])

        a2 = args.pop(0)
        if a2.startswith("<@"):
            p1.append(a2[2:-1])
            a2 = args.pop(0)

        if not a2.startswith("vs"):
            return simpleResp("Expected to see vs now")

        a3 = args.pop(0)
        if not a3.startswith("<@"):
            return simpleResp("Didn't recognise user %s" % (a3))
        p2.append(a3[2:-1])

        a4 = args.pop(0)
        if a4.startswith("<@"):
            p2.append(a4[2:-1])
            a4 = args.pop(0)

        if '-' in a4:
            b4 = a4.split('-')
            s1 = int(b4[0])
            s2 = int(b4[1])
        else:
            s1 = int(a4)
            a5 = args.pop(0)
            if a5 == '-':
                a5 = args.pop(0)
            s2 = int(a5)
            if s2 < 0:
                s2 = -s2  # Deal with case where someone writes 2 -10 by mistake

        if max(s1, s2) < 10:
            return simpleResp("Someone should have scored at least 10 points!")

        if max(s1, s2) > 10 and abs(s2 - s1) != 2:
            return simpleResp("Someone should have been two points ahead at the end?")

        if min(s1, s2) < 0:
            return simpleResp("")

        m = core.Match(p1, p2, s1, s2, datetime.datetime.now())

        mid = loldb.addmatch(m)

        return simpleResp("Match %s successfully submitted" % (mid))

    except Exception as e:
        print str(e)
        return simpleResp("I'm sorry I didn't understand that")


def mangleit(x, iseq):
    c = '.'
    if x[0] in iseq:
        c = '='
    return "%i%s %s" % (x[0], c, x[1])


def formatRanking(slack, d, mc):
    r = []
    l = 1e6
    c = 0
    tc = 0
    iseq = []

    allusers = slack.users.list().body

    if not 'ok' in allusers:
        raise Exception("Couldn't get users...")

    for n in sorted(d.items(), key=lambda x: x[1], reverse=True):
        tc += 1
        if n[1] < l - 0.1:
            c = tc
            l = n[1]
        else:
            iseq.append(c)
        name = getNiceName(allusers, n[0])
        ss = "%.1f" % (10.0 + (n[1]*10.0))
        if mc[n[0]] < 3:
            ss = '*'
        r.append((c, "%s (%s)" % (name, ss)))

    r = map(lambda x: mangleit(x, iseq), r)

    return r


def getNiceName(allusers, uid):
    members = allusers['members']
    name = uid
    dn = [x for x in members if x['id'] == uid]
    if len(dn) == 1:
        name = dn[0]['name']
    return name


def getTimeSinceDesc(w):
    delta = datetime.datetime.now() - w

    if delta.days > 0:
        return "%i days ago" % (delta.days)

    if delta.seconds > 3600:
        return "%i hours ago" % (delta.seconds / 3600)

    if delta.seconds > 60:
        return "%i minutes ago" % (delta.seconds / 60)

    return "just now"


def formatMatch(allusers, m):
    nnf = lambda u: getNiceName(allusers, u)
    part1 = ' '.join(map(nnf, m.players1))
    part2 = ' '.join(map(nnf, m.players2))
    tsd = getTimeSinceDesc(m.when)

    return '%s vs %s %i - %i (%s)' % (part1, part2, m.score1, m.score2, tsd)


def processRank(slack, args):
    m = loldb.getmatches()
    # d = ranking.getRankings(m)
    td = theanorank.getRanking(m)
    # print d
    print td
    mc = ranking.countGames(m)
    out = formatRanking(slack, td, mc)
    legstr = ''
    if numpy.min(mc.values()) < 3:
        legstr = '\n* has played less than 3 games'
    return simpleResp('```' + '\n'.join(out) + legstr + '```')


def processDelete(args):
    loldb.deletematch(args[0])
    return simpleResp("Match deleted!")


def processRecent(slack, args):
    allusers = slack.users.list().body
    rm = loldb.getrecent(3)
    fm = lambda m: formatMatch(allusers, m)
    msgt = 'Last 3 games:\n' + '\n'.join(map(fm, rm))
    return simpleResp(msgt)


def processPredict(args):
    d = loldb.getrankings()

    players1 = []
    while len(args) > 0 and args[0].startswith('<@'):
        players1.append(args.pop(0)[2:-1])

    if len(args) == 0:
        return simpleResp("Was expecting a 'vs' at some point")

    args.pop(0)

    players2 = []
    while len(args) > 0 and args[0].startswith('<@'):
        players2.append(args.pop(0)[2:-1])

    r1 = []
    r2 = []
    for p in players1:
        if not p in d:
            return simpleResp("I don't know the rank of <@%s>" % p)
        r1.append(d[p])

    for p in players2:
        if not p in d:
            return simpleResp("I don't know the rank of <@%s>" % p)
        r2.append(d[p])

    sd = numpy.mean(r2) - numpy.mean(r1)

    pred = ranking.generatePrediction(sd, 10000)

    line1 = "I predict team 2 has a %.0f%% chance of winning" % (pred[0]*100.0)
    line2 = "The most likely outcome is %i - %i (%.0f%% chance)" % \
            (pred[1][0], pred[1][1], pred[2]*100.0)

    return simpleResp('\n'.join([line1, line2]))


def processHelp(args):
    ht = {'result': "Submit a match result\n```@foosbot: result @dave @steve vs @bob @jon 10 - 6```",
          'rank': "See a table of player rankings based on recent results",
          'delete': "Delete a match entered incorrectly or by mistake\n```@foosbot: delete abcdef123456```",
          'recent': "See recently played matches",
          'predict': "Predict a match result\n```@foosbot: predict @steve vs @dave```"}

    sht = 'Commands are %s and %s. For more help, type help <command>' % (', '.join(ht.keys()[:-1]), ht.keys()[-1])

    if len(args) == 0:
        return simpleResp(sht)
    else:
        if args[0] in ht:
            return simpleResp(ht[args[0]])
        else:
            return simpleResp("Sorry, I don't know about %s" % args[0])


def processMessage(slack, _msg):
    try:

        # print "PROCESSING"
        # print type(_msg)
        msg = json.loads(_msg)
        # print "LOADED"

        if not 'type' in msg:
            return []

        if msg['type'] != 'message':
            # print "NOTMSG"
            return []
        if msg['channel'] != _fooschan:
            # print "NOTCHAN"
            return []

        print "INCHANNEL"

        if not 'text' in msg:
            print "Ignoring possible edit?"
            return []

        text = msg['text']

        print text

        if not text.startswith('<@U0BCNAB3P>'):
            return []

        ctext = text.partition(' ')[2]

        args = ctext.split(None)
        if not args:
            return simpleResp("You didn't ask me to do anything!")

        cmd = args[0]

        if cmd.lower() == 'result':
            return processSubmit(args[1:])
        elif cmd.lower().startswith('rank'):
            return processRank(slack, args[1:])
        elif cmd.lower().startswith('delete'):
            return processDelete(args[1:])
        elif cmd.lower().startswith('recent'):
            return processRecent(slack, args[1:])
        elif cmd.lower().startswith('help'):
            return processHelp(args[1:])
        elif cmd.lower().startswith('predict'):
            return processPredict(args[1:])
        else:
            return simpleResp("I didn't understand the command %s" % (cmd))

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        return simpleResp("<@%s> Error: %s" % (_adminuser, str(e)))



# {"type":"message","channel":"C0BCN8XD4","user":"U02AYNXND","text":"<@U0BCNAB3P>: test message","ts":"1443355146.000005","team":"T027SA6KX"}
