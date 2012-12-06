#!/usr/bin/python
import sys
import os
from Maltego import *
import stawk_db
import logging
import datetime

logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

sys.stderr = sys.stdout

def main():

    fb_view_url=None
    try:
                p=os.path.dirname(os.path.realpath(__file__))
                f=open("%s/../setup/webroot_guid.txt"%p,"r")
                fb_view_url=f.readline().strip() + "/web_data/facebook/"
    except:
                logging.debug("Warning: Couldn't determind streetview webserver folder")



    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()


	try:

		mac=m.AdditionalFields['mac']
		drone=m.AdditionalFields['drone']

		logging.debug(mac)
		logging.debug(drone)

		logging.debug("SELECT id,name,gender,locale,network,link,degree FROM facebook,dhcp_leases WHERE facebook.ip=dhcp_leases.ip AND mac=%s"%(mac))

		cursor.execute("SELECT id,name,gender,locale,network,link,degree FROM facebook,dhcp_leases WHERE facebook.ip=dhcp_leases.ip AND mac=%s",(mac))
		results=cursor.fetchall()

		for row in results:
			id,name,gender,locale,network,link,degree=row[0],row[1],row[2],row[3],row[4],row[5],row[6]

                        if id != None:
                                id=id.encode('utf8','xmlcharrefreplace')
                        if name != None:
                                name=name.encode('utf8','xmlcharrefreplace')
                        if gender != None:
                                gender=gender.encode('utf8','xmlcharrefreplace')
                        if locale != None:
                                locale=locale.encode('utf8','xmlcharrefreplace')
                        if network != None:
                                network=network.encode('utf8','xmlcharrefreplace')
                        else:  
                                network="-"
                        if link != None:
                                link=link.encode('utf8','xmlcharrefreplace')

			NewEnt=TRX.addEntity("maltego.FacebookObject",name)
			NewEnt.addAdditionalFields("id","id","nostrict",id)
			NewEnt.addAdditionalFields("gender","gender","nostrict",gender)
			NewEnt.addAdditionalFields("locale","locale","nostrict",locale)
			NewEnt.addAdditionalFields("network","network","nostrict",network)
			NewEnt.addAdditionalFields("link","link","nostrict",link)
			NewEnt.addAdditionalFields("degree","degree","nostrict",degree)

			NewEnt.addAdditionalFields("drone","drone","nostrict",drone)
			NewEnt.addAdditionalFields("mac","mac","nostrict",mac)

			logging.debug("Facebook profile photo - %s/%s/profile.jpg" % (fb_view_url,id))
			if( fb_view_url != None):
                                NewEnt.addAdditionalFields("facebook_profile_photo","Profile","strict","%s/%s/profile.jpg"%(fb_view_url,id))
                                NewEnt.setIconURL("%s/%s/profile.jpg" % (fb_view_url,id))




        except Exception, e:
                logging.debug("Exception:")
                logging.debug(e)


        TRX.returnOutput()
    
main()
                
