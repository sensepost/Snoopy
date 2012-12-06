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

	domain='None'
	if 'domain' in m.AdditionalFields:
		domain=m.AdditionalFields['domain']


	cursor.execute("SELECT DISTINCT client_ip,hostname,dhcp_leases.mac,vendor_short,ua FROM dhcp_leases,squid_logs,mac_vendor WHERE squid_logs.client_ip=dhcp_leases.ip AND dhcp_leases.mac_prefix=mac_vendor.mac AND domain = %s",(domain))
	results=cursor.fetchall()

	for row in results:

		try:
			client_ip=row[0]
			hostname=row[1].encode('utf8','xmlcharrefreplace')
			mac=row[2]
			vendor=row[3].encode('utf8','xmlcharrefreplace')
			useragent=row[4].encode('utf8','xmlcharrefreplace')
		except Exception,e:
			logging.debug(e)

        	NewEnt=TRX.addEntity("snoopy.Client", "%s (%s)"%(vendor,hostname))
		NewEnt.addAdditionalFields("hostname","hostname","strict",hostname)
		NewEnt.addAdditionalFields("mac","mac","strict",mac)
		NewEnt.addAdditionalFields("vendor","vendor","strict",vendor)
#		NewEnt.addAdditionalFields("useragent","useragent","strict",useragent)	#Some devices have multiple UAs
		NewEnt.addAdditionalFields("from_web","from_web","strict","True")
                NewEnt.addAdditionalFields("from_probes","from_probes","strict","True")

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
                
