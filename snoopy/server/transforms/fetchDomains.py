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
from common import *

logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

sys.stderr = sys.stdout

def main():

    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()


	try:

	#	logging.debug(m.AdditionalFields['end_time'])
	        now=datetime.datetime.now()
	        if 'start_time' in m.AdditionalFields and 'end_time' in m.AdditionalFields :
	                start_time=m.AdditionalFields['start_time']
	                end_time=m.AdditionalFields['end_time']
	        else:   
	                start_time=now-datetime.timedelta(0,lookback)
	                end_time=now+datetime.timedelta(1,0)
		
		logging.debug(start_time)
		logging.debug(end_time)
	
		if 'mac' in m.AdditionalFields:
			mac=m.AdditionalFields['mac']
		else:
			mac="0"
		if 'drone' in m.AdditionalFields:
			drone=m.AdditionalFields['drone']
		else:
			drone="0"

		logging.debug(mac)
		logging.debug(drone)
	
		cursor.execute("SELECT DISTINCT domain FROM snoopy_web_logs WHERE mac=%s", (mac))
		#cursor.execute("SELECT DISTINCT domain FROM snoopy_web_logs WHERE mac=%s AND timestamp > %s AND timestamp <%s", (mac,start_time,end_time))
		results=cursor.fetchall()


		for row in results:
			domain=row[0]
			if ( domain == "facebook.com" ):
				NewEnt=TRX.addEntity("maltego.FacebookObject",domain)
				
			else:
        			NewEnt=TRX.addEntity("Domain", domain)

			NewEnt.addAdditionalFields("start_time", "start_time", "nostrict",start_time)
                        NewEnt.addAdditionalFields("end_time","end_time", "nostrict",end_time)
			NewEnt.addAdditionalFields("mac","mac","strict",mac)
			NewEnt.addAdditionalFields("drone","drone","strict",drone)
#			NewEnt.addAdditionalFields("drone","drone","strict",drone)
#			NewEnt.addAdditionalFields("mac","mac","strict",mac)

        except Exception, e:
                logging.debug("Exception:")
                logging.debug(e)


        TRX.returnOutput()
    
main()
                
