# Foosbot

Foosbot is a Slack bot for recording foosball results and ranking players into a league. Players play pick-up games of first to 10, in any combination of 1v1 or 2v2 format and the bot will maintain a ranking order for the individual players.

# Installation

Foosbot requires the following python packages, e.g. pip install them in your virtualenv:

    slacker
    websocket-client
    PyYAML
    numpy
    theano

Then you need to create a config file called config.yaml in the location where you intend to run foosbot containing something like:

    ---
    slacktoken: <API token generated from https://api.slack.com/web>
    fooschan: <channel name where you want bot to run>
    adminuser: <your slack username>
    botuser: <a bot username set up in slack integrations>

Then just run ./foosbot.py

# Usage

To use foosbot, just talk to it in the slack channel you specified in your config file, e.g:

    @foosbot: help

Results are recorded by saying something like:

    @foosbot: result @steve vs @john 10-6

And then you can request rankings:

    @foosbot: rank

which once you've played enough games will return something like:

    1. steve (3.4)
    2. john (-3.4)

# Ranking Model

Technically the ranking algorithm assumes that a foosball game is a series of Bernoulli trials, with a probability determined by the difference in skill between two players. Given a set of matches, it tries to find a set of skill ratings for all players involved which maximises the likelihood of the observed results. To make the minimisation fast this is done with Stochastic Gradient Descent implemented with Theano.

To increase the quality of the rankings, players are required to have played at least 3 games before they are ranked. Old players are removed after a grace period of 30 days, or 7 days if they have less than 10 games recorded.