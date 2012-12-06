#!/usr/bin/python
# -*- coding: utf-8 -*-
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

from Maltego import *
import logging
import requests
import json
import stawk_db
import re

logging.basicConfig(level=logging.DEBUG,filename='/tmp/maltego_logs.txt',format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')

sys.stderr = sys.stdout

def main():

    print "Content-type: xml\n\n";
    MaltegoXML_in = sys.stdin.read()
    if MaltegoXML_in <> '':
        m = MaltegoMsg(MaltegoXML_in)
    
	cursor=stawk_db.dbconnect()
        TRX = MaltegoTransform()

	try:
		logging.debug("Here we go")
		for item in m.TransformSettings.keys():
       		 	logging.debug("N:"+item+" V:"+m.TransformSettings[item])
	
#		logging.debug(MaltegoXML_in)

		radius="5" #miles
		lat=m.AdditionalFields['lat']
		lng=m.AdditionalFields['long']
		if 'radius' in m.AdditionalFields:
			radius=m.AdditionalFields

		logging.debug("Tweep cords to search - %s,%s (%s miles)" %(lat,lng,radius))
	
		r=requests.get("https://search.twitter.com/search.json?q=geocode:%s,%s,%smi"%(lat,lng,radius))
		tw=json.loads(r.text)
		
		logging.debug("Tweep results - %d"%len(tw['results']))
		for tweep in tw['results']:
				name=tweep['from_user_name'].encode('utf8','xmlcharrefreplace')
				username=tweep['from_user'].encode('utf8','xmlcharrefreplace')
				uid=tweep['from_user_id_str'].encode('utf8','xmlcharrefreplace')
				recent_tweet=tweep['text'].encode('utf8','xmlcharrefreplace')
				img=tweep['profile_image_url'].encode('utf8','xmlcharrefreplace')				
				profile_page="http://twitter.com/%s"%username
				largephoto=re.sub('_normal','',img)


        			NewEnt=TRX.addEntity("maltego.affiliation.Twitter", name)
				NewEnt.addAdditionalFields("uid","UID","strict",uid)
				NewEnt.addAdditionalFields("affiliation.profile-url","Profile URL","strict",profile_page)
				NewEnt.addAdditionalFields("twitter.screen-name","Screen Name","strict",username)
				NewEnt.addAdditionalFields("person.fullname","Real Name","strict",name)
				NewEnt.addAdditionalFields("photo","Photo","nostrict",largephoto)
				NewEnt.addAdditionalFields("tweet","Recent Tweet","nostrict",recent_tweet)
				NewEnt.setIconURL(img)			

        except Exception, e:
                logging.debug("Exception:")
                logging.debug(e)


        TRX.returnOutput()
    
main()
                
