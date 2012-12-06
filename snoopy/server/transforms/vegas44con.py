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

logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

sys.stderr = sys.stdout

def main():

    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()

#	logging.debug(m.AdditionalFields['end_time'])


	#cursor.execute("SELECT DISTINCT device_mac,vendor_short FROM probes,mac_vendor WHERE SUBSTRING(device_mac,1,6) = mac AND timestamp > %s AND timestamp < %s LIMIT 100", (start_time,end_time))
	cursor.execute("SELECT DISTINCT(t1.device_mac),t1.location,t1.monitor_id FROM probes t1 INNER JOIN probes t2 ON t1.device_mac = t2.device_mac WHERE t1.location LIKE 'vegas%' AND t2.location = '44con'")
	results=cursor.fetchall()
	logging.debug("Observed %d clients" %len(results))

	try:

		for row in results:
	       	 	mac=row[0]
        		NewEnt=TRX.addEntity("snoopy.Client", mac);
			NewEnt.addAdditionalFields("mac","mac address", "strict",row[0])
	#		NewEnt.addAdditionalFields("start_time", "start_time", "strict",start_time)
	#		NewEnt.addAdditionalFields("end_time","end_time", "strict",end_time)
        
        except Exception, e:
                logging.debug("Exception from fetchClients.py:")
                logging.debug(e)


	TRX.returnOutput()
    
main()
                
