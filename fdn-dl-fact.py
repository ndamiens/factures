#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Téléchargement des factures FDN
#
# usage : fdn-dl-fact.py login_connection mot_de_passe repertoire_destination
#

import urllib
import urllib2
import sys
import cookielib
from HTMLParser import HTMLParser
import re
import os

url_site="https://vador.fdn.fr/adherents/"
arg_login=sys.argv[1]
arg_passwd=sys.argv[2]
destination=sys.argv[3]

class ParserLienPrelevements(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.session_id=None

	def handle_starttag(self,tag,attrs):
		if tag == 'a':
			for attr in attrs:
				if attr[0] == 'href':
					m = re.match("^.*sess=([0-9a-z._]*)&?",attr[1])
					if m is not None:
						self.session_id=m.group(1)
						return

class ParserLiensPdfFactures(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.pdfs = []

	def handle_starttag(self,tag,attrs):
		if tag == 'a':
			for attr in attrs:
				if attr[0] == 'href':
					m = re.match("^print-prlligsepa.cgi.*ligid=([0-9]*)&?",attr[1])
					if m is not None:
						self.pdfs.append(m.group(1))
						return


def login(url,arg_login,arg_passwd):
	data = urllib.urlencode({
		"adhlogin": "",
		"adhpasswd": "",
		"radlogin": arg_login,
		"radpsswd": arg_passwd,
		"telephone": "",
		"dplnum": "",
		"do":"yes"
	})
	req = urllib2.Request(url+"index.cgi?"+data)
	response = urllib2.urlopen(req)
	the_page = response.read()
	parser = ParserLienPrelevements()
	parser.feed(the_page)
	return parser.session_id

def prelevements(url,sid):
	data = urllib.urlencode({
		"sess": sid
	})
	req = urllib2.Request(url+"adh-prl.cgi?"+data)
	response = urllib2.urlopen(req)
	the_page = response.read()
	parser = ParserLiensPdfFactures()
	parser.feed(the_page)
	return parser.pdfs

def sauvegarde(url,sid,pdf,destination):
	dest = os.path.join(destination,pdf+".pdf")

	if os.path.exists(dest):
		return True

	data = urllib.urlencode({
		"sess": sid,
		"ligid": pdf
	})
	
	s = open(dest,"w")
	req = urllib2.Request(url+"print-prlligsepa.cgi?"+data)
	response = urllib2.urlopen(req)
	s.write(response.read())
	s.close()

	s = open(dest,"r")
	deb=s.read(10)
	s.close()
	
	if not deb.startswith("%PDF-1."):
		os.unlink(dest)
		return False
	
	return True

sid = login(url_site,arg_login,arg_passwd)
pdfs = prelevements(url_site,sid)
for pdf in pdfs:
	sauvegarde(url_site,sid,pdf,destination)
