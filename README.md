     _______  __    _  _______  _______  _______  __   __ 
    |       ||  |  | ||       ||       ||       ||  | |  |
    |  _____||   |_| ||   _   ||   _   ||    _  ||  |_|  |
    | |_____ |       ||  | |  ||  | |  ||   |_| ||       |
    |_____  ||  _    ||  |_|  ||  |_|  ||    ___||_     _|
     _____| || | |   ||       ||       ||   |      |   |  
    |_______||_|  |__||_______||_______||___|      |___|
                                                   V0.1  
    "Amy, technology isn't intrinsically good or evil. It's how it's used. Like the Death Ray."
    -Professor Farnsworth

Welcome to Snoopy; a distributed tracking and profiling framework. Snoopy is a work in progress, so please feel free to submit suggestions and/or corrections. This document outlines basic usage. To understand the background a little more, have a look at the following:

- [Snoopy: A distributed tracking and profiling framework](https://www.sensepost.com/blog/7557.html)
- [ZaCon4 - Glenn Wilkinson - Terrorism, tracking, privacy and human interactions](http://vimeo.com/52661183)

1. INTRODUCTION AND OVERVIEW
=============================
Snoopy consists of four components:

* Client software (aka Snoopy Drone software)
* Server software
* Web interface
* Maltego transforms

a. Snoopy Drones
-----------------
The client side software runs on what we call "Drones". A Drone can be any Linux based device that has a WiFi interface (with injection drivers) and outbound internet connectivity. Snoopy has been tested on a Nokia N900 and a laptop running BackTrack. The Drones perform the following two operations:

1. Collect Probe SSIDs from nearby wireless devices
2. Offer a Rogue Access Point for nearby wireless devices to connect to

Collected probe requests (e.g. Bob's iPhone looking for BTHomeHub-4123) are uploaded to the Snoopy server at regular intervals. All devices that associate to the Rogue AP have have their Internet served via the Snoopy Server.

b. Server Software
-------------------
The server populates all probe requests into a database, and uses Wigle to determine GPS coordinates, and Google Maps to determine street addresses (and street view photographs). This means that if you're probing for your home network, I may get a photograph of your house.

Each Drone connects to the server over OpenVPN, and has its own subnet. Associated clients receive an IP address from the Drone, and route traffic via it. This means that on the server we can match client IP addresses (and therefore MAC addresses) to internet activity.

On the server, the following happens:

- Internet traffic is transparently proxied through Squid, which logs all requests to MySQL
- SSLStrip attempts to rewrite webpages without HTTPS
- mitmproxy.py allows arbitrary injection into web pages
- Various scripts run to extract Social Media data (e.g. pulling Facebook profiles)

The network diagram looks like so:

         Client1                        Drone1                                  Snoopy Server
        +----------+            +-----------------------+               +-----------------------+
        |    wlan0-|<---WiFi--->|-at0                   |               |                   eth0|<-squid-sslstrip-mitmproxy->Internet
        |          |    |       | 10.2.0.1              |               |            11.22.33.44|    |
        | dhclient |    |       |                       |               |                       |    Traffic inspection
        |          |    |       |                  tap0-|<-openvpn----->|-tap0                  |    Social media analysis
        +----------+    |       |          192.168.42.2 |           +--/| 192.168.42.1          |
        10.2.0.2        |       +-----------------------+           |   +-----------------------+
                        |                                           |
                        |                                           | route 10.2.0.0 via 192.168.42.2
                        |                                           | route 10.3.0.0 via 192.168.42.3
          Client2       |                                           |
        +----------+    |                                           |
        |    wlan0-|<---+                                           |
        |          |                                                |
        | dhclient |                                                |
        |          |                                                |
        +----------+                                                |
        10.2.0.3                                                    |
                                                                    |
                                                                    |
                                                                    |
          Client3                       Drone2                      |      
        +----------+            +-----------------------+           |
        |    wlan0-|<---WiFi--->|-at0                   |           |
        |          |    |       | 10.3.0.1              |           |
        | dhclient |    |       |                       |           |
        |          |    |       |                  tap0-|<-openvpn--+
        +----------+    |       |          192.168.42.3 |       
        10.3.0.2        |       +-----------------------+       
                        |
                        |       
                        |
          Client4       |                                       
        +----------+    |                                       
        |    wlan0-|<---+                                       
        |          |                                            
        | dhclient |                                            
        |          |                                            
        +----------+
        10.3.0.3

c. The Web Interface
--------------------
Walter wrote a web interface for Snoopy. It can be accessed from http://your-snoopy-server.com:5000/

d. Maltego Transforms
----------------------
Several Maltego transforms exist to graphically explore collected data (see below for more info).


2. INSTALLATION
================
Server installation should be straight forward. It's only been tested on a stock install of Ubuntu 12.04 LTS 32bit. Changes are made to several server components, so it's highly recommended to run the install script on a base installation, and not run much else on that box (if anything). If in doubt, go through the *install.sh* file and manually make the changes. Otherwise, just run (*./install.sh*) the installer.

3. USAGE
========
Once installation is finished you should just be able to type 'snoopy' for the server menu to load. If not (or in doubt) go to the home directory of the user created during the installation phase. Inside the 'snoopy/server/' directory there is a 'snoopy.sh' file which you may run. Below is the menu:

        +---------------------------------------------------------------+
        |                    Welcome to Snoopy V0.1                     |
        |                        SERVER SIDE                            |
        |                                                               |
        |              SensePost Information Security                   |
        |         research@sensepost.com / www.sensepost.com            |
        +---------------------------------------------------------------+
        Date: Thu Nov  1 16:37:08 CET 2012
        Snoopy Server Status: Stopped
        Connected Drones: 0
        Wigle User: setYourWigleAccount

        Would you like to:
        [1] (Re)Start Snoopy server components
        [2] Stop Snoopy server components
        [3] Manage drone configuration packs
        [4] Configure server options
        [5] Set web traffic injection string
        [6] Observe logs
        [X] Exit

        [?] Help

1. Creating drone packs
Option [3] in the menu will allow you to create client side 'packs' for your Drone devices. Each Drone gets its own OpenVPN and SSH keys, DHCP ranges, and routing tables. You will be provided with a download URL per Drone device. Make sure your server and drone have their time set correctly or the VPN connection will not establish.

2. Installing and Running Snoopy on the Drone
You may have up to 100 drones (if you want more, check the source or email me, there's no actual limitation). Installation consists of downloading the configuration pack from the previous step, and running the relevant setup script. For the Nokia N900 an icon will be placed on your Desktop. e.g.:

        haxor@drone001# wget http://snoopy-server.com/secretdir/drone001.tar.gz
        haxor@drone001# tar xzvf drone001.tar.gz
        haxor@drone001# cd snoopy && ./setup_n900.sh

3. Looking up SSID Locations
Create an account on www.wigle.net, and set your credentials via 'Configure server options'

4. Web Interface
You can access the web inteface via http://your-snoopy-server:5000/. You can write your own plugins to traverse and display data. Walter's made is easy for you (check the appendix to this document).

5. Exploring Data with Maltego
In the Snoopy server menu go to 'Configure Server Options' > 'Maltego'. Here you will see URLs for downloading Snoopy entities, machines, and URLs for transforms. In order to use Maltego transforms you will need to:
     - Add Snoopy entities to Maltego 
     - Create an account on http://cetas.paterva.com/TDS/
     - Login to cetas.paterva.com/TDS/
     - Create a seed on cetas.paterva.com/TDS/
     - Add the transform URLs to the created seed
     - Add the seed in Maltego (Manage > Discover Transforms (Advanced) 
     - Enter the name as 'Snoopy', and the seed URL as your seed
     - Add the Snoopy machines to the machines section

Each Snoopy entity can have different transforms applied to it. Drag the 'Snoopy' entity on to your graph to get started. If you don't specify a start or end date in the entities properties it will fetch results for the last 5 minutes by default (this value can be changed in the server configuration menu).

The Snoopy machines allow you to automatically sequence transforms, and filter/delete nodes based on requirements. The source/comments should sufficiently outline how they work.


3. Legal Considerations
=======================
All or some of the Snoopy components may be illegal where you live. Please find out before using the software. In the United Kingdom the probe collection component is legal due to the broadcast nature of the traffic. However, the rogue access point component is most likely illegal in most regions. SensePost takes no responsibility for you getting into trouble from using this tool. 

4. Security Considerations
==========================
Each 'Drone pack' contains OpenVPN and SSH keys. If a Drone is compromised (by theft or
otherwise) it may pose a security risk to your server. It is *highly* recommended that
your Snoopy server run dedicated in its purpose. The user created on the server has the
following automatically added to the *.ssh/authorized_hosts file*, for a little bit of extra security:

    "no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty,command="/usr/bin/rsync ${SSH_ORIGINAL_COMMAND#* }""

5. Future Work
===============
There are lots of thing still to be done / added. This version is rather PoC. 

- Integrate ToR support
- Add filters to easily add other traffic captures (e.g. mDNS)
- Incorporate aGPS hacking (since we already control victims DNS)
- Evilgrade
- Bluetooth/GSM tracking
- WiFi deauth / 3G jamming
- Camera with facial identification
- Stolen cookie Firefox plugin loader
- Replace data upload process (currently all drones rsync with the same user).

6. Known issues / bugs
======================

- SSIDs with unusual characters may cause trouble
- Currently all probe requests are captured and populated into a db. The db gets large rather quickly, especially in busy areas. The database should be normalized, and a decision on whether to keep all probes or not made.
- Originally the probe sniffing was done with Scapy, but replaced with a tshark one liner (due to Scapy's inability to read 802.11 signal strength parameter). A discovered caveat with the old version of tshark available on the N900 is that it does not support outputting the epoch time, only the local time. This messes badly with timezones. If you could compile a new tshark for the N900 that'd be great (here's looking at you PwnieExpress). Point being, make sure your server/drones are all in the same timezone for now.

7. Contact
==============
The code was written by Glenn (with the exception of Walter's web interface). You can
email him via glenn@sensepost.com or bug^H^H^H follow him on Twitter: @glennzw. Glenn's not a developer, and apologies for his poor code. He's a hacker, and this tool let him hack you.

Acknowledgements
-----------------
Thanks for help/advice/input from:

- The SensePost crew (cool place to work).
- DocScrutinizer, and the rest of the #maemo gang on Freenode for N900 help.


---------------------------------------------------------------------------------------
APPENDIX A1. ATTACK SCENARIOS (not endorsed, or encouraged)
---------------------------------------------------------------------------------------

Catching the Spy
----------------
Q. We know that a foreign spy arrives at Heathrow on the 11th November, but we don't know
when or on which flight. Our intel suggests he will stay at the Hilton after arriving,
and catch a flight from Luton airport on the 14th (again we don't know what time or 
destination). He is a master of disguise. How can we identify him?

A. Deploy Snoopy drones at Heathrow, Hilton, and Luton. The 'CommonLocation' Maltego
transform will note the intersection of all devices present at those three locations.
Hopefully only one result - our human target.
Once discovered, we can examine Google maps and street view photographs of where our
spy has travelled to. His identify could be revealed if his device(s) are tricked into
connecting to the Snoopy rogue access point (such as his Facebook, Twitter, or email).

Identifying Undesirables
-------------------
Ask Snoopy to note all individuals who have connected to a WiFi spot in certain sandy^W
undesirable countries.

Tracking Customers
------------------
Deploy Snoopy in your 10 department stores. Note human traffic, repeat customers, types
of customers.

Malware Distribution
--------------------
Inject malicious code to take over client devices and install malware. Exploits can be fired directly from the server to connected victims, due to routing tables.

The London Underground
----------------------
TFL could deploy a Snoopy Drone in each London Underground. They could monitor human traffic, noting peak and trough times/days, and assign/reduce staff accordingly.

Large Scale Human Tracking
--------------------------
Deploy 500 Snoopy Drones all over London. Monitor people's movements when they pass
by a Drone. Interesting human movement patterns are sure to manifest if applied over
weeks/months.

---------------------------------------------------------------------------------------
APPENDIX A2. HARDWARE NOTES
---------------------------------------------------------------------------------------
For a Linux based Desktop/Laptop, the [Alfa AWUS036H](http://is.gd/GOcgNU) card performs average. A more reliable card is the [Ubiquity SR-71](http://is.gd/KnSHWS). Any feedback on what works/doesn't work for you in terms of injection driver support would be appreciated.

For the N900, you will notice that the loading of injection drivers severely reduces
the battery life. The [TecNet 6600mAh](http://is.gd/pQz9X2) battery pack gave around 6-8 hours in testing. You will, however, need an [adapter](http://is.gd/Mavr11) to plug the N900 into any battery pack. Reducing (or disabling) the GPS polling frequency will also better serve battery life.

Tips on connecting your N900 to your laptop via USB (for the purpose of SSH) can be
found [here](http://wiki.maemo.org/N900_USB_networking)

I'm currently testing on the RaspberryPi, Alfa R36 mini AP, and SheevaPlug. Results to
follow.

---------------------------------------------------------------------------------------
APPENDIX A3. SNOOPY MALTEGO SCRIPTING
---------------------------------------------------------------------------------------
You can create your own Maltego transforms to explore collected data. The ones supplied
are mostly to demonstrate what can be done. Check the source code, and go read:

- http://www.paterva.com/web6/documentation/developer.php
- http://www.paterva.com/web6/documentation/developer-tds.php

Contact glenn@sensepost.com if you have any queries (or ask the awesome Maltego guys).

---------------------------------------------------------------------------------------
APPENDIX A4. SNOOPY WEB INTERFACE SCRIPTING
---------------------------------------------------------------------------------------

# Introduction
The web ui code is accessible via 
~user/snoopy/server/bin/snoopy/src/snoopy/

# Requirements (already installed)
## Python Packages
* [Beaker](http://beaker.readthedocs.org/)
* [cryptacular](http://pypi.python.org/pypi/cryptacular/)
* [Flask](http://flask.pocoo.org/)
* [MySQLdb](http://mysql-python.sourceforge.net/MySQLdb.html)
* [SQLAlchemy](http://sqlalchemy.org/)


# Plug-ins
Plug-ins consist of two parts:
* Back-end (data providing) part, written in Python
* Front-end (displaying) part, written in JavaScript (optional)

## Back-end
A plug-in is a callable that is dynamically loaded by the Snoopy application.
Let's start with an example:

    from snoopy import db, pluginregistry

    @pluginregistry.add('client-data', 'ssidlist', 'SSID List', js='/static/js/ssidlist.js')
    def ssid_list(mac):
        with db.SessionCtx() as session:
            query = session.query(
                distinct(db.Probe.probe_ssid) # SELECT DISTINCT probe_ssid FROM probes
            ).filter_by(
                device_mac=mac                # WHERE device_mac=$mac
            ).order_by(
                db.Probe.probe_ssid           # ORDER BY probe_ssid
            )
            return query.all()

Now for the blow-by-blow...

    from snoopy import db, pluginregistry

We need `db` to access the Snoopy database and `pluginregistry` to register our
plug-in.

    @pluginregistry.add('client-data', 'ssidlist', 'SSID List', js='/static/js/ssidlist.js')

This is how we register our plug-in (which can be any callable). The first
argument specifies the name of the group that this plug-in falls into. We
specified `client-data`, since this plug-in accepts a MAC address and returns
data to be displayed in a client data window. Apart from `client-data`, there
is also the `session-data` group of plug-ins that operate on proximity
sessions. The second parameter is the plug-in name. This name is for internal
use only and should be JSON-friendly. The third parameter is the plug-in title.
Essentially it is the same as the name, but the title is displayed in the GUI.
More specifically, this is the title of the data section in the client data
window.

All keyword arguments after the title are saved as options. While the plug-in
system does not require any options, Snoopy supports the `js` option. This
option specifies the **URL** (from the browser side, not from Snoopy's/the
server's side) of the JavaScript component of this plug-in.

    def ssid_list(mac):

This plug-in is a simple function. It accepts a MAC address string, as
per `client-data` plug-ins' definition. The name of the callable is not used.

The body of this example plug-in simply performs a SQLAlchemy query that
basically does `SELECT DISTINCT probe_ssid FROM probes WHERE device_mac=$mac`
and returns the results as a list. The return values of plug-ins are usually
added as part of a JSON response. Therefore the results has the limitation that
it must be JSON-friendly (as supported by Flask's `jsonify()` function).

As simple as that!

## Front-end
Front-end plug-ins for client data are referred to as client data handlers.
They are registered via the `Snoopy.registerPlugin(sectionName, dataHandler)`
function. `sectionName` is the name of the data section that the data handler
wants to handle. This name is the same as the back-end plug-in name that
generated the data. The `dataHandler` must be a function with the following
signature: `function($section, clientData) {...}`. `$section` is a jQuery
object of the div element where the data handler may display data or affect
changes. The client data (generated by the back-end plug-in) is given in the
`clientData` parameter.

Since the data handler's only allowed output is changes to the given div
(`$section`), no return value is necessary.

