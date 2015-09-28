#!/usr/bin/env python

import slacker
# import json
import websocket
import slackparser
import json
import traceback
import time
import sys
import yaml

config = yaml.load(open('config.yaml'))

slack = slacker.Slacker(config['slacktoken'])

rtminfo = slack.rtm.start()
wsurl = rtminfo.body['url']


def onrecv(ws, message):
    print message
    sendback = slackparser.processMessage(slack, message)
    print sendback
    for s in sendback:
        print s
        try:
            print "SENDING", json.dumps(s)
            ws.send(json.dumps(s) + '\n')
            time.sleep(1)
        except Exception as e:
            print "ERROR SENDING"
            print str(e)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)


def onerr(ws, err):
    print err


def onclose(ws):
    print "Socket closed"

print "Attempting to connect to %s" % (wsurl)

ws = websocket.WebSocketApp(wsurl, on_message=onrecv,
                            on_error=onerr, on_close=onclose)

ws.run_forever()


# Examples
# {"type":"hello"}
# {"type":"presence_change","user":"U0BCNAB3P","presence":"active"}
# {"type":"user_typing","channel":"C0BCN8XD4","user":"U02AYNXND"}
# {"type":"message","channel":"C0BCN8XD4","user":"U02AYNXND","text":"a message","ts":"1443355097.000004","team":"T027SA6KX"}
# {"type":"user_typing","channel":"C0BCN8XD4","user":"U02AYNXND"}
# {"type":"message","channel":"C0BCN8XD4","user":"U02AYNXND","text":"<@U0BCNAB3P>: test message","ts":"1443355146.000005","team":"T027SA6KX"}
# {"type":"presence_change","user":"U0293DYK9","presence":"active"}
# {"type":"presence_change","user":"U043N038C","presence":"away"}