import json
import traceback
import sys
import core
import datetime
import loldb


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

        s1 = int(a4)

        a5 = args.pop(0)
        if a5 == '-':
            a5 = args.pop(0)

        s2 = int(a5)

        if max(s1, s2) < 10:
            return simpleResp("Someone should have scored at least 10 points!")

        m = core.Match(p1, p2, s1, s2, datetime.datetime.now())

        mid = loldb.addmatch(m)

        return simpleResp("Match %s successfully submitted" % (mid))

    except Exception as e:
        print str(e)
        return simpleResp("I'm sorry I didn't understand that")


def formatRanking(slack, d):
    r = []
    l = 1e6
    c = 0

    allusers = slack.users.list().body

    if not 'ok' in allusers:
        raise Exception("Couldn't get users...")

    members = allusers['members']

    for n in sorted(d.items(), key=lambda x: x[1], reverse=True):
        if n[1] < l - 0.1:
            c += 1
            l = n[1]
        name = n[0]
        dn = [x for x in members if x['id'] == n[0]]
        if len(dn) == 1:
            name = dn[0]['name']
        r.append("%i. %s" % (c, name))

    return r


def processRank(slack, args):
    d = loldb.getrankings()
    out = formatRanking(slack, d)
    return map(simpleMsg, out)


def processDelete(args):
    loldb.deletematch(args[0])
    return simpleResp("Match deleted!")


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
        text = msg['text']

        print text

        if not text.startswith('<@U0BCNAB3P>: '):
            return []

        ctext = text.partition(': ')[2]

        args = ctext.split(' ')
        cmd = args[0]

        if cmd.lower() == 'result':
            return processSubmit(args[1:])
        elif cmd.lower().startswith('rank'):
            return processRank(slack, args[1:])
        elif cmd.lower().startswith('delete'):
            return processDelete(args[1:])
        else:
            return simpleResp("I didn't understand the command %s" % (cmd))

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        return simpleResp("<@%s> Error: %s" % (_adminuser, str(e)))



# {"type":"message","channel":"C0BCN8XD4","user":"U02AYNXND","text":"<@U0BCNAB3P>: test message","ts":"1443355146.000005","team":"T027SA6KX"}
