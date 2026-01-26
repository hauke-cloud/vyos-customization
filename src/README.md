# Source Files for VyOS Customization Package

This directory contains the source files that will be packaged and installed on VyOS systems.

## Directory Structure

```
src/
├── config/
│   └── config.boot.default      # Default VyOS configuration
└── scripts/
    ├── postinst                 # Post-installation hook
    ├── auto-install.sh          # Automated installation script
    └── generate-password.sh     # Password generation helper
```

## Files Description

### config/config.boot.default
Default VyOS configuration applied to new installations.
- **Installed to**: `/opt/vyatta/etc/config.boot.default`
- **Purpose**: Provides a base configuration for VyOS systems
- **Contains**: Hostname, networking, SSH, NTP, logging configuration

### scripts/postinst
Post-installation hook that runs after VyOS is installed to disk.
- **Installed to**: `/opt/vyatta/etc/install-image/postinst`
- **Purpose**: Handles persistence configuration and system setup
- **Runs**: During VyOS image installation process

### scripts/auto-install.sh
Automated non-interactive installation script for Packer builds.
- **Installed to**: `/usr/local/bin/vyos-auto-install`
- **Purpose**: Enables automated VyOS installation in CI/CD pipelines
- **Usage**: Called by Packer to install VyOS to disk

### scripts/generate-password.sh
Helper script for generating encrypted passwords for VyOS users.
- **Installed to**: `/usr/local/bin/generate-password.sh`
- **Purpose**: Generate password hashes for VyOS configuration
- **Usage**: `generate-password.sh` (interactive)

## Modifying Files

To update the customizations:

1. Edit files in this directory
2. Update `debian/changelog` with version bump
3. Commit and push changes
4. GitHub Actions will build and publish the new package
5. Next ISO build will use the updated package

## Adding New Files

To add new customization files:

1. Add file to appropriate subdirectory
2. Add entry to `debian/install` mapping file to installation path
3. Update `debian/changelog`
4. If the file needs to be executable, update `debian/rules`
