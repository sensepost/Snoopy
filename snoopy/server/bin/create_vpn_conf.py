#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This script will build an openvpn configuration pack for your client.
# Different client packs are built for different clients, at this stage
# we do:
# -Nokia N900 (assuming pwnphone imaged)
# -Generic Linux (assuming driver support via airmon-ng)

import sys
import os
import ipaddr
import subprocess
import stawk_db
import shutil
import random
import hashlib
import traceback, os.path
import imp
import stat
import re

cursor=stawk_db.dbconnect()
# Load config file
snoopyBinPath=os.path.dirname(os.path.realpath(__file__))
os.chdir(snoopyBinPath)
try:
	f = open('../setup/config')
	data = imp.load_source('data', '', f)
	f.close()
	vpn_server=data.vpn_server
	rsync_user=data.rsync_user
	rsync_user_home=data.rsync_user_home
	web_root=data.web_root
except Exception, e:
	print "Unable to load config file!"
	print e
	sys.exit(-1)

supported=['n900','linux']

def list():
	cursor.execute("SELECT id,download_link FROM drone_conf")
	results=cursor.fetchall()
	print "Existing drone configurations:"
	print "------------------------------"
	for r in results:
		print "http://%s/drone_downloads/%s/%s.tar.gz" %(vpn_server,r[1],r[0])

drone_id,device_type="",""

def menu():
	global device_type
	global drone_id
	print """
+---------------------------------------------------------------+
|                    Welcome to Snoopy V0.1                     |
|                      Drone Configuration                    	|
|                                                               |
|              SensePost Information Security                   |
|         research@sensepost.com / wwww.sensepost.com           |
+---------------------------------------------------------------+

[1] List existing client packs
[2] Create new client pack
[x] Return 
"""
#	sys.stdout.write("Option: ")
#	choice=sys.stdin.read(1)
	choice=raw_input("Option: ")
	if choice == "1":
		list()
		sys.exit(0)
	elif choice == "2":
		print "Devices types currently supported: %s" %supported 
		device_type=""
		drone_id=""
		while device_type not in supported:
			device_type = raw_input("Please enter device type: ")
		while drone_id == "":
			drone_id = raw_input("Please enter a name for your drone (e.g. N900-glenn): ")
	elif choice == "x":
		sys.exit(0)


if( len(sys.argv) < 3):
	menu()

else:

	if sys.argv[1] == "--list":
		list()
		sys.exit(0)
	else:
		drone_id=sys.argv[1]
		device_type=sys.argv[2]

if device_type not in supported:
	print "Error, unsupported device! Your options were:"
	print supported
	exit(-1)

# You probably shouldn't change anything from here
vpn_server_tap="192.168.42.1"
first_ip_tap="192.168.42.2"	#Increment on the least octet, giving /24
first_ip_wifi="10.2.0.1"	#Increment on the second octet, giving /16

ip_tap=""
ip_wifi=""

cursor.execute("SELECT * FROM drone_conf WHERE id=%s", (drone_id))
results=cursor.fetchone()
if( results != None):
	print "[!] Error - client already key exists for '%s'" % drone_id
	exit(-1) 

cursor.execute("SELECT ip_wifi,ip_tap FROM drone_conf ORDER BY INET_ATON(ip_wifi) DESC LIMIT 1")
results=cursor.fetchone()
if( results == None):
	print "[+] Configuring first client"
	ip_tap=first_ip_tap
	ip_wifi=first_ip_wifi
else:
	if( int(results[1].split('.')[3]) >= 255):
		print "[!] My programmer only gave me the ability to create 255 drones. Sorry :("
		exit(1)

	ip_wifi=str(ipaddr.IPAddress(results[0])+2**16)
	ip_tap=str(ipaddr.IPAddress(results[1])+1)

print "[+] Creating VPN client certs..."
try:
	# Epic Hack Battles of History. Know a better way..?
	script="""
#!/bin/bash
sed -i "s/export KEY_CN=.*//" /etc/openvpn/easy-rsa/vars
echo "export KEY_CN=%s" >> /etc/openvpn/easy-rsa/vars
sed -i "/^$/d" /etc/openvpn/easy-rsa/vars
cd /etc/openvpn/easy-rsa
source vars &> /dev/null
./pkitool %s &> /dev/null
""" %(drone_id,drone_id)

	f=open('create_keys.sh','w')
	f.write(script)
	f.close()
	r=subprocess.check_call(['bash ./create_keys.sh'],shell=True)
	os.remove('create_keys.sh')
	if( r != 0):
		print "[!] Error attempting to create client certificate and key"
		exit(-1)

except Exception, e:
	print "[!] Error attempting to create client certificate and key"
	print e
	exit(-1)

# Check to ensure files exist, and are not 0 in length
try:
	files=["/etc/openvpn/easy-rsa/keys/%s.crt"%drone_id,"/etc/openvpn/easy-rsa/keys/%s.csr"%drone_id,"/etc/openvpn/easy-rsa/keys/%s.key"%drone_id,"/etc/openvpn/easy-rsa/keys/ca.crt"]
	for f in files:
		size=os.stat(f).st_size
		fail=False
		if size <= 0:
			fail=True
			print "Error! Created VPN file '%s' is zero length!"%f
	
	if fail == True:
		sys.exit(-1)
