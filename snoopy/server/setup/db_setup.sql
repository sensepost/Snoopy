DROP database IF EXISTS snoopy;

CREATE database snoopy charset=utf8;
use snoopy;

GRANT ALL on snoopy .* TO snoopy@'localhost' IDENTIFIED BY 'RANDOMPASSWORDGOESHERE';
FLUSH PRIVILEGES;

CREATE TABLE sslstrip(
	timestamp DATETIME,
	secure TINYINT,
	host VARCHAR(50),
	domain VARCHAR(50),
	src_ip VARCHAR(16),
	url VARCHAR(70),
	post VARCHAR(400)
);

CREATE TABLE facebook(
	id VARCHAR(20),
	ip VARCHAR(20),
	name VARCHAR(100),
	first_name VARCHAR(100),
	last_name VARCHAR(100),
	link VARCHAR(100),
	username VARCHAR(100),
	gender VARCHAR(10),
	locale VARCHAR(40),
	network VARCHAR(40),
	it VARCHAR(20),
	degree INT,
	cookie TEXT,
	password VARCHAR(50),

	PRIMARY KEY(id)
);

CREATE TABLE facebook_friends(
	id VARCHAR(20),
	friend_id VARCHAR(20)
);


CREATE TABLE probes(
	monitor_id VARCHAR(20), INDEX(monitor_id),
	device_mac VARCHAR(12), INDEX(device_mac),
	location VARCHAR(200),
	probe_ssid varchar(100), INDEX(probe_ssid),
	signal_db INT(11),
	timestamp DATETIME, INDEX(timestamp),
	run_id VARCHAR(20),
	proximity_session VARCHAR(20),
	priority TINYINT,
	mac_prefix VARCHAR(6), INDEX(mac_prefix),
	PRIMARY KEY(monitor_id,device_mac,probe_ssid,timestamp)
);

CREATE TABLE gps_movement(
	monitor_id VARCHAR(20),
	run_id VARCHAR(20),
	timestamp DATETIME,
	gps_lat decimal(8,6),
	gps_long decimal(8,6),
	accuracy decimal(8,6),
	PRIMARY KEY(monitor_id, timestamp)
);

CREATE TABLE wigle(
	ssid VARCHAR(100), INDEX(ssid),
	gps_long decimal(11,8),
	gps_lat decimal(11,8),
	last_update DATETIME,
	mac VARCHAR(12),
	overflow SMALLINT(6),
	country VARCHAR(30),
	code VARCHAR(10),
	address VARCHAR(200)
);

CREATE TABLE dhcp_leases(
	mac CHAR(12),
	ip VARCHAR(16), INDEX(ip),
	hostname VARCHAR(40),
	expire DATETIME,
	mac_prefix CHAR(6), INDEX (mac_prefix),
	ip_prefix VARCHAR(7), INDEX (ip_prefix),
	PRIMARY KEY(mac,ip)
);

CREATE TABLE squid_logs(
	timestamp DATETIME,
	client_ip VARCHAR(16), INDEX(client_ip),
	http_code INT,
	method VARCHAR(4),
	domain VARCHAR(50),
	host VARCHAR(50),
	url TEXT,
	ua VARCHAR(200),
	cookies TEXT
);

CREATE TABLE drone_conf(
	id VARCHAR(30),
	comment VARCHAR(50),
	ip_tap VARCHAR(16),
	ip_wifi VARCHAR(16),
	ip_prefix VARCHAR(7), INDEX(ip_prefix),
	download_link VARCHAR(32)
);

CREATE TABLE mac_vendor(
	mac VARCHAR(6), INDEX(mac),
	vendor_short VARCHAR(12),
	vendor_long VARCHAR(30)
);


CREATE TABLE snoopy_user (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255),
  password varchar(255) NOT NULL,
  is_admin tinyint(1) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
);

CREATE VIEW get_fb_from_squid AS SELECT SUBSTRING(cookies,7+(SELECT LOCATE("c_user",cookies)),(SELECT (LOCATE(";",cookies, (SELECT LOCATE("c_user",cookies)))) -(SELECT LOCATE("c_user",cookies)+7))) as c_user, cookies,client_ip FROM squid_logs WHERE cookies LIKE '%c_user%' GROUP BY c_user;

CREATE VIEW snoopy_web_logs AS
SELECT DISTINCT id AS drone_id,mac,squid_logs.client_ip,hostname AS client_hostname,domain,host,url,ua,cookies,timestamp
FROM
	drone_conf,
	squid_logs,
	dhcp_leases

WHERE
	SUBSTRING(drone_conf.ip_wifi,1,LOCATE('.', drone_conf.ip_wifi, LOCATE('.', drone_conf.ip_wifi)+1)) = SUBSTRING(squid_logs.client_ip,1,LOCATE('.',squid_logs.client_ip, LOCATE('.',squid_logs.client_ip)+1)) 
	AND squid_logs.client_ip=dhcp_leases.ip;

CREATE VIEW proximity_sessions AS
SELECT monitor_id,location,device_mac, MIN(timestamp) AS first_probe,MAX(timestamp) AS last_probe,MAX(timestamp)-MIN(timestamp) AS duration, mac_vendor.vendor_short FROM probes, mac_vendor WHERE probes.mac_prefix=mac_vendor.mac GROUP BY monitor_id,proximity_session ORDER BY first_probe;
