#!/usr/bin/python
# -*- coding: utf8 -*-
#
# Téléchargement des factures FDN
#
# usage : fdn-dl-fact.py login_connection mot_de_passe repertoire_destination
#

import sys
from HTMLParser import HTMLParser
import re
import os
import requests

url_site="http://clients.wibox.fr/"
arg_login=sys.argv[1]
arg_passwd=sys.argv[2]
destination=sys.argv[3]

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


def login(url,arg_login,arg_passwd):
	data = {
		"login": arg_login,
		"pwd": arg_passwd
	}
	r = requests.post(url+"login.php", data=data)
	text = r.text
	return r.cookies


def factures(url,cookies):
	r = requests.get(url+"contrat_facture.php",cookies=cookies)
	the_page = r.text
	parser = ParserLiensPdfFactures()
	parser.feed(the_page)
	return parser.pdfs

def sauvegarde(url,cookies,pdf,destination):
	dest = os.path.join(destination,pdf['n_fact']+".pdf")

	if os.path.exists(dest):
		return True
	print pdf
	r = requests.get(url+"traitement/contrat_facture.php", params=pdf, cookies=cookies)
	
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

cookies = login(url_site,arg_login,arg_passwd)
pdfs = factures(url_site,cookies)
for pdf in pdfs:
	sauvegarde(url_site,cookies,pdf,destination)
