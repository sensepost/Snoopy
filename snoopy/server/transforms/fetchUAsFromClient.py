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


	try:
		if 'mac' in m.AdditionalFields:
			mac=m.AdditionalFields['mac']

		logging.debug(mac)
	
		cursor.execute("SELECT DISTINCT ua FROM squid_logs,dhcp_leases WHERE squid_logs.client_ip=dhcp_leases.ip AND dhcp_leases.mac=%s", (mac))
		results=cursor.fetchall()


		for row in results:
       		 	ua=row[0].encode('utf8','xmlcharrefreplace')
        		NewEnt=TRX.addEntity("snoopy.useragent", ua);
			
#			NewEnt.addAdditionalFields("start_time","Start time", "strict", start_time)
#			NewEnt.addAdditionalFields("end_time","End time", "strict", end_time)

        except Exception, e:
                logging.debug("Exception:")
                logging.debug(e)


        TRX.returnOutput()
    
main()
                
