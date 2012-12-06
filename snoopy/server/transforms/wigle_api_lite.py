#!/usr/bin/python

# glenn@sensepost.com

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
import sys
import logging
import os
import urllib2
import httplib2
import urllib
import json

conf_file="wigler_conf.cnf"
pp = pprint.PrettyPrinter(indent=4)

save_dir="./street_views/"

def read_config():

 	# Read configuration file
	wigle_accounts=[]
	config_file = open(conf_file,"r")
	for line in config_file:
        	if( line[0] != '#'):
                	line=line.strip()
                	opts=line.split(",")
                	if( len(opts) != 3):
                       		logging.debug("[E] Invalid line in configuration file.")
                        	print opts
                        	exit(-1)
                	else:  
                        	wigle_accounts.append(opts)     


def wigle(account,ssid):

	url={'land':"https://wigle.net/", 'login': "https://wigle.net/gps/gps/main/login", 'query':"http://wigle.net/gps/gps/main/confirmquery/"}

	#1. Create HTTP objects with proxy
	user,password,proxy=account
	proxies = {"http":proxy,"https":proxy}	
	#2. Log in to Wigle
	logging.debug("[+] Logging into wigle with %s:%s via proxy '%s'" %(user,password,proxy))
	payload={'credential_0':user, 'credential_1':password}
	try:
		r = requests.post(url['login'],data=payload,proxies=proxies,timeout=10)
	except Exception, e: #(requests.exceptions.ConnectionError,requests.exceptions.Timeout), e:
		logging.debug("[E] Unable to connect via proxy %s. Thread returning." %(proxy))
		print e
		return
	if( 'Please login' in r.text or 'auth' not in r.cookies):
		logging.debug("[-] Error logging in with credentials %s:%s. Thread returning." %(user,password))
		exit(-1)
	else:
		logging.debug("[-] Successfully logged in with credentials %s:%s via %s." %(user,password,proxy))
	cookies=dict(auth=r.cookies['auth'])
	#3. Poll SSID queue
	logging.debug("[-] Looking up %s (%s %s)" %(ssid,user,proxy))
	payload={'longrange1': '', 'longrange2': '', 'latrange1': '', 'latrange2':'', 'statecode': '', 'Query': '', 'addresscode': '', 'ssid': ssid, 'lastupdt': '', 'netid': '', 'zipcode':'','variance': ''}
	try:
		r = requests.post(url['query'],data=payload,proxies=proxies,cookies=cookies,timeout=10)
		if( r.status_code == 200):
	        	if('too many queries' in r.text):
	                	logging.debug("[-] User %s has been shunned, pushing %s back on queue... Sleeping for 10 minutes..." %(user,ssid))
	                elif('An Error has occurred:' in r.text):
	             		logging.debug("[-] An error occured whilst looking up '%s' with Wigle account '%s' (via %s)!" % (ssid,user,proxy))
				
	            	elif('Showing stations' in r.text):
				locations=fetch_locations(r.text,ssid)
				#pp.pprint(locations)
				return locations
			else:
				logging.debug("[-] Unknown error occured whilst looking up '%s' with Wigle account '%s' (via %s)!" % (ssid,user,proxy))
				exit(-1)
		else:
			logging.debug("[-] Bad status" %i)
		
	
	except (requests.exceptions.ConnectionError, requests.exceptions.Timeout), e:
		logging.debug("[-] Exception. Unable to retrieve SSID '%s' with creds %s:%s via '%s'. Returning SSID to queue" %(ssid,user,password,proxy))
		print e
	


def fetch_locations(text,ssid):
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
                	dist=haversine(float(locations[i]['lat']),float(locations[i]['long']),float(locations[j]['lat']),float(locations[j]['long']))
                        if (dist < remove_distance):
                             	#logging.debug(" %d and %d are %d metres apart, thus, DELETION! :P" % (j,dist))
              	                tD[j]=1
        tmp=[]
        for i in range(0,len(locations)):
                if (i not in tD):
              		tmp.append(locations[i])

        locations=tmp
	if( len(locations) == 0):
		locations.append({'ssid':ssid,'mac':'', 'last_seen':'', 'last_update':'', 'lat':'', 'long':'','overflow':-1}) #No results, just return the ssid
 
       	return locations        # Return list of locations

def haversine(lat1, lon1, lat2, lon2):
                R = 6372.8 # In kilometers
                dLat = math.radians(lat2 - lat1)
                dLon = math.radians(lon2 - lon1)
                lat1 = math.radians(lat1)
                lat2 = math.radians(lat2)

                a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon / 2) * math.sin(dLon / 2) * math.cos(lat1) * math.cos(lat2)
                c = 2 * math.asin(math.sqrt(a))
                return R * c * 1000.0 # In metres

def getAddress(lat,lng):
        http=httplib2.Http()
        br_headers={'cache-control':'no-cache', 'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)', 'host':'maps.google.com'}
        base='http://maps.google.com/maps/geo?output=json&sensor=true_or_false&q='
        base_img='http://maps.googleapis.com/maps/api/streetview?size=800x800&sensor=false&location='
        cords="%s,%s" %(lat,lng)

        urllib.urlretrieve(base_img+cords,"%s/%s.jpg"%(save_dir,cords))

        failed=0
        while(failed < 5): 
                headers,page = http.request(base+cords, method='GET', headers=br_headers)
                data = json.loads(page)

                if ( headers['status'] == "200" ):
                        if( data['Status']['code'] == 200):
                                address,country,code="","",""
                                try:
                                        address=data['Placemark'][0]['address']
                                        country=data['Placemark'][0]['AddressDetails']['Country']['CountryName']
                                        code=data['Placemark'][0]['AddressDetails']['Country']['CountryNameCode']
                                except:
                                        None

                                return {'http_status':200,'g_status':'200','address':address,'country':country,'code':code}
                        else:
                                return {'http_status':200,'g_status':data['Status']['code']}
                else:
                        print "Failed. Backing off for 5 seconds"
                        print headers['status']
                        time.sleep(5)
                        failed=failed+1

        return {'http_status':headers['status']}


def fetchLocations(ssid):

	if not os.path.exists(save_dir) and not os.path.isdir(save_dir):
		os.makedirs(save_dir)
	
#	account=("sourkiss2","sourkiss2","") #"http://ideaseo:ideaseo1@65.60.13.196:29786")
	account=("alphabravo","wigleisawesome44","")
	locations=wigle(account,ssid)

	if (locations != None):	
		for l in locations:
			l['ga']=getAddress(l['lat'],l['long'])

	logging.debug(locations)
	return locations
	

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
	ssid=sys.argv[1]
        pp.pprint(fetchLocations(ssid))

