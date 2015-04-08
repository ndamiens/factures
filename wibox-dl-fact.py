#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Téléchargement des factures Wibox
#
# usage : wibox-dl-fact.py identifiant mot_de_passe repertoire_destination
#

import sys
from HTMLParser import HTMLParser
import re
import os
import requests
import time

url_site="http://clients.wibox.fr/"
arg_login=sys.argv[1]
arg_passwd=sys.argv[2]
destination=sys.argv[3]

class ParserFormLogin(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.present = False
	def handle_starttag(self,tag,attrs):
		if tag == 'form':
			for attr in attrs:
				if (attr[0] == 'action') and (attr[1] == "http://clients.wibox.fr/login.php"):
					self.present = True
				

class ParserLiensPdfFactures(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.pdfs = []

	def handle_starttag(self,tag,attrs):
		if tag == 'a':
			for attr in attrs:
				if attr[0] == 'href':
					m = re.match("http://.*/traitement/contrat_facture.php\?n_fact=FACP([0-9]+)&n_key=([a-f0-9]+)",attr[1])
					if m is not None:
						self.pdfs.append({
							"n_fact": "FACP"+m.group(1),
							"n_key": m.group(2)
						})

def est_page_login(html):
	parser = ParserFormLogin()
	parser.feed(html)
	return parser.present

def login(url,arg_login,arg_passwd):
	s = requests.Session()
	data = {
		"login": arg_login,
		"pwd": arg_passwd
	}
	r = requests.post(url)
	r = s.get(url);
	text = r.text
	r = s.post(url+"login.php", data=data)
	if est_page_login(r.text):
		return False
	# test en chargeant index.php

	r = s.get(url+"index.php")
	if est_page_login(r.text):
		print "session :("
		return False
	return s


def factures(url,session):
	r = session.get(url+"contrat_facture.php")
	the_page = r.text
	if est_page_login(the_page):
		return False
	parser = ParserLiensPdfFactures()
	parser.feed(the_page)
	return parser.pdfs

def sauvegarde(url,session,pdf,destination):
	dest = os.path.join(destination,pdf['n_fact']+".pdf")

	if os.path.exists(dest):
		return True
	print pdf
	r = session.get(url+"traitement/contrat_facture.php", params=pdf)
	
	s = open(dest,"w")
	s.write(r.content)
	s.close()

	s = open(dest,"r")
	deb=s.read(10)
	s.close()
	
	if not deb.startswith("%PDF-1."):
		print "%s pas un pdf !" % (dest)
		os.unlink(dest)
		return False
	
	return True

session = login(url_site,arg_login,arg_passwd)

if not session:
	print "login failed"
	sys.exit(1)

pdfs = factures(url_site,session)

if not pdfs:
	print "session perdue ?"
	sys.exit(1)

for pdf in pdfs:
	sauvegarde(url_site,session,pdf,destination)
	time.sleep(1)

sys.exit(0)
