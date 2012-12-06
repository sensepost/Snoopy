import stawk_db
import datetime

cursor=stawk_db.dbconnect()
drones=[]

day='2012-08-24 '

st=day+'00:00:00'
fi=day+'23:59:59'
cursor.execute("SELECT monitor_id,min(timestamp),max(timestamp) FROM probes WHERE timestamp > %s AND timestamp <%s GROUP BY monitor_id", (st,fi))

for r in cursor.fetchall():
	drones.append((r[0],r[1],r[2]))

for d in drones:
	drone_id = d[0]
	print drone_id
	fp,lp=d[1],d[2]
	fp=fp - datetime.timedelta(minutes=fp.minute, seconds=fp.second)
	lp=lp - datetime.timedelta(minutes=(lp.minute-60), seconds=lp.second)

	hours=(((lp-fp)).seconds)/3600
	for h in range(hours):
		frm=fp + datetime.timedelta(hours=h)
		to=fp + datetime.timedelta(hours=h+1)
	
		cursor.execute("SELECT COUNT( DISTINCT (device_mac)) FROM probes where timestamp > %s AND timestamp < %s AND monitor_id=%s",(frm,to,drone_id))
		count=int(cursor.fetchone()[0])
		print "%s to %s = %d" %(frm.strftime("%H:%M"),to.strftime("%H:%M"),count)
