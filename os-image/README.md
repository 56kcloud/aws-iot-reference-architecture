[![Build OS](https://github.com/56kcloud/aws-iot-reference-architecture/actions/workflows/build-image.yml/badge.svg)](https://github.com/56kcloud/aws-iot-reference-architecture/actions/workflows/build-image.yml)

# Custom OS image
## About
Creating a custom OS image offers a number of advantages in this context :
- **Custom configuration** : By creating a custom OS image, the entire system can be pre-configured according to the specific needs of the application or infrastructure. This includes system settings, installed software, permissions, users, start-up scripts, etc.
- **Security** : A custom OS image allows to put in place specific security measures to meet the requirements of the application or environment. Security configurations can be applied, unnecessary services disabled and security patches applied as soon as the image is created.
- **Efficiency** : By including only the components needed for the application, a custom OS image can be lighter and more efficient in terms of resource consumption. This can improve performance and reduce the potential attack surface.
- **Reproducibility** : Creating a custom OS image makes it easy to reproduce the working environment on multiple devices in a consistent way. This makes configuration management easier and ensures consistency across different devices.
- **Compatibility** : A custom OS image can be tailored to meet the specific hardware requirements of the infrastructure. This ensures greater compatibility with specific peripherals, drivers and hardware components.

## How it works
Image creation is managed by Packer, an open source tool for automating image creation. Packer follows a process defined by the JSON configuration [raspios-lite.json](./raspios-lite.json).

Here's how it works in detail :
1. **Packer configuration** ([raspios-lite.json](./raspios-lite.json)) : The Packer configuration file describes all the steps required to create the image. It specifies the builders (in this case, the Arm builder), the provisioners that configure the image, the base image sources, and other parameters.
2. **Running Packer**: In this project, Packer runs in a Docker environment. When the `docker run` command is executed, the tool starts the build process following the specified configuration.
3. **Packer builder ARM plugin** : The Arm builder is responsible for creating the image for the Arm architecture. It uses the Arm build model to create a custom image based on the specifications.
4. **Provisioning** : Provisioners in the configuration file are run to configure the image. This can include installing software, configuring system parameters, etc. In this case, some system settings are configured using the bash script [set_os.sh](./set_os.sh). The provisioning script [provision.sh](./provision.sh) used to install the necessary software is saved in the image and configured to be run when the OS is booted for the first time. Finally, the claim certificate and its private key are saved in the image.
5. **Build complete**: Once all build and provisioning steps have been successfully completed, Packer creates a custom image in the specified format (*.img* in this case).

## Notes
⚠️ The base image used for this architecture is Raspberry Pi OS Lite based on Debian.

## Learn more
- [Packer](https://www.packer.io)
- [Packer plugin to build Arm images](https://github.com/mkaczanowski/packer-builder-arm)
- [Raspberry Pi OS images](https://downloads.raspberrypi.org/raspios_lite_arm64/images/)