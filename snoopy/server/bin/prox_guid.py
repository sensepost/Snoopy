#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This script creates proximity sessions based on intervals between observed probe requests.

import stawk_db
import string
from random import choice
import time
import logging

# Time without seeing a probe from a device
# to mark the prox session as finished.
proximity_buffer = 600 	# 10 minutes
sleep_for=10		# Rereun every n seconds

def getGuid():
	return ''.join([choice(string.letters + string.digits) for i in range(18)])

def do_prox():
	cursor=stawk_db.dbconnect()
	cursor.execute("SELECT device_mac FROM probes WHERE 1 GROUP BY device_mac HAVING SUM(CASE WHEN proximity_session IS NULL AND timestamp IS NOT NULL THEN 1 ELSE 0 END)>0")
	macs=cursor.fetchall()
	if( len(macs) > 0):
		logging.info("%d devices probing. Grouping into proximity sessions..." %len(macs))
	for row in macs:
		curr_mac=row[0]
		first_row=None
		cursor.execute("SELECT DISTINCT unix_timestamp(timestamp),proximity_session FROM probes where device_mac=%s AND timestamp IS NOT NULL ORDER BY unix_timestamp(timestamp)",curr_mac)
		results=cursor.fetchall()

	
		#Unusual case when only one result
		if(len(results) == 1):
			cursor.execute("UPDATE probes SET proximity_session=%s WHERE device_mac=%s",(getGuid(),curr_mac))
		else:
			# Find first null prox session, and start from the entry before it.
			start_from=0
			while( start_from< len(results)-1 and results[start_from][1] != None):	
				start_from+=1

			if( start_from>0):
				start_from-=1
				prev_prox = results[start_from][1]
			else:
				prev_prox = getGuid()
			start_from+=1
		

			prev_ts=results[start_from-1][0]
			for r in range(start_from,len(results)):
				special_flag=True
				timestamp=results[r][0]

				if( (results[r-1][0]+proximity_buffer) < timestamp):
					cursor.execute("UPDATE probes SET proximity_session=%s WHERE device_mac=%s AND unix_timestamp(timestamp)>=%s AND unix_timestamp(timestamp) <%s", (prev_prox,curr_mac,prev_ts,timestamp))
					prev_prox=getGuid()
					prev_ts=timestamp
					special_flag=False
				else:
					pass	
			if( results[r][1] == None or special_flag):
				cursor.execute("UPDATE probes SET proximity_session=%s WHERE device_mac=%s AND unix_timestamp(timestamp)>=%s AND unix_timestamp(timestamp) <=%s", (prev_prox,curr_mac,prev_ts,timestamp))



def main():
	logging.info("Starting proximity calculator...")

	while True:
		try:
			do_prox()
		except Exception, e:
			print e
		time.sleep(sleep_for)



if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
	main()


