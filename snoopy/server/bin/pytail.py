#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This script searches for certain files, and watches them for changes.
# The changes are inserted into the database.

from pytail_helper import LogWatcher
import stawk_db
import re
import urllib2
from publicsuffix import PublicSuffixList
import csv
import time
import sys
import urllib
import pprint
import logging

from warnings import filterwarnings
import MySQLdb as Database
filterwarnings('ignore', category = Database.Warning)

verbose=1
psl = PublicSuffixList()
#cursor=stawk_db.dbconnect()
files=['squid_logs.txt','probe_data.txt', 'coords.txt', 'dhcpd.leases', 'sslstrip_snoopy.log']


def callback(filename, lines):
	if( files[0] in filename):
		if verbose>0:logging.info("New squid logs!")
		squid(lines)
	elif( files[1] in filename):
		if verbose>0:logging.info("New probe data!")
		probe_data(lines)
	elif( files[2] in filename):
		if verbose>0:logging.info("New coord data!")
		coords(lines)
	elif( files[3] in filename):
		if verbose>0:logging.info("New dhcp leases!")
		dhcp(lines)
	elif( files[4] in filename):
		if verbose>0:logging.info("New sslstrip data!")
		sslstrip(lines)
	sys.stdout.flush()

# Thanks Junaid for this method
# If we can figure out how to make squid log POST data (say the first 200 chars) we
# can dispose of this approach.
def sslstrip(lines):
	isEntry = False
	anEntry = {}
	for aLine in lines:
	        if aLine.startswith('2012-') and aLine.find(' Client:') > -1:
	                if isEntry:
	                        processEntry(anEntry)
	                        isEntry = False

	                if aLine.find(' POST Data (') > -1:
	                        isEntry = True
	                        anEntry = {}
	                        anEntry['timestamp'] = aLine[:aLine.find(',')]
	                        anEntry['secure'] = 0
	                        anEntry['post'] = ''
	                        if aLine.find('SECURE POST Data (') > -1:
	                                anEntry['secure'] = 1

	                        tStart = aLine.find(' POST Data (') + 12
	                        anEntry['host'] = aLine[tStart:aLine.find(')', tStart)]
				anEntry['domain']=domain=psl.get_public_suffix(anEntry['host'])

	                        tStart = aLine.find(' Client:') + 8
	                        anEntry['src_ip'] = aLine[tStart:aLine.find(' ', tStart)]

			 	tStart = aLine.find(' URL(') + 8
	                        anEntry['url'] = aLine[tStart:aLine.find(')URL', tStart)]

	        elif isEntry:
	                anEntry['post'] = '%s%s' % (anEntry['post'], urllib.unquote_plus(aLine.strip()))
	if isEntry:
		processEntry(anEntry)

def processEntry(anEntry):
	cursor.execute("INSERT IGNORE INTO sslstrip (timestamp,secure,post,host,domain,src_ip,url) VALUES(%s,%s,%s,%s,%s,%s,%s)",(anEntry['timestamp'],anEntry['secure'],anEntry['post'],anEntry['host'],anEntry['domain'],anEntry['src_ip'],anEntry['url']))


def coords(lines):
	for line in lines:
		line=line.rstrip()
		# e.g N900-glenn,1344619634_27185,1344622644.848847,52.781064,-1.237870,58.640000
		c=line.split(",")
		c[2]=re.sub('\..*','',c[2])
		cursor.execute("INSERT IGNORE INTO gps_movement (monitor_id,run_id,timestamp,gps_lat,gps_long,accuracy) VALUES (%s,%s,FROM_UNIXTIME(%s),%s,%s,%s)",(c[0],c[1],c[2],c[3],c[4],c[5]))
		

def probe_data(lines):
	for line in lines:
		line=line.rstrip()
		# e.g "N900-glenn","1344619634_27185","lough001","00:c0:1b:0b:54:89","tubes","-87","Aug 10, 2012 18:29:58.779969000"
		c=csv.reader([line],delimiter=",")
 		r=next(iter(c), None)
		r[6]=re.sub('\..*','',r[6])
		r[3]=re.sub(':','',r[3]) #Remove colons from mac
		try:
			r[6]=time.mktime(time.strptime(r[6],"%b %d, %Y %H:%M:%S"))	#Until we can update N900's tshark to use frame.time_epoch
		except Exception,e:
			pass
		cursor.execute("INSERT INTO probes (monitor_id,run_id,location,device_mac,probe_ssid,signal_db,timestamp,priority,mac_prefix) VALUES (%s,%s,%s,%s,%s,CONVERT(%s,SIGNED INTEGER),FROM_UNIXTIME(%s),2,%s) ON DUPLICATE KEY UPDATE monitor_id=monitor_id", (r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[3][:6]))

def squid(lines):
	for line in lines:
		line=line.rstrip()
		data=line.split(" ")
		data=map(urllib2.unquote, data)					
		epoch,ip,http_code,method,host,url,ua,cookies=data
		domain=psl.get_public_suffix(host)

		cursor.execute("INSERT INTO squid_logs (timestamp,client_ip,http_code,method,domain,host,url,ua,cookies) VALUES (FROM_UNIXTIME(%s),%s,%s,%s,%s,%s,%s,%s,%s)", (epoch,ip,http_code,method,domain,host,url,ua,cookies) )	


def dhcp(lines):
	for line in lines:
		line=line.rstrip()
		try:
			f=re.search('(.*)\s.*',line)
			line=f.group(1)
			f=re.search('(\S*)\s(\S*)\s(\S*)\s(.*)',line)
			expire,mac,ip,hostname=f.group(1),f.group(2),f.group(3),f.group(4)
			mac=re.sub(':','',mac)
			tmp=re.search('(\d+\.\d+)\.\d+\.\d+',ip)
			ip_prefix=tmp.group(1)
			cursor.execute("INSERT IGNORE INTO dhcp_leases (mac,ip,hostname,expire,mac_prefix,ip_prefix) VALUES (%s,%s,%s,FROM_UNIXTIME(%s),%s,%s)", (mac,ip,hostname,expire,mac[:6],ip_prefix))
			#cursor.execute("INSERT IGNORE INTO dhcp_leases (mac,ip,hostname,expire) VALUES (%s,%s,%s,FROM_UNIXTIME(%s))", (mac,ip,hostname,expire))
		except Exception,e:
			logging.error("Error attempting to parse DHCP file!")
			logging.debug(line)
			logging.debug(e)


def main(searchdir):
	global cursor
	while True:
		cursor=stawk_db.dbconnect()
		try:
			logging.info("Staring database population engine")
			l = LogWatcher(searchdir,files, callback)
			l.loop()
		except Exception, e:
			logging.error("Exception!")
			logging.error(e)
		time.sleep(5)

if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
	logging.info("START")

        if( len(sys.argv) < 2):
                logging.error("[E] Please supply me a directory name to watch. e.g:\n python pytail.py ../uploads/")
                exit(-1)

        searchdir=sys.argv[1]
        logging.info("Watching '%s' for files: %s" %(searchdir, ', '.join(files)))

	main(searchdir)


