#!/bin/bash
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This script will listen for all traffic from victims (10.0.0.0/8 range) and write rotating pcaps to disk
# Rsync will move any files which are no longer being written to to the xplico drop directory, which it will
# routinely parse. Result can then be viewd in the xplico interface.
# The fuser command seems to always output if a file is being written to. Can you not make it output to terminal?

# TODO: Move pcaps to different folders based on differnet IPs, so each monitor device has its own list. It xplico,
# this will involve creating a new 'sesion' for each device.


mkdir -p /tmp/tmpsnoopy
save_path=/tmp/tmpsnoopy/
to_path=/opt/xplico/pol_1/sol_1/new/	#xplico pcap dir for case 1 session 1
iface=tap0
t_pid=31337	#Random initial PID for tshark process

if [ ! -d "$to_path" ]; then
	echo "[E] $to_path doesn't exist. Is xplico setup, with a case created?"
	exit
fi

function move_caps
# Move pcap files that are not currently being written to.
{
 echo -n "" > /tmp/include_list.txt
 for i in `find $save_path -type f`
 do
 	op=`fuser $i`
 	if [ "$op" == "" ]
 	then
 		c=`echo $i | sed 's/.*\///g'`
 		echo $c >> /tmp/include_list.txt
 	fi
 done
 rsync -rzt --remove-source-files --include-from=/tmp/include_list.txt --include="*/" --exclude \* $save_path $to_path
}

function ensure_sniffing
# Check if tshark is running, if not, start
{
 if ! ps p $t_pid | grep -v "TIME CMD" | grep -q $t_pid
  then
	echo [+] Staring tshark..
	tshark -i $iface -b duration:10 -w $save_path/snoop.pcap src net 10.0.0.0/8 or dst net 10.0.0.0/8 &
 	t_pid=$!
	sleep 10
  fi
}

control_c()
# run if user hits control-c
{
  echo -en "\n*** Ouch! Exiting ***\n"
  kill -9 $t_pid
  exit
}
trap control_c SIGINT

#########################
# Main Loop		#
#########################
while true; 
do
 ensure_sniffing
 move_caps
 sleep 10
done

