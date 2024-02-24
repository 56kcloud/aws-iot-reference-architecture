#!/bin/bash

# Enable SSH
touch /boot/firmware/ssh

# Add password to pi user
echo 'pi:welcome' | chpasswd

# Enable zswap with default settings
sed -i -e 's/$/ zswap.enabled=1/' /boot/firmware/cmdline.txt

# Force automatic rootfs expansion on first boot:
# https://forums.raspberrypi.com/viewtopic.php?t=174434#p1117084
wget -O /etc/init.d/resize2fs_once https://raw.githubusercontent.com/RPi-Distro/pi-gen/master/stage2/01-sys-tweaks/files/resize2fs_once
chmod +x /etc/init.d/resize2fs_once
systemctl enable resize2fs_once

# Run provision script on first boot
sed -i -e '$i \sudo bash -c '\''/usr/bin/bash /home/pi/provision.sh > /home/pi/provision.log 2>&1'\'' &\n' "/etc/rc.local"

# Make the provision script executable
chmod +x /home/pi/provision.sh