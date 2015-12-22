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
import datetime


config = yaml.load(open('config.yaml'))
slack = slacker.Slacker(config['slacktoken'])


def mangleconfig(config):
    # Sort out friendly names in config
    chans = slack.channels.list().body['channels']
    cc = filter(lambda x: x['name'] == config['fooschan'], chans)
    if len(cc) != 1:
        print "Unable to find channel %s in slack, please check your config" % (config['fooschan'])
        sys.exit(1)
    else:
        print "Channel %s found with id %s" % (config['fooschan'], cc[0]['id'])
        config['fooschan'] = cc[0]['id']

    users = slack.users.list().body['members']
    uc = filter(lambda x: x['name'] == config['adminuser'], users)
    if len(uc) != 1:
        print "Unable to find user %s in slack, please check your config" % (config['adminuser'])
        sys.exit(1)
    else:
        print "Admin user %s found with id %s" % (config['adminuser'], uc[0]['id'])
        config['adminuser'] = uc[0]['id']


def onrecv(ws, message):
    # print message
    sendback = slackparser.processMessage(slack, config, message)
    # print sendback
    for s in sendback:
        s['channel'] = config['fooschan']
        # print ss
        try:
            # print "SENDING", json.dumps(s)
            ws.send(json.dumps(s) + '\n')
            time.sleep(1)
        except Exception as e:
            print "ERROR SENDING"
            print str(e)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)


def onerr(ws, err):
    print "ERROR: ", err


def onclose(ws):
    print "Socket closed"


def run_bot():
    rtminfo = slack.rtm.start()
    wsurl = rtminfo.body['url']

    print "Attempting to connect to %s" % (wsurl)

    ws = websocket.WebSocketApp(wsurl, on_message=onrecv,
                                on_error=onerr, on_close=onclose)

    ws.run_forever()


mangleconfig(config)

failcount = 0
lastfail = datetime.datetime.now()
while True:
    print "Connecting"
    run_bot()
    print "Connection lost..."
    now = datetime.datetime.now()
    timeran = now - lastfail
    lastfail = now
    if timeran.total_seconds() < 3600:
        failcount += 1
    else:
        failcount = 0

    if failcount > 10:
        print "Too many failures, exiting"
        break
    else:
        print "Will reconnect in 60 seconds"
        time.sleep(60)
