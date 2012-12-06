#!/usr/bin/python
# -*- coding: utf-8 -*-
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

import sys
import os
from Maltego import *
import stawk_db
import logging
import datetime
from xml.sax.saxutils import escape

logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

sys.stderr = sys.stdout

def main():

    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()

	#logging.debug(MaltegoXML_in)
	try:
		mac,drone='%','%'
		if 'mac' in m.AdditionalFields:
			mac=m.AdditionalFields['mac']
		if 'drone' in m.AdditionalFields:
			drone=m.AdditionalFields['drone']

		logging.debug(mac)
		logging.debug(drone)
#		cursor.execute("SELECT DISTINCT probe_ssid FROM probes WHERE probe_ssid NOT LIKE '%\\\\\\%' AND  device_mac=%s", (mac))
		cursor.execute("SELECT DISTINCT probe_ssid FROM probes WHERE device_mac=%s", (mac))
		results=cursor.fetchall()


		for row in results:
       		 	ssid=escape(row[0])
			#ssid=(row[0]).encode('ascii','xmlcharrefreplace')
			if ssid != '':
				logging.debug(ssid)
        			NewEnt=TRX.addEntity("snoopy.SSID", ssid);
			
#			NewEnt.addAdditionalFields("start_time","Start time", "strict", start_time)
#			NewEnt.addAdditionalFields("end_time","End time", "strict", end_time)

        except Exception, e:
                logging.debug("Exception:")
                logging.debug(e)


        TRX.returnOutput()

try:    
	main()
except Exception, e:
	logging.debug("Exception:")
	logging.debug(e)                
