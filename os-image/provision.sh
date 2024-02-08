#!/bin/bash

### BEGIN INIT INFO
# Provides:          provision.sh
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start provisioning on first boot
# Description:       Install Docker Engine, GGC and provision device on AWS
### END INIT INFO

# Set up device with fleet provisioning is based on AWS documentation: https://docs.aws.amazon.com/greengrass/v2/developerguide/fleet-provisioning.html#fleet-provisioning-prerequisites

# Giving the device time to boot (second)
sleep 60

# Move to user directory where provisioning files are stored
cd /home/pi

# Save stdout/stderr to a log file
exec >provision_log.txt 2>&1

# Get serial number of device
SERIAL_NUMBER=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2)

n=1
while IFS= read -r "var$n"; do
  n=$((n + 1))
done < ./config_parameters.txt

REGION=$var1
iot_data_endpoint=$var2
iot_credentials_endpoint=$var3
TES_ROLE_ALIAS_NAME=$var4
FLEET_TEMPLATE_NAME=$var5

# ---------------------------- Install Docker Engine ----------------------------
# Installation of Docker Engine is based on Docker documentation: https://docs.docker.com/engine/install/debian/
echo "************ Installing Docker... ************"
# update-alternatives --set iptables /usr/sbin/iptables-legacy
# update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get -y install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world
echo "Docker installed!"

# ---------------------------- Download certificates to the device ----------------------------
echo "************ Download certificates to the device... ************"
sudo mkdir -p /greengrass/v2
sudo chmod 755 /greengrass
sudo cp -r ./claim.pem.crt /greengrass/v2
sudo cp -r ./claim.private.pem.key /greengrass/v2
sudo curl -o /greengrass/v2/AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
echo "Done"

# ---------------------------- Set up the device environment ----------------------------
echo "************ Set up the device environment... ************"
sudo apt update
sudo apt -y install default-jdk
sudo useradd --system --create-home ggc_user
sudo groupadd --system ggc_group
sudo sed -i 's|root.*|root    ALL=(ALL:ALL) ALL|' "/etc/sudoers"
echo "Done"

# ---------------------------- Download the AWS IoT Greengrass Core software ----------------------------
echo "************ Download the AWS IoT Greengrass Core software... ************"
curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip
jarsigner -verify -certs greengrass-nucleus-latest.zip
unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && rm greengrass-nucleus-latest.zip
ggc_version=$(java -jar ./GreengrassInstaller/lib/Greengrass.jar --version | sed 's|AWS Greengrass v||')
echo "Version of the AWS IoT Greengrass Core software : $ggc_version"
echo "Done"

# ---------------------------- Download the AWS IoT fleet provisioning plugin ----------------------------
echo "************ Download the AWS IoT fleet provisioning plugin... ************"
curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/aws-greengrass-FleetProvisioningByClaim/fleetprovisioningbyclaim-latest.jar > GreengrassInstaller/aws.greengrass.FleetProvisioningByClaim.jar
echo "Done"

# ---------------------------- Install the AWS IoT Greengrass Core software and provision device on AWS ----------------------------
echo "************ Install the AWS IoT Greengrass Core software and provision device on AWS... ************"
# Edit configuration file
sed -i 's|version: ""|version: "'$ggc_version'"|' "config.yaml"
sed -i 's|awsRegion: ""|awsRegion: "'$REGION'"|' "config.yaml"
sed -i 's|iotDataEndpoint: ""|iotDataEndpoint: "'$iot_data_endpoint'"|' "config.yaml"
sed -i 's|iotCredentialEndpoint: ""|iotCredentialEndpoint: "'$iot_credentials_endpoint'"|' "config.yaml"
sed -i 's|iotRoleAlias: ""|iotRoleAlias: "'$TES_ROLE_ALIAS_NAME'"|' "config.yaml"
sed -i 's|provisioningTemplate: ""|provisioningTemplate: "'$FLEET_TEMPLATE_NAME'"|' "config.yaml"
sed -i 's|SerialNumber: ""|SerialNumber: "'$SERIAL_NUMBER'"|' "config.yaml"

sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
  -jar ./GreengrassInstaller/lib/Greengrass.jar \
  --trusted-plugin ./GreengrassInstaller/aws.greengrass.FleetProvisioningByClaim.jar \
  --init-config ./config.yaml \
  --component-default-user ggc_user:ggc_group \
  --setup-system-service true
echo "Done"

# ---------------------------- Delete all unused files after provisioning ----------------------------
# Delete all provisioning files
rm ./config_parameters.txt
rm ./claim.private.pem.key
rm ./claim.pem.crt
rm ./config.yaml
rm -rf ./GreengrassInstaller

# Delete self to provision once
rm "${0}"