except Exception,e:
	print "Exception when inspecting VPN files:"
	print e
	sys.exit(-1)	

print "[+] Writing VPN client configuration..."
	
conf_file="""
;dev tun
dev tap
client
proto tcp
remote %s 1194
resolv-retry infinite
nobind
user nobody
group nogroup
persist-key
persist-tun
ca ca.crt
cert %s.crt
key %s.key
comp-lzo
""" %(vpn_server,drone_id,drone_id)

# Required for N900/maemo over 3G 
if device_type == 'n900':
	conf_file += "\nscript-security 2\nipchange ./add_default_route.sh #Hack required for N900 with 3G"
default_route_file="""#!/bin/sh
gprsroute=`route | grep gprs` ; defroute=`route | grep default | grep G` ; if [ -n "$gprsroute" -a -z "$defroute" ]; then nexthop=`ifconfig gprs0 | grep "inet addr" | cut -d : -f 3 | cut -d " " -f 1` ; route add -host $nexthop dev gprs0 ; route add default gw $nexthop ; fi"""	

#Write CCD directive for the new drone IP
f=open('/etc/openvpn/ccd/%s'%drone_id, 'w')
f.write("ifconfig-push %s 255.255.255.0" % ip_tap)

print "[+] Writing Snoopy client configuration files..."

ds=str(ipaddr.IPAddress(ip_wifi)+1)
de='.'.join(ip_wifi.split('.')[0:2])+'.255.255'
snoopy_config="""
# Modify these if you like, but rather via snoopy.sh
iface=wlan999
delay_between_gps_checks=30
promisc=true
ssid=Internet

# You probably shouldn't change anything from here
arch=%s
device_id=%s

#Vars for rsync
delay_between_syncs=30
sync_server=%s
sync_user=%s
upload_path=%s/snoopy/server/uploads

#Vars for rogueAP
at0_ip=%s
vpn_tap_ip=%s
dhcpd_start=%s
dhcpd_end=%s
dhcpd_mask=255.255.0.0
"""%(device_type,drone_id,vpn_server,rsync_user,rsync_user_home,ip_wifi,vpn_server_tap,ds,de)

save_path="../client_configs/%s/snoopy/"%drone_id
print "[+] Creating SSH keys..."
try:
	shutil.copytree("../../client/",save_path)
	os.makedirs("%s/configs/openvpn"%save_path)
	shutil.copy("/etc/openvpn/easy-rsa/keys/%s.crt"%drone_id, "%s/configs/openvpn"%save_path)
	os.makedirs("%s/snoopy_data/%s"%(save_path,drone_id))
	os.makedirs("%s/configs/ssh"%save_path)
	shutil.copy("/etc/openvpn/easy-rsa/keys/%s.csr"%drone_id, "%s/configs/openvpn"%save_path)
	shutil.copy("/etc/openvpn/easy-rsa/keys/%s.key"%drone_id, "%s/configs/openvpn"%save_path)
	shutil.copy("/etc/openvpn/easy-rsa/keys/ca.crt", "%s/configs/openvpn"%save_path)
	
	tmp=open('/tmp/log','w')
	r=subprocess.check_call(["ssh-keygen -f %s/configs/ssh/id_rsa -N ''"%save_path],shell=True,stdout=tmp)
	key=linestring = open("%s/configs/ssh/id_rsa.pub"%save_path, 'r').read()
	f=open("/home/%s/.ssh/authorized_keys" %rsync_user,"a")

	#Somewhat thin security:
	condom='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty,command="/usr/bin/rsync ${SSH_ORIGINAL_COMMAND#* }" '
	f.write(condom + key)

	f=open("%s/configs/openvpn/openvpn.conf"%save_path, "w")
	f.write(conf_file)
	f.close()
	f=open("%s/configs/openvpn/add_default_route.sh"%save_path,"w")
	f.write(default_route_file)
	f.close()
	os.chmod("%s/configs/openvpn/add_default_route.sh"%save_path,stat.S_IXOTH) # Sets file +x, or VPN will not execute it
	
	f=open("%s/configs/config"%save_path,"w")
	f.write(snoopy_config)	
	f.close()

	print "[+] Building Snoopy client pack.."
	rand_dir=hashlib.md5(str(random.random())).hexdigest()
	os.makedirs("%s/drone_downloads/%s"%(web_root,rand_dir))
	r=subprocess.check_call(["cd ../client_configs/%s && tar czf %s/drone_downloads/%s/%s.tar.gz *" %(drone_id,web_root,rand_dir,drone_id)], shell=True)	
	print "[+] Done! Client pack can be downloaded via\n    http://%s/drone_downloads/%s/%s.tar.gz" %(vpn_server,rand_dir,drone_id)

except Exception, e:
	print e
	#print "[!] Failed to write keys and configs %d: %s" % (e.args[0], e.args[1])
	exit(-1)

tmp=re.search('(\d+\.\d+)\.\d+\.\d+',ip_wifi)
ip_prefix=tmp.group(1)
cursor.execute("INSERT INTO drone_conf (id,ip_tap,ip_wifi,ip_prefix,download_link) VALUES (%s,%s,%s,%s,%s)", (drone_id,ip_tap,ip_wifi,ip_prefix,rand_dir))
