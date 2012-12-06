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
from time import strftime
import re
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

	# If no start / end times are specified, we default to lookback 
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


	logging.debug("-----------------")

	logging.debug("1. Currenttime -%s, Start time - %s, End time - %s" %(now,start_time,end_time))
	try:
	
		logging.debug("select DISTINCT drone_conf.id from dhcp_leases inner join mac_vendor on mac_prefix=mac_vendor.mac inner join squid_logs on client_ip=dhcp_leases.ip inner join drone_conf on drone_conf.ip_prefix=dhcp_leases.ip_prefix WHERE squid_logs.timestamp > %s AND squid_logs.timestamp < %s UNION SELECT DISTINCT monitor_id FROM probes WHERE timestamp > %s AND timestamp < %s AND location LIKE %s" % (start_time,end_time,start_time,end_time,location))
		cursor.execute("select DISTINCT drone_conf.id from dhcp_leases inner join mac_vendor on mac_prefix=mac_vendor.mac inner join squid_logs on client_ip=dhcp_leases.ip inner join drone_conf on drone_conf.ip_prefix=dhcp_leases.ip_prefix WHERE squid_logs.timestamp > %s AND squid_logs.timestamp < %s UNION SELECT DISTINCT monitor_id FROM probes WHERE timestamp > %s AND timestamp < %s AND location LIKE %s", (start_time,end_time,start_time,end_time,location))

#		cursor.execute("select DISTINCT drone_conf.id from dhcp_leases inner join mac_vendor on mac_prefix=mac_vendor.mac inner join squid_logs on client_ip=dhcp_leases.ip inner join drone_conf on drone_conf.ip_prefix=dhcp_leases.ip_prefix WHERE squid_logs.timestamp > %s AND squid_logs.timestamp < %s UNION SELECT DISTINCT monitor_id FROM proximity_sessions WHERE last_probe > %s AND last_probe < %s AND location LIKE %s", (start_time,end_time,start_time,end_time,location))
		results=cursor.fetchall()

		logging.debug("Observed drone count: %d" %len(results))
			
		for row in results:
			logging.debug("2. Currenttime -%s, Start time - %s, End time - %s" %(now,start_time,end_time))
	        	drone=row[0]
	        	NewEnt=TRX.addEntity("snoopy.Drone", row[0]);
			NewEnt.addAdditionalFields("drone","drone", "strict", row[0])
			NewEnt.addAdditionalFields("start_time","Start time", "nostrict", start_time)
			NewEnt.addAdditionalFields("end_time","End time", "nostrict", end_time)
#			NewEnt.addAdditionalFields("location","location", "strict", location)

			NewEnt.addAdditionalFields("start_time_txt","Start time_txt", "nostrict", start_time)
                        NewEnt.addAdditionalFields("end_time_txt","End time_txt", "nostrict", end_time)


			NewEnt.addAdditionalFields("current_time","current_time","nostrict",now)


	except Exception, e:
		logging.debug("Exception:")
		logging.debug(e)


        TRX.returnOutput()
    
main()
                
