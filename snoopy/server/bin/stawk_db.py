# -*- coding: utf-8 -*-
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

import MySQLdb
import logging
import time

dbhost="localhost"
dbuser="snoopy"
dbpass="RANDOMPASSWORDGOESHERE"
dbdb="snoopy"
retries=20

def dbconnect():
	for i in range(retries):
		try:
			# unicdoe is a whore
			db = MySQLdb.connect(dbhost, dbuser,dbpass,dbdb, use_unicode=True, charset='utf8')
			db.autocommit(True)
		except Exception,e:
			logging.error("Unable to connect to MySQL! I'll try %d more times"%(retries-i))
			logging.error(e)
			time.sleep(5)
		else:
	        	return db.cursor()

