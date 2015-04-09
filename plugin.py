###
# Copyright (c) 2015, Robert Stemen
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import time
import requests
from requests.exceptions import HTTPError
import xml.etree.ElementTree as ET


class RedSox(callbacks.Plugin):
	_REDSOX = "BOS"
	_MLB = "http://gd2.mlb.com"
	_MLBCOMP = "/components/game/mlb"
	_MLBDATE = "/year_%s/month_%s/day_%s"
	_SUMMARY = "/epg.xml"
	_BOXSCORE = "/boxscore.xml"

	def _getLineScoreXML(self, gameID):
		url = self._MLB + gameID + self._BOXSCORE
		try:
			response = urllib2.urlopen(url).read()
		except HTTPError:
			print 'ERROR'
			return
		else:
			xml = ET.fromstring(response)

		return xml

	def _getGameID(self):
		year = time.strftime("%Y")
		month = time.strftime("%m")
		day = time.strftime("%d")

		dateURL = self._MLBDATE % (year, month, day)
		url = self._MLB + self._MLBCOMP + dateURL + self._SUMMARY
		response = urllib2.urlopen(url).read()

		xml = ET.fromstring(response)
		for game in xml.findall("game"):
			home = game.findall("[@home_name_abbrev='%s'" % self._REDSOX)
			away = game.findall("[@away_name_abbrev='%s'" % self._REDSOX)
			gameID = game.get("game_data_directory")
			if (home == self._REDSOX) or (away == self._REDSOX):
				return gameID

		return ""

	def _getBlockSize(self, item, xml):
		awayField = "away_%s" % item
		awayBlock = xml.get(awayField) or " "
		homeField = "home_%s" % item
		homeBlock = xml.get(homeField) or " "
		return max(len(awayBlock), len(homeBlock))

	def _getInningBlockSize(self, xml):
		awayBlock = xml.get("away") or " "
		homeBlock = xml.get("home") or " "
		return max(len(awayBlock), len(homeBlock))

	def _getLineScore(self, team, xml):
		nameField = "%s_fname" % team
		name = xml.get(nameField)
		blockSize = self._getBlockSize("fname", xml)

		line = "%s "
		if len(name) != blockSize:
			for i in range(blockSize - len(name) - 1):
				line += " "
		line += "|"

		line %= name

		linescore = xml.find("linescore")
		inningList = linescore.findall("inning_line_score")
		# for inning in range(1, len(inningList)):
		for inning in range(max(10, len(inningList))):
			if inning < len(inningList):
				inningscore = inningList[inning]
				score = inningscore.get(team) or " "
				blockSize = self._getInningBlockSize(inningscore)
			else:
				score = " "
				blockSize = 1

			scoreBlock = " %s "
			if len(score) != blockSize:
				for i in range(blockSize - len(score)):
					scoreBlock += " "
			scoreBlock += "|"

			scoreBlock %= score
			line += scoreBlock

		scoreField = "%s_team_runs" % team
		score = linescore.get(scoreField)
		blockSize = self._getBlockSize("team_runs", linescore)

		scoreBlock = " %s "
		if len(score) != blockSize:
			for i in range(blockSize - len(score)):
				scoreBlock += " "
		scoreBlock += "|"
		
		scoreBlock %= score

		line += scoreBlock

		return line
	
	def score(self, irc, msg, args):
		"""takes no arguments

		Returns the line score of the Red Sox game taking place today.
		"""
		gameID = self._getGameID()
		if gameID != "":
			xml = self._getLineScoreXML(gameID)
			away = self._getLineScore("away", xml)
			home = self._getLineScore("home", xml)
			irc.reply(away)
			irc.reply(home)
	score = wrap(score)

Class = RedSox


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
