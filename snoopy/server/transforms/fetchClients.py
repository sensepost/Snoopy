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
	logging.debug(m)    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()

#	logging.debug(m.AdditionalFields['end_time'])

	logging.info("Fetching victims")


	drone='%'
	if 'properties.drone' in m.AdditionalFields:
                drone=m.AdditionalFields['properties.drone']
	
	if 'drone' in m.AdditionalFields:
		drone=m.AdditionalFields['drone']
	
#	drone=m.AdditionalFields['drone']

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

	logging.debug("1. S,E - %s / %s"%(start_time,end_time))

	if 'location' in m.AdditionalFields:
                location=m.AdditionalFields['location']
		# I'm a dirty hacker, short and stout.
		logging.debug("SELECT MIN(timestamp),MAX(timestamp) FROM probes WHERE location LIKE %s AND monitor_id=%s AND timestamp >= %s AND timestamp <= %s"%(location,drone,start_time,end_time))
		cursor.execute("SELECT MIN(timestamp),MAX(timestamp) FROM probes WHERE location LIKE %s AND monitor_id=%s AND timestamp >= %s AND timestamp <= %s",(location,drone,start_time,end_time))
		result=cursor.fetchone()
		start_time=result[0]
		end_time=result[1]
        else:
                location="%"


	logging.debug("2. S,E - %s / %s"%(start_time,end_time))
	logging.debug(drone)


	try:

		logging.info("SELECT DISTINCT device_mac,vendor_short,monitor_id AS drone_id,'probes' AS source, IFNULL(hostname,'') AS hostname,location FROM proximity_sessions LEFT OUTER JOIN dhcp_leases ON proximity_sessions.device_mac = dhcp_leases.mac WHERE monitor_id='%s' AND location LIKE '%s' AND last_probe > '%s' AND last_probe < '%s' UNION SELECT DISTINCT dhcp_leases.mac,mac_vendor.vendor_short,drone_conf.id AS drone_id, 'web' AS source, dhcp_leases.hostname, '' AS location from dhcp_leases inner join mac_vendor on mac_prefix=mac_vendor.mac inner join squid_logs on client_ip=dhcp_leases.ip inner join drone_conf on drone_conf.ip_prefix=dhcp_leases.ip_prefix WHERE drone_conf.id='%s' AND timestamp > '%s' AND timestamp < '%s'"%(drone,location,start_time,end_time,drone,start_time,end_time))
		cursor.execute("SELECT DISTINCT device_mac,vendor_short,monitor_id AS drone_id,'probes' AS source, IFNULL(hostname,'') AS hostname,location FROM proximity_sessions LEFT OUTER JOIN dhcp_leases ON proximity_sessions.device_mac = dhcp_leases.mac WHERE monitor_id=%s AND location LIKE %s AND last_probe >= %s AND last_probe <= %s UNION SELECT DISTINCT dhcp_leases.mac,mac_vendor.vendor_short,drone_conf.id AS drone_id, 'web' AS source, dhcp_leases.hostname, '' AS location from dhcp_leases inner join mac_vendor on mac_prefix=mac_vendor.mac inner join squid_logs on client_ip=dhcp_leases.ip inner join drone_conf on drone_conf.ip_prefix=dhcp_leases.ip_prefix WHERE drone_conf.id=%s AND timestamp >= %s AND timestamp <= %s",(drone,location,start_time,end_time,drone,start_time,end_time))
		results=cursor.fetchall()
		logging.debug( "Observed %d clients" %len(results))

		dataz={}
		for row in results:
			logging.debug(row)
		        mac=row[0]
		        vendor=row[1]
			drone=row[2]
		        source=row[3]
		        hostname=row[4]
			obs_location=row[5]
		        tmp={'vendor':vendor,'hostname':hostname}
		        if source=='web':
		                tmp['from_web']="True"
		        elif source == 'probes':
		                tmp['from_probes']="True"
		
		        if mac not in dataz:
		                dataz[mac]=tmp
				dataz[mac]['obs_location']=obs_location
		        else:  
		                dataz[mac] = dict(dataz[mac].items() + tmp.items())
				dataz[mac]['obs_location'] = dataz[mac]['obs_location'] + ", " + obs_location



		for k,v in dataz.iteritems():
	       	 	mac=k
			vendor=v['vendor']
			hostname=v['hostname']
			obs_location=v['obs_location']
			from_web,from_probes="False","False"
			if 'from_web' in v:
				from_web="True"
			if 'from_probes' in v:
				from_probes="True"
        	
	#		if from_web == "False":
			if len(hostname) < 1:
				NewEnt=TRX.addEntity("snoopy.Client", "%s"%(vendor));
			else:
				NewEnt=TRX.addEntity("snoopy.Client", "%s (%s)"%(vendor,hostname))
			NewEnt.addAdditionalFields("mac","mac address", "strict",mac)
			NewEnt.addAdditionalFields("vendor","vendor","strict",vendor)
			NewEnt.addAdditionalFields("hostname","hostname","hostname",hostname)

			NewEnt.addAdditionalFields("from_web","from_web","nostrict",from_web)
			NewEnt.addAdditionalFields("from_probes","from_probes","nostrict",from_probes)

			NewEnt.addAdditionalFields("drone","drone","nostrict",drone)
		
			NewEnt.addAdditionalFields("start_time", "start_time", "nostrict",start_time)
			NewEnt.addAdditionalFields("end_time","end_time", "nostrict",end_time)
     			NewEnt.addAdditionalFields("location","Location","nostrict",location)
     			NewEnt.addAdditionalFields("obs_location","Observed Locations","nostrict",obs_location)
			
	
			#Add something to icon to distinguish probes and web?
 
        except Exception, e:
                logging.debug("Exception from fetchClients.py:")
                logging.debug(e)


	TRX.returnOutput()

try:   
	main()
except Exception,e:
	logging.debug(e)
