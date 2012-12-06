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
    	#logging.debug(MaltegoXML_in)
        m = MaltegoMsg(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()

	drone='%'
	now=datetime.datetime.now()
        if 'start_time' in m.AdditionalFields and 'end_time' in m.AdditionalFields :
                start_time=m.AdditionalFields['start_time']
                end_time=m.AdditionalFields['end_time']
        else:  
                start_time=now+datetime.timedelta(seconds=-lookback)
                end_time=now+datetime.timedelta(seconds=lookback)

                # Maltego requires format e.g 2012-10-23 22:37:12.0
                now=now.strftime("%Y-%m-%d %H:%M:%S.0")
                start_time=start_time.strftime("%Y-%m-%d %H:%M:%S.0")
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S.0")


        if 'location' in m.AdditionalFields:               
		location=m.AdditionalFields['location']
	else:  
                location="%"	

	if 'properties.drone' in m.AdditionalFields:
		drone=m.AdditionalFields['properties.drone']


	cursor.execute("SELECT domain, COUNT(*) FROM (SELECT domain, client_ip FROM squid_logs GROUP BY domain, client_ip) AS x GROUP BY domain")
	results=cursor.fetchall()

	for row in results:
		num=-1
		domain="fuck unicode"
		try:
			domain=row[0].encode('utf8','xmlcharrefreplace')
			num=row[1]
		except Exception,e:
			logging.debug(e)

        	NewEnt=TRX.addEntity("Domain", domain);
		NewEnt.addAdditionalFields("num","Number","strict",num)
		NewEnt.addAdditionalFields("domain","domain","strict",domain)
		NewEnt.setWeight(num)

		#NewEnt.addAdditionalFields("drone","drone","strict",drone)
                #NewEnt.addAdditionalFields("start_time", "start_time", "nostrict",start)
                #NewEnt.addAdditionalFields("end_time","end_time", "nostrict",end)
                #NewEnt.addAdditionalFields("location","location","strict",location)
		#NewEnt.addAdditionalFields("run_id","run_id","strict",run_id)


        TRX.returnOutput()
try:    
	main()
except Exception, e:
	logging.debug(e)
                
