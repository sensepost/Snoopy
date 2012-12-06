#!/bin/bash
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This script will parse pcap files, ready to be inserted into our db.

mkdir $device_id
echo -n "" > ./$device_id/probe_data.txt

for filename in `find ./new_pcaps/ -name probeRequests_*.cap`
do
  device_id=$(cat ./new_pcaps/device_id.txt)
  location=$(echo $filename | sed 's/.*probeRequests_\(.*\)_.*/\1/')
  date=$(echo $filename| sed 's/.*_\(.*\)\.cap/\1/')
  run_id=$(perl -e "use Time::Piece; print Time::Piece->strptime('$date','%F-%k%M%S')->epoch;")
  run_id=$run_id"_"$RANDOM

  if [ -z "$run_id" ]  || [ -z "$date" ] || [ -z "$location" ] || [ -z "$device_id" ]
   then
  	echo "Error - could not determine all variables. Do you have a device_id.txt file containing your\n device's unique ID, and is the filename of the format probeRequests_<location>_<date>.cap"
  	exit
  fi
  
  mkdir  $device_id
 
  tshark -r $filename -R 'wlan.fc.type_subtype eq 4' -T fields -e wlan.sa -e wlan_mgt.ssid -e radiotap.dbm_antsignal -e frame.time -E separator=, -E quote=d | sed -u "s/^/\"$device_id\",\"$run_id\",\"$location\",/" >> ./$device_id/probe_data.txt
  mv $filename ./old_pcaps/
done


num_probes=$(wc -l probe_data.txt)
echo Done. Extracted $num_probes probes...
