#!/usr/bin/python
# -*- coding: utf-8 -*-
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

import sys
import os
from Maltego import *
import stawk_db
import logging
from wigle_api_lite import fetchLocations
import time
from xml.sax.saxutils import escape

logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

sys.stderr = sys.stdout
def main():

    street_view_url=None
    try:
		p=os.path.dirname(os.path.realpath(__file__))
		f=open("%s/../setup/webroot_guid.txt"%p,"r")
		street_view_url=f.readline().strip() + "/web_data/street_views/"
    except:
		logging.debug("Warning: Couldn't determind streetview webserver folder")



    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)

	logging.debug(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()

	ssid=m.Value

	try:
		cursor.execute("SELECT gps_lat,gps_long,country,code,address FROM wigle WHERE overflow = 0 AND ssid=%s LIMIT 500",(ssid)) #Can be useful to LIMIT 5, or some such. Make sure to do the same in fetchClientsFromCountry.py
		#cursor.execute("SELECT gps_lat,gps_long,country,code,address FROM wigle WHERE overflow = 0 AND ssid=%s",(ssid))
		results=cursor.fetchall()	
		for row in results:
			# How to Unicode, plox?
			lat=row[0]
			long=row[1]
#			country=row[2].decode('raw_unicode_escape').encode('ascii','xmlcharrefreplace')
#			code=row[3].decode('raw_unicode_escape').encode('ascii','xmlcharrefreplace')
#			address=row[4].decode('utf-8').encode('ascii','xmlcharrefreplace')
			country=row[2].encode('utf8','xmlcharrefreplace')
			code=row[3].encode('utf8','xmlcharrefreplace')
			address=row[4].encode('utf8','xmlcharrefreplace')

			#NewEnt=TRX.addEntity("snoopy.ssidLocation",country)
			NewEnt=TRX.addEntity("maltego.Location",country)
			NewEnt.addAdditionalFields("latitude","latitude","strict",lat)
			NewEnt.addAdditionalFields("longitude","longitude","strict",long)
			NewEnt.addAdditionalFields("country", "Country", "strict", country)
		        NewEnt.addAdditionalFields("countrycode", "Country Code", "strict", code)
#	       		NewEnt.addAdditionalFields("streetaddress", "Street Address", "strict", "<![CDATA[" + address + "]]>")
			NewEnt.addAdditionalFields("streetaddress", "Street Address", "strict", address)
			NewEnt.addAdditionalFields("googleMap", "Google map", "nostrict", escape("http://maps.google.com/maps?t=h&q=%s,%s"%(lat,long)))
	
			logging.debug(street_view_url)	
			if( street_view_url != None):
				NewEnt.addAdditionalFields("streetview","streetview","strict","%s/%s,%s.jpg"%(street_view_url,lat,long))	
				NewEnt.setIconURL("%s/%s,%s.jpg" % (street_view_url,lat,long))


	except Exception,e:
		logging.debug(e)


	logging.debug(TRX)
        TRX.returnOutput()
   

def debug1(self):
        print "<MaltegoMessage>";
        print "<MaltegoTransformResponseMessage>";

        print "<Entities>"
        for i in range(len(self.entities)):
                self.entities[i].returnEntity();
        print "</Entities>"

        print "<UIMessages>"
        for i in range(len(self.UIMessages)):
                print "<UIMessage MessageType=\"" + self.UIMessages[i][0] + "\">" + self.UIMessages[i][1] + "</UIMessage>";
        print "</UIMessages>"

        print "</MaltegoTransformResponseMessage>";
        print "</MaltegoMessage>";


 
main()
                
