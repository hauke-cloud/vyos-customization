<!-- llm-readme-management spec=1 commit=0a51a9ca9de64d2324b201be6a94f9b5be916b95 template=default model=qwen3.6-35b-a3b digest=598d66067ca0 generated=2026-09-09T00:19:21Z -->
<a href="https://hauke.cloud" target="_blank"><img src="https://img.shields.io/badge/home-hauke.cloud-brightgreen" alt="hauke.cloud" style="display: block;" /></a>
<a href="https://github.com/hauke-cloud" target="_blank"><img src="https://img.shields.io/badge/github-hauke.cloud-blue" alt="hauke.cloud Github Organisation" style="display: block;" /></a>
<a href="https://github.com/hauke-cloud/llm-readme-management" target="_blank"><img src="https://img.shields.io/badge/template-default-orange" alt="Repository type - default" style="display: block;" /></a>


# Vyos Customization


<img src="https://raw.githubusercontent.com/hauke-cloud/.github/main/resources/img/organisation-logo-small.png" alt="hauke.cloud logo" width="109" height="123" align="right">


<llm header>

This repository provides a Debian package that ships custom default configuration files and an automated disk installer for VyOS appliances. It produces a ready-to-install `.deb` archive containing predefined networking, SSH, NTP, and console settings. You should keep reading if you are an operator or build-pipeline author provisioning VyOS systems and need to automate initial appliance configuration.

</llm>


## :book: Description

<llm description>

This repository provides a Debian package that automates the initial configuration and disk installation of VyOS appliances. When provisioning fresh VyOS systems, you need to apply predefined networking, SSH, NTP, console, and syslog settings before the first boot. The package ships a default `config.boot.default` file that applies these settings immediately upon startup, removing the need for manual post-installation configuration.

To streamline deployment in automated workflows, the package also includes an `install-image` helper script. This script non-interactively converts a live VyOS ISO into a bootable disk image by partitioning the target drive, copying the kernel and root filesystem, configuring GRUB for BIOS and UEFI targets, and setting up overlay persistence.

- Ships a default `config.boot.default` file with predefined hostname, credentials, WAN DHCP, SSH, NTP, console, and syslog settings.
- Provides an automated `install-image` script that partitions disks, installs GRUB, and configures persistence for the root filesystem.
- Bundles all files into a standard Debian package for straightforward integration into Packer or custom build pipelines.

</llm>


## 🚀 Getting started

<llm getting_started hint="Assume nothing about the ecosystem beyond what the analysis names. If the repository has no build step, say what a reader does with it instead.">

1. Clone the repository and enter its directory.
```bash
git clone https://github.com/hauke-cloud/vyos-customization.git
cd vyos-customization
```
2. Install the required build dependencies on your Debian-derived system.
```bash
sudo apt-get install -y dpkg-dev debhelper
```
3. Build the architecture-independent `.deb` package in the parent directory.
```bash
dpkg-buildpackage -us -uc -b
```

</llm>


## :airplane: Usage

<llm usage>

- **Build locally:** On a Debian-derived system, install the required dependencies and compile the package:
  ```bash
  sudo apt-get install -y dpkg-dev debhelper
  dpkg-buildpackage -us -uc -b
  ```
  This produces the `.deb` file in the parent directory.

- **Publish via CI:** You trigger automated builds by pushing a `v*` tag or dispatching the workflow manually. The workflow extracts the version from `debian/changelog`, builds the package with `jiro4989/build-deb-action@v3`, and publishes it as a GitHub Release artifact via `softprops/action-gh-release@v1`.

- **Run the disk installer:** Once the package is installed on a target VyOS system, you execute the non-interactive installer script. It reads configuration from environment variables:
  ```bash
  export IMAGE_NAME="VyOS-1.5"
  export DISK="/dev/sda"
  export PASSWORD="vyos"
  export CONSOLE_TYPE="tty"
  sudo /usr/local/bin/install-image
  ```
  The script partitions the target disk, copies the kernel and rootfs, generates GRUB menu entries with normal, password-reset, and recovery boot options, and installs GRUB to i386-pc, x86_64-efi, or arm64-efi targets.

</llm>


## 📄 License

This Project is licensed under the GNU General Public License v3.0

- see the [LICENSE](LICENSE) file for details.


## :coffee: Contributing

To become a contributor, please check out the [CONTRIBUTING](CONTRIBUTING.md) file.


## :email: Contact

For any inquiries or support requests, please open an issue in this
repository or contact us at [contact@hauke.cloud](mailto:contact@hauke.cloud).
