#!/usr/bin/python
# This class spawns multiple threads for querying Wigle. Each thread gets its own wigle creds
# and proxy, whcih are read from wigler_conf.cnf. If more threads than Wigle accounts are available
# multiple threads will share the same account. So you could, for example, have 10 threads using
# one Wigle account.
#
# e.g of use:

# from wigle_api import wigle_api
# myW = wigle_api(10)
# myW.push_ssid('foobar')
# result = myW.pop_result()

# glenn@sensepost.com

from threading import Thread
import time
from random import randint
import re
import sys
from collections import deque
import requests
from BeautifulSoup import BeautifulSoup
import pprint
import math
import socket

conf_file="wigler_conf.cnf"
pause_time=10 #10 seconds between Wigle queries

class wigle_api():

	ssid_queue=deque()
	result_queue=deque()
	Flag=True
	pp = pprint.PrettyPrinter(indent=4)

	def __init__(self,num_threads):

	        # Read configuration file
		wigle_accounts=[]
        	print "[+] Reading config file"
        	config_file = open(conf_file,"r")
        	for line in config_file:
                	if( line[0] != '#'):
                        	line=line.strip()
                        	opts=line.split(",")
                        	if( len(opts) != 3):
                               		print "[E] Invalid line in configuration file."
                                	print opts
                                	exit(-1)
                        	else:  
                                	wigle_accounts.append(opts)     

	
		print "[+] Starting %d threads for Wigle queries" % num_threads

		# This try block doesn't stop threads on ctrl+c. Help?
		try:
			for i in range(num_threads):
				Thread(target=self.wigle_thread, args=[self,i,wigle_accounts[i%len(wigle_accounts)]]).start()
		except KeyboardInterrupt:
			print "[!] Caught ctr-c, exiting"
			exit(1)
		print "[+] All threads started"


	def push_ssid(self,ssid):
		self.ssid_queue.append(ssid)

	def pop_result(self):
		try:
			return self.result_queue.popleft()
		except IndexError:
			return None			

	def query_ssid(self,ssid):
		ssid_queue.append(ssid)

	def wigle_thread(self,Thread,i,account):
		url={'land':"https://wigle.net/", 'login': "https://wigle.net/gps/gps/main/login", 'query':"http://wigle.net/gps/gps/main/confirmquery/"}

		#1. Create HTTP objects with proxy
		user,password,proxy=account
		proxies = {"http":proxy,"https":proxy}	
		#2. Log in to Wigle
		print "[%d] Logging into wigle with %s:%s via proxy '%s'" %(i,user,password,proxy)
		payload={'credential_0':user, 'credential_1':password}
		try:
			r = requests.post(url['login'],data=payload,proxies=proxies,timeout=10)
		except Exception, e: #(requests.exceptions.ConnectionError,requests.exceptions.Timeout), e:
			print "[%d] Unable to connect via proxy %s. Thread returning." %(i,proxy)
			print e
			return
		if( 'Please login' in r.text or 'auth' not in r.cookies):
			print "[%d] Error logging in with credentials %s:%s. Thread returning." %(i,user,password)
			exit(-1)
		else:
			print "[%d] Successfully logged in with credentials %s:%s via %s." %(i,user,password,proxy)
		cookies=dict(auth=r.cookies['auth'])
		#3. Poll SSID queue
		while self.Flag:
			try:
				ssid=self.ssid_queue.popleft()
				print "[%d] Looking up %s (%s %s)" %(i,ssid,user,proxy)
				payload={'longrange1': '', 'longrange2': '', 'latrange1': '', 'latrange2':'', 'statecode': '', 'Query': '', 'addresscode': '', 'ssid': ssid, 'lastupdt': '', 'netid': '', 'zipcode':'','variance': ''}
				r = requests.post(url['query'],data=payload,proxies=proxies,cookies=cookies,timeout=10)
				if( r.status_code == 200):
                               		if('too many queries' in r.text):
                                        	print "[%d] User %s has been shunned, pushing %s back on queue... Sleeping for 10 minutes..." %(i,user,ssid)
						self.ssid_queue.append(ssid)
                                        	time.sleep(600)
                                	elif('An Error has occurred:' in r.text):
                                        	print "[%d] An error occured whilst looking up '%s' with Wigle account '%s' (via %s)!" % (i,ssid,user,proxy)
						
                                	elif('Showing stations' in r.text):
						locations=self.fetch_locations(r.text,ssid)
						self.result_queue.append(locations)
						#self.pp.pprint(locations)
					else:
						print "[%d] Unknown error occured whilst looking up '%s' with Wigle account '%s' (via %s)!" % (i,ssid,user,proxy)
						exit(-1)
				else:
					print "[%d] Bad status" %i
				
				time.sleep(pause_time) #No DoS 

			except IndexError:
				time.sleep(0.5)
			except (requests.exceptions.ConnectionError, requests.exceptions.Timeout), e:
				print "[%d] Exception. Unable to retrieve SSID '%s' with creds %s:%s via '%s'. Returning SSID to queue" %(i,ssid,user,password,proxy)
				print e
				time.sleep(10)
				self.ssid_queue.append(ssid)
		

	def fetch_locations(self,text,ssid):
        	soup=BeautifulSoup(text)
                results=soup.findAll("tr", {"class" : "search"})
                locations=[]
                overflow=0
                if (len(results)>99 ):
               		overflow=1
                for line in results:
                	row=line.findAll('td')
                        if( row[2].string.lower() == ssid.lower()):
                                	locations.append({'ssid':row[2].string,'mac':row[1].string, 'last_seen':row[9].string, 'last_update':row[15].string, 'lat':row[12].string, 'long':row[13].string,'overflow':overflow})

                # Sort by last_update
                sorted=False
                while not sorted:
                     	sorted=True
                        for i in range(0,len(locations)-1):
                              	if( int(locations[i]['last_update']) < int(locations[i+1]['last_update'])):
                                       	sorted=False
                                        locations[i],locations[i+1] = locations[i+1],locations[i]

                # Remove duplicates within proximity of each other, keeping the most recent
                # TODO: Update this to find the great circle average
                remove_distance=5000 #5 kilometres
                tD={}
                for i in range(0,len(locations)-1):
                	for j in range(i+1,len(locations)):
                        	dist=self.haversine(float(locations[i]['lat']),float(locations[i]['long']),float(locations[j]['lat']),float(locations[j]['long']))
                                if (dist < remove_distance):
                                     	#print " %d and %d are %d metres apart, thus, DELETION! :P" % (i,j,dist)
                      	                tD[j]=1
                tmp=[]
                for i in range(0,len(locations)):
                        if (i not in tD):
                      		tmp.append(locations[i])

                locations=tmp
		if( len(locations) == 0):
			locations.append({'ssid':ssid,'mac':'', 'last_seen':'', 'last_update':'', 'lat':'', 'long':'','overflow':-1}) #No results, just return the ssid
                return locations        # Return list of locations


        def haversine(self,lat1, lon1, lat2, lon2):
                        R = 6372.8 # In kilometers
                        dLat = math.radians(lat2 - lat1)
                        dLon = math.radians(lon2 - lon1)
                        lat1 = math.radians(lat1)
                        lat2 = math.radians(lat2)

                        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon / 2) * math.sin(dLon / 2) * math.cos(lat1) * math.cos(lat2)
                        c = 2 * math.asin(math.sqrt(a))
                        return R * c * 1000.0 # In metres

	def stop(self):
		print "[+] Telling threads to stop"
		self.Flag=False	


def main():

	myW = wigle_api(1)
	myW.stop()

if __name__ == "__main__":
        main()
	
