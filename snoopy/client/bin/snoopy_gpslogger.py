#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# Script to poll GPS on N900. Quick, dirty, PoC hack. Please rewrite for me.
# Waits for accuracy to be < 100m

import location
import gobject
import sys
import time
import math

if len(sys.argv) < 3:
    sys.stderr.write('Usage:' + sys.argv[0] +' <file_to_write_gps_position_to> <interval_time>\n')
    sys.exit(1)

acc=10000 #100m
prepend_text=sys.argv[3]
sleep_time=int(sys.argv[2])
filename=sys.argv[1]
#print "[+] Will poll GPS until accuracy of %d meters." %(acc/100)


class gps_fix:
	fix=None

	def on_error(self,control, error, data):
	    print "location error: %d... quitting" % error
	    data.quit()
	
	def on_changed(self,device, data):
	    if not device:
	        return
	
	    #Uncomment line below to show progress...
	    cacc= "#Accuracy: %f,%f,%f,%f,%f" %(time.time(),device.fix[4],device.fix[5],device.fix[6]/100,device.fix[11]) 
	    #print cacc
	    #f.write(cacc)
	    #f.write("\n")
	    #f.flush()
	   
	    if not device.fix[6] == device.fix[6]:
	        return
	
	    if device.fix[6] > acc:
	        return
	
	    if device.fix:
	        if device.fix[1] & location.GPS_DEVICE_LATLONG_SET:
		    f=open(filename, "a")
		    #print "[+] GPS coords: (%f,%f) +/- %f" %(device.fix[4],device.fix[5],device.fix[6]/100)
	            pos ="%s,%f,%f,%f,%f" %(prepend_text,time.time(),device.fix[4],device.fix[5],device.fix[6]/100)
		    self.fix=(device.fix[4],device.fix[5])
		    f.write(pos)
		    f.write("\n")
		    f.close()
		    data.stop()
		    #time.sleep(sleep_time)
		    #data.start()
	
	def on_stop(self,control, data):
	    data.quit()
	    #pass
	
	def start_location(self,data):
	    data.start()
	    return False
	
	def __init__(self):
		loop = gobject.MainLoop()
		control = location.GPSDControl.get_default()
		device = location.GPSDevice()
		control.set_properties(preferred_method=location.METHOD_USER_SELECTED,
		                       preferred_interval=location.INTERVAL_DEFAULT)
		
		control.connect("error-verbose", self.on_error, loop)
		device.connect("changed", self.on_changed, control)
		control.connect("gpsd-stopped", self.on_stop, loop)
		
		gobject.idle_add(self.start_location, control)
		
		loop.run()


def haversine(lat1, lon1, lat2, lon2):
	R = 6372.8 # In kilometers
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon / 2) * math.sin(dLon / 2) * math.cos(lat1) * math.cos(lat2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c * 1000.0 # In metres

lastPos=(0,0)
while(1):
	g = gps_fix()

	#print lastPos[0],g.fix[0],lastPos[1],g.fix[1] 
	distanceMoved=haversine(lastPos[0],lastPos[1],g.fix[0],g.fix[1])
	#print "Distance moved %f" %distanceMoved
	if( distanceMoved < 100):
		time.sleep(sleep_time)
	lastPos=(g.fix[0],g.fix[1])

