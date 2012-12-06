#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# Don't run directly, but via snoopy.sh
# This Script starts various Snoopy components

#ToDo: Incorporate all Snoopy components into a single snoopy.py file.

import logging
import prox_guid
import pytail
import facebook
import ssid_to_loc

import os
import time
import sys
import signal
from multiprocessing import Process

snoopyBinPath=os.path.dirname(os.path.realpath(__file__))

sys.path.append("%s/snoopy/src/snoopy"%snoopyBinPath)
from snoopy.web import main as webmain
webmain.app.root_path = "%s/snoopy/src/snoopy/"%snoopyBinPath

goFlag=True

def signal_handler(signal, frame):
	global goFlag
        logging.debug('Caught SIGINT, ending.')
	goFlag=False
signal.signal(signal.SIGINT, signal_handler)

def main(snoopyDir):

	global goFlag
	while ( goFlag ):

		logging.basicConfig(filename="%s/logs/snoopy.log"%(snoopyDir),level=logging.INFO,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
		logging.info("\n--------------------------------------------------------------")
		logging.info("Main Snoopy Process starting. Divert all power to the engines!")
		pool=[]
		pool.append( Process(target=prox_guid.main) )
		pool.append( Process(target=facebook.main, args=('%s'%(snoopyDir),)) )
		pool.append( Process(target=pytail.main, args=('%s/uploads/'%(snoopyDir),)) )	
		pool.append(Process(target=ssid_to_loc.main) )
		pool.append(Process(target=webmain.start))
	
		for p in pool:
			p.start()
	
		all_good=True
		while all_good and goFlag:
			for p in pool:
				if not p.is_alive():
					all_good = False
			time.sleep(2)
	
		for p in pool:
			p.terminate()
	
		if(  goFlag ):
			logging.warning("One of my processes died, I'll restart all")
			main(snoopyDir)
	
	logging.debug("Process ended")

if __name__ == "__main__":
	snoopyDir=sys.argv[1]
	try:
        	main(snoopyDir)
	except Exception, e:
		logging.error("Main Snoopy thread exception: %s" %str(e))

