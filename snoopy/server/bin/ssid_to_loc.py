#!/usr/bin/python
# coding=utf-8
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# Uses wigle_api to query SSIDs from the MySQL database

from wigle_api_lite import fetchLocations
import time
import stawk_db
import sys
import re
import logging

from warnings import filterwarnings
import MySQLdb as Database
filterwarnings('ignore', category = Database.Warning)

num_threads=2
Flag=True
bad_ssids={}
#if len(sys.argv) < 2:
	#priority=None
#	priority=2
#else:
	# Allows us to set real time priority, e.g for Maltego
#	priority=int(sys.argv[1])

def main():
	logging.info("Starting Wigle GeoLocator")

	cursor = stawk_db.dbconnect()
	while Flag:
		cursor.execute("SELECT DISTINCT probe_ssid FROM probes WHERE probe_ssid != '' AND probe_ssid NOT LIKE '%\\\\\\%' AND probe_ssid NOT IN (SELECT DISTINCT ssid from wigle) ORDER BY PRIORITY")
		result=cursor.fetchall()
		if(len(result) > 0):
			logging.info("Looking up address for %d SSIDs" %len(result))
		for r in result:
			if r[0] in bad_ssids and bad_ssids[r[0]] > 4:
				logging.info("Ignoring bad SSID '%s' after %d failed lookups"%(r[0],bad_ssids[r[0]]))
				cursor.execute("INSERT INTO wigle (ssid,overflow) VALUES (%s,-2)",(ssid))
			else:
				locations=fetchLocations(r[0])
	
				if locations == None:
					logging.info("Wigle account has been shunned, backing off for 20 minutes")
					time.sleep(60*20)
				elif 'error' in locations:
					logging.info("An error occured, will retry in 60 seconds (%s)" %locations['error'])
					if r[0] not in bad_ssids:
						bad_ssids[r[0]]=0
					bad_ssids[r[0]]+=1
					#print bad_ssids
					time.sleep(60)
	
				else:
					for l in locations:
	        	                	country,code,address="","",""
	                	        	if( 'country' in l['ga'] ):
	                        			country=l['ga']['country']
		                        	if( 'code' in l['ga'] ):
	        	                 		code=l['ga']['code']
	                	         	if( 'address' in l['ga'] ):
	                        	 		address=l['ga']['address']
	
		                                ssid=l['ssid']
	       	                        	g_long=l['long']
	                                	g_lat=l['lat']
	                                	mac=re.sub(':','',l['mac'])
	                                	last_seen=l['last_seen']
	                                	overflow=l['overflow']
					
	
	
	#                                	logging.info("INSERT INTO wigle (ssid,mac,gps_lat,gps_long,last_update,overflow, country,code,address) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(ssid,mac,g_lat,g_long,last_seen,overflow,country,code,address))
	                                	cursor.execute("INSERT INTO wigle (ssid,mac,gps_lat,gps_long,last_update,overflow, country,code,address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(ssid,mac,g_lat,g_long,last_seen,overflow,country,code,address))


#			print locations

		time.sleep(5)

if __name__ == "__main__":
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

	while True:
		try:
        		main()
		except Exception, e:
			logging.error("Beware the ides of March")
			logging.error(e)
			time.sleep(10)

