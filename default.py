#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (C) 2015 KodeKarnage
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html


import xbmc
import xbmcaddon
import xbmcgui
import os
import time
import datetime

import smtplib
from email.mime.text import MIMEText

# This is a throwaway variable to deal with a python bug
try:
	throwaway = datetime.datetime.strptime('20110101','%Y%m%d')
except:
	pass

__addon__       = xbmcaddon.Addon()
__setting__     = __addon__.getSetting
__setset__      = __addon__.setSetting
DIALOG          = xbmcgui.Dialog()
LOG_FILE 	 	= os.path.join(xbmc.translatePath('special://temp'), 'kodi.log')
ERROR_FLAGS		= ['ERROR: EXCEPTION Thrown']

# STORED = 'MYFITSRERROPR|||SECONDERROPR'

# def __setting__(key):

# 	return STORED


# def __setset__(key, setting):

# 	STORED = setting 

# LOG_FILE 	= 'C:\\temp\\kodi.log'


class Error_Blotter(object):

	def __init__(self, max_lines = 30):
		self.active_error = []
		self.final_list   = []
		self.max_lines    = max_lines

	def new_error(self, line):
		if self.active_error:
			self.final_list.append(self.active_error)
		self.active_error = [line]

	def add_line(self, line):
		if self.active_error:
			self.active_error.append(line)
			if len(self.active_error) >= self.max_lines:
				self.final_list.append(self.active_error)
				self.active_error = []

	def finalise(self):
		if self.active_error:
			self.final_list.append(self.active_error)


class Main(object):
	''' Log Scanner is a service that periodically scans the kodi.log and emails a compilation of
		all the python script errors to the user.


		20:04:30 102982.718750 T:2637165600   ERROR: EXCEPTION Thrown (PythonToCppException) : -->Python callback/script returned the following error<--
	'''

	def __init__(self):

		self.error_cache = {}

		self.commence_scan_and_reporting()

		print 'Exiting'


	def commence_scan_and_reporting(self):

		print 'Scanning logs'

		found_errors = self.scan_logs()

		print 'Error Cache Size = %s' % len(self.error_cache)

		self.error_cache.update(found_errors)

		print 'Error Cache Size = %s' % len(self.error_cache)

		new_errors = self.compile_errors(self.error_cache)

		print 'New Errors = %s' % len(new_errors)

		if new_errors:

			self.email_results(new_errors)

			new_keys = [x[0] for x in new_errors]

			self.update_reported_errors(new_keys)


	def scan_logs(self):

		blotter = Error_Blotter()

		with open(LOG_FILE, 'r') as f:

			lines = f.readlines()
			for line in lines:

				if any([error in line for error in ERROR_FLAGS]):

					blotter.new_error(line)

				else:

					blotter.add_line(line)

			blotter.finalise()

			errors = blotter.final_list

		return {x[0]: x for x in errors}


	def parse_reported_errors(self):
		''' The stored settings are in order from oldest to newest, only the topline is stored'''

		reported_errors = __setting__('reported')

		res = reported_errors.split('|||')

		return res


	def update_reported_errors(self, update_list):
		''' Only the last 100 errors are kept '''

		current = self.parse_reported_errors()

		current.extend(update_list)

		new = current[::-1][:100]

		new.sort()

		__setset__('reported','|||'.join(new))


	def compile_errors(self, error_cache):

		e_tuples = error_cache.items()

		e_tuples.sort(key= lambda x: x[0])

		reported = self.parse_reported_errors()

		new_errors = [x for x in e_tuples if x[0] not in set(reported)]

		return new_errors


	def email_results(self, errors):

		''' errors is a list of tuples, key, rest of error '''

		print 'Emailing...'

		thyme = time.time()

		recipient = 'subliminal.karnage@gmail.com'

		body = '<table border="1">'
		for _, error in errors:
			body += '<tr><td>%s</td></tr>' % "\n------------------------------------------------------------------------------\n"

			for line in error:
				body += '<tr><td>%s</td></tr>' % line

			body += '<tr><td>%s</td></tr>' % "\n------------------------------------------------------------------------------\n"

		body += '</table>'

		msg = MIMEText(body, 'html')
		msg['Subject'] = 'LogScanner Report %s' % thyme
		msg['From'] = 'LogScanner'
		msg['To'] = recipient
		msg['X-Mailer'] = 'LogScanner Shout Out %s' % thyme

		smtp = smtplib.SMTP('alt4.gmail-smtp-in.l.google.com')
		smtp.sendmail(msg['From'], msg['To'], msg.as_string(9))
		smtp.quit()


if ( __name__ == "__main__" ):

	Main()

