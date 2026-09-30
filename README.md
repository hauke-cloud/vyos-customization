<!-- llm-readme-management spec=1 commit=0a51a9ca9de64d2324b201be6a94f9b5be916b95 template=default model=qwen3.8-27b-q4 digest=598d66067ca0 generated=2026-09-30T17:23:11Z -->
<a href="https://hauke.cloud" target="_blank"><img src="https://img.shields.io/badge/home-hauke.cloud-brightgreen" alt="hauke.cloud" style="display: block;" /></a>
<a href="https://github.com/hauke-cloud" target="_blank"><img src="https://img.shields.io/badge/github-hauke.cloud-blue" alt="hauke.cloud Github Organisation" style="display: block;" /></a>
<a href="https://github.com/hauke-cloud/llm-readme-management" target="_blank"><img src="https://img.shields.io/badge/template-default-orange" alt="Repository type - default" style="display: block;" /></a>


# Vyos Customization


<img src="https://raw.githubusercontent.com/hauke-cloud/.github/main/resources/img/organisation-logo-small.png" alt="hauke.cloud logo" width="109" height="123" align="right">


<llm header>

A Debian package that ships a default VyOS boot configuration and a non-interactive bash installer for writing a VyOS system image from the live medium to a target disk. It is for you if you build custom VyOS ISOs and need a repeatable image install with GRUB boot menus for normal boot, password reset, and recovery.

</llm>


## :book: Description

<llm description>

`vyos-customization` is a Debian package (architecture `all`) that provides a repeatable, non-interactive way to install a VyOS system image from a running live medium onto a target disk. It is intended for operators who build custom VyOS ISOs or images (for example via Packer or the vyos-build/live-build process) and need a consistent default configuration and GRUB boot menu on every installed system.

The package ships a default `config.boot` file and a bash script, `install-image`, that partitions the target disk (GPT with BIOS-boot, EFI, and ext4 root), copies the kernel and live squashfs, writes the configuration with a SHA-512 password hash, and generates a full GRUB setup. CI builds the `.deb` and publishes it as a GitHub Release artifact when a `v*` tag is pushed.

- Default VyOS boot configuration (hostname, admin user, NTP, serial console, SSH, DHCP on `eth0`)
- Non-interactive disk installer with GPT layout and GRUB for i386-pc, x86_64-efi, and arm64-efi
- GRUB boot-mode menu (Normal, Password reset, System recovery) and console-type menu (tty / serial)
- Configurable via environment variables: `IMAGE_NAME`, `DISK`, `PASSWORD`, `CONSOLE_TYPE`

The package is maintained by Hauke Mettendorf and lives in the `hauke-cloud` GitHub organisation.

</llm>


## 🚀 Getting started

<llm getting_started hint="Assume nothing about the ecosystem beyond what the analysis names. If the repository has no build step, say what a reader does with it instead.">

1. Clone the repository.

```bash
git clone https://github.com/hauke-cloud/vyos-customization.git
cd vyos-customization
```

2. Install the Debian packaging build dependencies.

```bash
sudo apt-get install -y dpkg-dev debhelper
```

3. Build the `.deb` package; the output file appears in the parent directory.

```bash
dpkg-buildpackage -us -uc -b
```

The resulting `vyos-customization_1.0.0-1_all.deb` installs a default VyOS boot configuration and the `install-image` script. You run that script from a VyOS live system to partition a target disk, copy the live image, generate a GRUB boot menu, and install GRUB for the detected firmware.

</llm>


## :airplane: Usage

<llm usage>

Once the `vyos-customization` package is installed on a VyOS live system, the primary task is running the image installer. It is configured entirely through environment variables; there are no CLI flags.

**Install a VyOS image to a disk**

From a running VyOS live system (the script exits if the live squashfs is absent), set the variables you need and invoke the installer:

```bash
IMAGE_NAME="VyOS-1.5" DISK="/dev/sda" PASSWORD="s3cret" CONSOLE_TYPE="ttyS" \
  /usr/local/bin/install-image
```

`CONSOLE_TYPE` is `tty` for a graphical or KVM console, or `ttyS` for serial at 115200 baud. The script partitions the target disk (GPT with a BIOS-boot partition, a 256 MiB EFI partition, and an ext4 root labelled `persistence`), copies the kernel and live squashfs, writes the default config with a SHA-512 hash of `PASSWORD`, generates a GRUB menu (Normal / Password reset / System recovery), and installs GRUB for i386-pc and x86_64-efi.

**Build the .deb locally**

```bash
sudo apt-get install -y dpkg-dev debhelper
dpkg-buildpackage -us -uc -b
```

The resulting `.deb` appears in the parent directory.

**Cut a new release**

Bump the version in `debian/changelog`, then push a tag matching `v*` to trigger the GitHub Actions workflow, which builds the package and publishes it as a GitHub Release artifact:

```bash
dch -v 1.0.1-1 "New release message"
git add debian/changelog
git commit -m "Bump to 1.0.1-1"
git tag v1.0.1-1
git push --tags
```

</llm>


## 📄 License

This Project is licensed under the GNU General Public License v3.0

- see the [LICENSE](LICENSE) file for details.


## :coffee: Contributing

To become a contributor, please check out the [CONTRIBUTING](CONTRIBUTING.md) file.


## :email: Contact

For any inquiries or support requests, please open an issue in this
repository or contact us at [contact@hauke.cloud](mailto:contact@hauke.cloud).
