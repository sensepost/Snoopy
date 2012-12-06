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

#	logging.debug("SELECT DISTINCT location FROM probes WHERE timestamp > '%s' AND timestamp < '%s' AND monitor_id LIKE '%s'" %(start_time,end_time,drone))
#	cursor.execute("SELECT DISTINCT location FROM probes WHERE timestamp > %s AND timestamp < %s AND monitor_id LIKE %s", (start_time,end_time,drone))

	logging.debug("SELECT location,MIN(timestamp),MAX(timestamp),run_id FROM probes WHERE timestamp > '%s' AND timestamp < '%s' AND monitor_id LIKE '%s' GROUP BY location"% (start_time,end_time,drone))	
	cursor.execute("SELECT location,MIN(timestamp),MAX(timestamp),run_id FROM probes WHERE timestamp > %s AND timestamp < %s AND monitor_id LIKE %s GROUP BY location", (start_time,end_time,drone))


	results=cursor.fetchall()

	for row in results:
		location,start,end,run_id=row[0],row[1].strftime("%Y-%m-%d %H:%M:%S.0"),row[2].strftime("%Y-%m-%d %H:%M:%S.0"),row[3]
		logging.debug("SE / ET - %s / %s" %(start,end))
        	NewEnt=TRX.addEntity("snoopy.DroneLocation", location);

		NewEnt.addAdditionalFields("drone","drone","strict",drone)
                NewEnt.addAdditionalFields("start_time", "start_time", "nostrict",start)
                NewEnt.addAdditionalFields("end_time","end_time", "nostrict",end)
                NewEnt.addAdditionalFields("location","location","strict",location)
		NewEnt.addAdditionalFields("run_id","run_id","strict",run_id)


        TRX.returnOutput()
try:    
	main()
except Exception, e:
	logging.debug(e)
                
