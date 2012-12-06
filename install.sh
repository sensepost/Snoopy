#!/bin/bash
# glenn@sensepost.com
# Snoopy // 2012

# Snoopy server side setup script. Installs required packages, and reconfigures. This has only been
# tested on Ubuntu 32bit 12.04 LTS Server. Read through it carefully if you're not installing on a 
# fresh box that you don't mind breaking.

clear
echo -en "
+-----------------------------------------------------------------------------------------------+
|          		     Welcome to the Snoopy V0.1 installer.     				|
|                                                           					|
|             			 SensePost Information Security                   		|
|        		 research@sensepost.com / www.sensepost.com/labs         		|
+-----------------------------------------------------------------------------------------------+
| Snoopy is a distributed tracking and profiling framework built by glenn@sensepost.com. 	|
|												| 	
| This script is intended to be run on a stock Ubuntu 12.04 32 bit server. It will attempt to	|
| perform the following tasks:									|
| 1. Create a user account, and copy Snoopy's files to the user's folder	 		|
|    (drones will sync collected data here)							|
| 2. Generate SSH keys for the user								|
| 3. Ask you to select your server's public IP address						|
| 4. Install Ubuntu packges: python-pip, gcc, libxml2-dev, libxslt-dev, python2.7-dev, xplico,	|
|    mysql-server, squid3, apache2, openvpn, bind9, iptables-persistent, tshark, python-mysqldb	|
| 5. Install Python packages: PIL, mitmproxy, ipaddr, publicsuffix, twisted			|
| 6. Setup OpenVPN, BIND, Apache, and Squid (with custom configurations).			|
| 7. Setup iptables rules									|
| 												|
| \E[5mWARNING:\E[25m											|
| This script will overwrite existing Apache, Squid, BIND, OpenVPN and iptables configurations.	|
|												|
| By proceeding you accept that:								|
|	- You have read and agree to the supplied LICENSE.txt 					|
|	- SensePost takes no responsibility for any illegal activities perpetrated with		|
|	  this tool.
|												|
| Press any key to continue...									|
+-----------------------------------------------------------------------------------------------+"

read foo
xplico=no #Set to yes to install xplico. ToDo Incorporate xplico database into Snoopy.

echo -n "[+] Let's create a Snoopy account. Please enter a name (enter for default 'woodstock'): "
read user
user="${user:=woodstock}"

useradd -c "Snoopy Account" -m $user
if [ "$?" -ne 0 ]; then
        echo "[!] Failed to create user $user :("
        exit 1
fi
home_dir=$(getent passwd $user | cut -d: -f6)
echo "[+] Copying files to '$home_dir/snoopy'"
cp -R snoopy $home_dir/
cp LICENSE.txt README.txt $home_dir/snoopy/
#tar xzf snoopy_install_files.tar.gz -C $home_dir
chown -R $user: $home_dir/snoopy
if [ "$?" -ne 0 ]; then
        echo "[!] Failed to extract files :("
        exit 1
fi

cd $home_dir/snoopy/server/
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
su - $user -c "mkdir -p $home_dir/snoopy/server/uploads"
su - $user -c "mkdir -p $home_dir/snoopy/server/client_configs"
echo "[+] Creating ssh keys for $user.."
su - $user -c "ssh-keygen -f $home_dir/.ssh/id_rsa -N ''" 
su - $user -c "touch $home_dir/.ssh/authorized_keys"
sed -i "s/^rsync_user=.*/rsync_user=\"$user\"/" ./setup/config

sed -i "s,^rsync_user_home=.*,rsync_user_home=\"$home_dir\"," ./setup/config

echo "[+] On with configuration; let's set your public IP address"
IPs=$(ifconfig | grep "inet addr"| sed 's/.*addr:\(\S*\)\s*.*/\1/'| grep -v "127.0.0.1")
if [ -z "$IPs" ]; then
        echo "[!] No available IP addresses!"
	exit -1
else   
        echo "    Enter one of the following IP addresses:"
        echo -e '    \E[31;1m'$IPs'\E[0m'
        echo -n "    IP: "
        read -e server_ip

        if [[ "$IPs" != *$server_ip* ]]
        then   
                echo "[!] You gave me a non-existent IP address! I even gave you the options to choose from :(";
		exit -1
        else
                sed -i "s/^vpn_server=.*/vpn_server=\"$server_ip\"/" ./setup/config
        fi
fi

# Add xplico repo
if [ "$xplico" == "yes" ]; then
	echo "deb http://repo.xplico.org/ $(lsb_release -s -c) main" >> /etc/apt/sources.list
	apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 791C25CE &
	if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
fi

echo "[+] Updating repositories..."
sleep 3
apt-get update 
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi

echo "[+] Installing required packages..."
sleep 3

apt-get install -y python-pip gcc libxml2-dev libxslt-dev python2.7-dev mysql-server squid3 openvpn bind9 tshark python-mysqldb apache2 python-beaker python-flask python-jinja2 python-mysqldb python-sqlalchemy python-werkzeug
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
if [ "$xplico" == "yes" ]; then
	apt-get install -y xplico 
fi
pip install lxml beautifulsoup requests PIL mitmproxy ipaddr publicsuffix twisted cryptacular Flask_SQLAlchemy
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi

echo "[+] Done installing packages. Onward and upward!"
echo "[+] Building OpenVPN certificates..."
sleep 1

#################
#OpenVPN	#
#################
rm -rf /etc/openvpn/easy-rsa/ /etc/openvpn/ccd/
mkdir -p /etc/openvpn/easy-rsa/
mkdir -p /etc/openvpn/ccd/
#mkdir /etc/openvpn/packs/
cp -R /usr/share/doc/openvpn/examples/easy-rsa/2.0/* /etc/openvpn/easy-rsa/ 
cd /etc/openvpn/easy-rsa/
ln -s openssl-1.0.0.cnf openssl.cnf
source ./vars 
./clean-all 
echo "    Creating server CA"
./pkitool --initca 
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
echo "    Generating keys "
./pkitool --server server 
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
echo "    Generating DH parameters (this may take some time)"
./build-dh 
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
cd $home_dir/snoopy/server/

echo "[+] Creating Snoopy Server OpenVPN configuration file"

#tap0 is required to bind dhcp3-server to the server interface, a
# work in progress to allow a central DHCP server.

cat > /etc/openvpn/openvpn.conf << EOL
local $server_ip
;dev tun
dev tap0

topology subnet
proto tcp
port 1194
ca /etc/openvpn/easy-rsa/keys/ca.crt
cert /etc/openvpn/easy-rsa/keys/server.crt
key /etc/openvpn/easy-rsa/keys/server.key
dh /etc/openvpn/easy-rsa/keys/dh1024.pem
client-config-dir ccd
user nobody
group nogroup
server 192.168.42.0 255.255.255.0
persist-key
persist-tun
status openvpn-status.log 5
verb 3
client-to-client
push "redirect-gateway def1"
log-append /var/log/openvpn
comp-lzo
script-security 3
up "/usr/bin/snoopy_routes.sh"

EOL

echo "[+] Adding routes for 'Server<---Drone--->Victim' communication"
#Routes for VPN, figure out how to do this properly
echo '#!/bin/bash
for i in {2..100}; do ip route add 10.$i.0.0/16 via 192.168.42.$i; done' > /usr/bin/snoopy_routes.sh
chmod +x /usr/bin/snoopy_routes.sh
/etc/init.d/openvpn start
# For each client, the create_vpn_config.py script will
# do './pkitool clientname'


echo "[+] Configurating squid proxy with custom logging..."
#########################
# Update squid3.conf	#
#########################
#TODO: Figure out how to send logs directly to MySQL. I almost had it working, but fell back to 
#	parsing a text file (with pytail.py)
rm /etc/logrotate.d/squid3 &	#Disable log rotation
ln -s /var/log/squid3/access.log $home_dir/snoopy/server/uploads/squid_logs.txt
cp /etc/squid3/squid.conf /etc/squid3/squid.conf.bak
cat > /etc/squid3/squid.conf.new << EOL
http_port 192.168.42.1:3128 transparent
acl vpn src 10.0.0.0/8
http_access allow vpn
# Use mitmproxy.py as parent proxy
cache_peer 192.168.42.1 parent 3129 0 no-query no-digest
never_direct allow all

logformat squid %ts %>a %Hs %rm %{Host}>h %rp %{User-Agent}>h %{Cookie}>h
access_log /var/log/squid3/access.log squid

EOL

sed 's/^\(http_port.*\)/#\1/' -i /etc/squid3/squid.conf
cat /etc/squid3/squid.conf >> /etc/squid3/squid.conf.new
mv /etc/squid3/squid.conf.new /etc/squid3/squid.conf

echo "[+] Restarting squid"
/etc/init.d/squid3 restart 


echo "[+] Configuring BIND to control victims' DNS"
#########################
# Configure bind	#
#########################
mv /etc/bind/named.conf.options /etc/bind/named.conf.options.bak
cat > /etc/bind/named.conf.options << EOL
options {
	directory "/var/cache/bind";
        allow-query { 10.0.0.0/8; 192.168.42.0/24;};
        listen-on {192.168.42.1;};
        forwarders {8.8.8.8;};
        auth-nxdomain no;    # conform to RFC1035
};
EOL
echo "[+] Restarting BIND..."
/etc/init.d/bind9 restart 

echo "[+] Configuring Apache webserver..."
##################
# Apache2	#
#################
#mkdir -p /var/www/drone_downloads/ #create_vpn_conf stores it's output here for users to download

#CGI bin for python, for transforms

cp /etc/apache2/sites-available/default /etc/apache2/sites-available/default.bak
cat > /etc/apache2/sites-available/default <<EOL
<VirtualHost *:80>
        ServerAdmin webmaster@localhost

        DocumentRoot /var/www
        <Directory />
                Options FollowSymLinks
                AllowOverride None
        </Directory>
        <Directory /var/www/>
                Options -Indexes FollowSymLinks MultiViews
                AllowOverride None
                Order allow,deny
                allow from all
        </Directory>

        ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
        <Directory "/usr/lib/cgi-bin">
                AllowOverride None
                Options +ExecCGI -MultiViews +FollowSymLinks
                Order allow,deny
                Allow from all
                AddHandler cgi-script .py
                AddHandler default-handler .html .htm
        </Directory>

        ErrorLog ${APACHE_LOG_DIR}/error.log

        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel warn

        CustomLog ${APACHE_LOG_DIR}/access.log combined

    Alias /doc/ "/usr/share/doc/"
    <Directory "/usr/share/doc/">
        Options Indexes MultiViews FollowSymLinks
        AllowOverride None
        Order deny,allow
        Deny from all
        Allow from 127.0.0.0/255.0.0.0 ::1/128
    </Directory>

</VirtualHost>
EOL

cgi_dir=$(head -1 /dev/urandom | tr -dc _A-Z-a-z-0-9 | head -c${1:-132}|md5sum | sed 's/ .*//')
mkdir -p /usr/lib/cgi-bin/$cgi_dir
ln -s $home_dir/snoopy/server/transforms/ /usr/lib/cgi-bin/$cgi_dir/

web_dir=$(head -1 /dev/urandom | tr -dc _A-Z-a-z-0-9 | head -c${1:-132}|md5sum | sed 's/ .*//')
echo "http://$server_ip/$web_dir/" > $home_dir/snoopy/server/setup/webroot_guid.txt
mkdir -p /var/www/$web_dir
ln -s $home_dir/snoopy/server/web_data/ /var/www/$web_dir/

cat > $home_dir/snoopy/server/setup/transforms.txt << EOL
Snoopy Maltego Entities:
http://$server_ip/$web_dir/web_data/maltego/snoopy_entities.mtz
Snoopy Maltego Machines:
http://$server_ip/$web_dir/web_data/maltego/snoopy_machines.tar.gz
Snoopy Maltego Transforms:
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchDrones.py (input entity Custom snoopy.Snoopy)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchSSIDs.py (input entity Custom snoopy.Client)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchClients.py (input entity Custom snoopy.Drone)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchClients.py (input entity Custom snoopy.DroneLocation)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchSSIDLocations.py (input entity Custom snoopy.SSID)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchDomains.py (input entity Custom snoopy.Client)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchFacebook.py (input entity Maltego.FacebookObject)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchFacebookFriends.py (input entity maltego.FacebookObject)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchAllFacebook.py (input entity Custom snoopy.Snoopy)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchLocations.py (input entity Custom snoopy.Drone)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchCountries.py (input entity Custom snoopy.Snoopy)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchClientsFromCountry.py (input entity Location)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchAllDomains.py (input entity Custom snoopy.Snoopy)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchClientsFromDomain.py (input entity Maltego.Domain)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchUserAgents.py (input entity Custom snoopy.Snoopy)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchClientsFromUA.py (input entity Custom snoopy.useragent)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchTweetsByLocation.py (input entity Location)
http://$server_ip/cgi-bin/$cgi_dir/transforms/fetchUAsFromClient.py (input entity Custom snoopy.Client)
EOL

/etc/init.d/apache2 restart 

if [ "$xplico" == "yes" ]; then
	echo "[+] Configuring xplico"
	/opt/xplico/script/session_mng.pyc -n "Snoopy" "Data Intercepted" 
fi

echo "[+] Setting iptables to transparently route web traffic to squid, and masquerade other."
#################
# iptables	#
#################
# Transparent proxying. TODO: Squid SSL MITM. mitmproxy currently doesn't support transparant proxying. WPAD. EvilGrade.
mkdir -p /etc/iptables/
iptables -t nat -A PREROUTING -s 10.0.0.0/8 -i tap0 -p tcp --dport 80 -j DNAT --to 192.168.42.1:3128
iptables -t nat -A PREROUTING -s 10.0.0.0/8 -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3128
iptables -t nat -A PREROUTING -s 10.0.0.0/8 -i tap0 -p tcp --dport 8080 -j DNAT --to 192.168.42.1:3128
iptables -t nat -A PREROUTING -s 10.0.0.0/8 -i eth0 -p tcp --dport 8080 -j REDIRECT --to-port 3128
# Masquerade all other ports
iptables -t nat -A POSTROUTING -s 10.0.0.0/8 -p tcp -o eth0 -j MASQUERADE
# Give APs internet access
iptables -t nat -A POSTROUTING -s 192.168.42.0/24 -o eth0 -j MASQUERADE
iptables-save > /etc/iptables/rules.v4
echo "[+] Saving iptables to start on reboot"

echo "[+] Disabling IPv6"
echo "[+] Enabling IP forwarding"
#########################################
# Disable IPv6	and enable IPforwarding	#
#########################################
cat >> /etc/sysctl.conf << EOL
net.ipv4.ip_forward = 1
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOL
sysctl -p 

echo "[+] Creating Snoopy database user and populating database."
#########################			
# Create database	#
#########################
stty -echo
echo -n "    Enter your MySQL root password: "
read mysqlpass
stty echo
echo ""
toughpassword=$(head -1 /dev/urandom | tr -dc _A-Z-a-z-0-9 | head -c${1:-132}|md5sum | sed 's/ .*//')

sed -i "s/RANDOMPASSWORDGOESHERE/$toughpassword/" $home_dir/snoopy/server/setup/db_setup.sql
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
sed -i "s/RANDOMPASSWORDGOESHERE/$toughpassword/" $home_dir/snoopy/server/bin/stawk_db.py
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
sed -i "s/RANDOMPASSWORDGOESHERE/$toughpassword/" $home_dir/snoopy/server/transforms/stawk_db.py
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
sed -i "s/RANDOMPASSWORDGOESHERE/$toughpassword/" $home_dir/snoopy/server/bin/snoopy/src/snoopy/db/__init__.py
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi

mysql -u root -p$mysqlpass < $home_dir/snoopy/server/setup/db_setup.sql
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
mysql -u root -p$mysqlpass snoopy < $home_dir/snoopy/server/setup/mac_vendor.sql
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi

lesstoughpassword=$(head -100 /dev/urandom | tr -dc _A-Z-a-z-0-9 | head -c${1:-10})
echo "[+] Setting web interface (http://$server_ip:5000/) password to '$lesstoughpassword' - maybe write that down."
sed -i "s/YABADABADOO/$lesstoughpassword/" $home_dir/snoopy/server/bin/snoopy/src/snoopy/db/__init__.py
if [ "$?" -ne 0 ]; then echo "[!] Failed :("; exit 1; fi
echo "admin:$lesstoughpassword" > $home_dir/snoopy/server/web_ui_creds.txt

cat > /usr/bin/snoopy << EOL
#!/bin/bash
cd $home_dir/snoopy/server/
bash snoopy.sh
EOL
chmod +x /usr/bin/snoopy

echo "-------------------------------------------------------------------------------------------------------------------------------"

echo "    Snoopy installation done! You should run the command 'snoopy' now to load the server
    menu. From there you can create some configuration packs to load on your Drones. Have fun,"
echo "    be good, and learn!"
echo ""
echo "    Contact glenn@sensepost.com for questions/suggestions to do with Snoopy."
echo ""
echo "    http://www.sensepost.com/labs"
echo "    research@sensepost.com"


