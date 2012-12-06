#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# Determines if Drones are connected via OpenVPN

import re
import time

f=open("/etc/openvpn/openvpn-status.log", "r")
line=f.readline()
while ( not re.search('^Common.*',line)):
	line=f.readline()

line=f.readline()
while ( not re.search('^ROUTING.*',line)):
	line=line.strip()
	r=line.split(',')
	client,ip,time=r[0],r[1],r[4]
	ip=ip.split(':')[0]
#	print "'%s' connected since' %s' (from '%s')" %(client,time,ip)
	print "%s\t%s\t%s" %(time,ip,client)

	line=f.readline()
	
