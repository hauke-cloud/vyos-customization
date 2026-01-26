# VyOS Customization Package

This repository contains a Debian package with custom configurations and scripts for VyOS.

## Package Structure

The package installs:
- Custom systemd services and timers (`/usr/lib/systemd/system/`)
- Helper scripts (`/usr/bin/` or `/usr/local/bin/`)
- Default VyOS configuration (`/opt/vyatta/etc/config.boot.default`)
- Post-installation hook (`/opt/vyatta/etc/install-image/postinst`)

## Building the Package

### Local Build

```bash
# Install build dependencies
sudo apt-get install -y dpkg-dev debhelper

# Build the package
dpkg-buildpackage -us -uc -b

# The .deb file will be created in the parent directory
```

### GitHub Actions Build

The package is automatically built and published to GitHub Pages on every push to main:
- DEB packages are stored in the APT repository at `https://<org>.github.io/vyos-customization/`
- GPG-signed for verification

## Using in VyOS ISO Build

Add the following to your VyOS ISO build process:

```bash
# Add custom APT repository
echo "deb [trusted=yes] https://hauke-cloud.github.io/vyos-customization/ ./" > \
  vyos-build/data/live-build-config/includes.chroot/etc/apt/sources.list.d/vyos-customization.list

# Install the package during build
echo "vyos-customization" >> vyos-build/data/live-build-config/package-lists/custom.list.chroot
```

## Package Contents

### VyOS Configuration
- `config.boot.default` - Default VyOS configuration for new installations
  - Located at: `/opt/vyatta/etc/config.boot.default`
  - Sets hostname, basic networking, SSH, NTP, etc.

### Installation Scripts
- `postinst` - Post-installation hook for VyOS image install
  - Located at: `/opt/vyatta/etc/install-image/postinst`
  - Runs after VyOS is installed to disk
  - Handles persistence configuration and upgrades

- `auto-install.sh` - Automated installation script for Packer builds
  - Located at: `/usr/local/bin/vyos-auto-install`
  - Non-interactive VyOS installation to /dev/sda
  - Used by Packer for automated ISO-based installs

### Helper Scripts
- `generate-password.sh` - Password generation helper
  - Located at: `/usr/local/bin/generate-password.sh`
  - Generates encrypted passwords for VyOS users

## Version Management

Version is defined in `debian/changelog`. Update it with:

```bash
dch -i  # Interactive changelog editor
# or
dch -v 1.0.1-1 "New release message"
```

## Development

1. Add your files to `src/` directory
2. Update `debian/install` to specify where files should be installed
3. Update `debian/changelog` with version and changes
4. Build and test the package locally
5. Push to GitHub - CI will build and publish automatically

## License

GNU General Public License v3.0
