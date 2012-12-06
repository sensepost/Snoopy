#!/bin/bash
# glenn@sensepost.com 
# Snoopy // 2012
# By using this code you agree to abide by the supplied LICENSE.txt

echo "+-----------------------------------------------------------------------+
+ SensePost Information Security                                        +
+ Snoopy Drone Installer                                                +
+ http://www.sensepost.com/labs / research@sensepost.com		+
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
+ This script should be run on a PwnPhone N900 installation. You'd need +
+ to manually install the PowerKernel if you don't want to use the 	+
+ PwnPhone. I'll install some additional packages now.	              	+
+-----------------------------------------------------------------------+
"

#Get current path
sd=$(cd $(dirname "$0"); pwd)

#Make sure everything is +x
for i in `find . -iname '*.py'`; do chmod +x $i; done
for i in `find . -iname '*.sh'`; do chmod +x $i; done

#Install stuff
#apt-get update
apt-get install -y tshark
apt-get install -y python-location
apt-get install -y sed-gnu
apt-get install -y openssh
apt-get install -y bash
apt-get install -y rsync
apt-get install -y netcat
apt-get install -y macchanger

#Copy the drivers from the PwnPhone setup, to ensure they match the PwnPhone 
# PowerKernel installation
cp /home/user/MyDocs/pwnphone/drivers/*.ko $sd/configs/drivers/ 

echo "+-----------------------------------------------------------------------------+"
echo "+ Copying Desktop icons                                                       +"
echo "+-----------------------------------------------------------------------------+"
# Desktop icons

sed -i "s,^Exec=.*,Exec=osso-xterm -e \"sudo $sd/snoopy.sh\"," ./setup/snoopy.desktop
cp ./setup/snoopy.desktop /usr/share/applications/hildon/
cp ./setup/snoopy.png /opt/usr/share/pixmaps/

#NB Don't manually update /etc/sudoers on N900
echo "user ALL = NOPASSWD: $sd/snoopy.sh" > /etc/sudoers.d/snoopy.sudoers
update-sudoers

echo "+----------------------------------------------------------------------------+"
echo "+ Done. You should have a new icon on your Desktop			   +"
echo "+----------------------------------------------------------------------------+"
