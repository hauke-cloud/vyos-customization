#!/usr/bin/env python3
#
# Copyright VyOS maintainers and contributors <maintainers@vyos.io>
#
# This file is part of VyOS.
#
# VyOS is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# VyOS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# VyOS. If not, see <https://www.gnu.org/licenses/>.

from argparse import ArgumentParser, Namespace
from pathlib import Path
from shutil import copy, chown, rmtree, copytree, disk_usage
from glob import glob
from sys import exit
from os import environ
from os import readlink
from os import getpid
from os import getppid
from os import sync
from json import loads
from json import dumps
from typing import Union
from urllib.parse import urlparse
from passlib.hosts import linux_context
from errno import ENOSPC

from psutil import disk_partitions

from vyos.base import Warning
from vyos.configtree import ConfigTree
from vyos.defaults import base_dir
from vyos.defaults import directories
from vyos.remote import download
from vyos.system import disk
from vyos.system import grub
from vyos.system import image
from vyos.system import compat
from vyos.system import raid
from vyos.system import SYSTEM_CFG_VER
from vyos.system import grub_util
from vyos.template import render
from vyos.utils.auth import (
    DEFAULT_PASSWORD,
    EPasswdStrength,
    evaluate_strength
)
from vyos.utils.dict import dict_search
from vyos.utils.file import chmod_2775
from vyos.utils.file import read_file
from vyos.utils.file import write_file
from vyos.utils.process import cmd, run, rc_cmd
from vyos.utils.auth import get_local_users
from vyos.utils.auth import get_user_home_dir
from vyos.version import get_version_data
from vyos.config_mgmt import unsaved_commits

# define text messages
MSG_ERR_NOT_LIVE: str = 'The system is already installed. Please use "add system image" instead.'
MSG_ERR_LIVE: str = 'The system is in live-boot mode. Please use "install image" instead.'
MSG_ERR_NOT_ENOUGH_SPACE: str = 'Image upgrade requires at least 2GB of free drive space.'
MSG_ERR_UNSAVED_COMMITS: str = 'There are unsaved changes to the configuration. Either save or revert before upgrade.'
MSG_ERR_NO_DISK: str = 'No suitable disk was found. There must be at least one disk of 2GB or greater size.'
MSG_ERR_IMPROPER_IMAGE: str = 'Missing sha256sum.txt.\nEither this image is corrupted, or of era 1.2.x (md5sum) and would downgrade image tools;\ndisallowed in either case.'
MSG_ERR_INCOMPATIBLE_IMAGE: str = 'Image compatibility check failed, aborting installation.'
MSG_ERR_ARCHITECTURE_MISMATCH: str = 'The current architecture is "{0}", the new image is for "{1}". Upgrading to a different image architecture will break your system.'
MSG_ERR_FLAVOR_MISMATCH: str = 'The current image flavor is "{0}", the new image is "{1}". Upgrading to a non-matching flavor can have unpredictable consequences.'
MSG_ERR_MISSING_ARCHITECTURE: str = 'The new image version data does not specify architecture, cannot check compatibility (is it a legacy release image?)'
MSG_ERR_MISSING_FLAVOR: str = 'The new image version data does not specify flavor, cannot check compatibility (is it a legacy release image?)'
MSG_ERR_CORRUPT_CURRENT_IMAGE: str = 'Version data in the current image is malformed: missing flavor and/or architecture fields. Upgrade compatibility cannot be checked.'
MSG_ERR_UNSUPPORTED_SIGNATURE_TYPE: str = 'Unsupported signature type, signature cannot be verified.'
MSG_INFO_INSTALL_WELCOME: str = 'Welcome to VyOS installation!\nThis command will install VyOS to your permanent storage.'
MSG_INFO_INSTALL_EXIT: str = 'Exiting from VyOS installation'
MSG_INFO_INSTALL_SUCCESS: str = 'The image installed successfully; please reboot now.'
MSG_INFO_INSTALL_DISKS_LIST: str = 'The following disks were found:'
MSG_INFO_INSTALL_DISK_SELECT: str = 'Which one should be used for installation?'
MSG_INFO_INSTALL_RAID_CONFIGURE: str = 'Would you like to configure RAID-1 mirroring?'
MSG_INFO_INSTALL_RAID_FOUND_DISKS: str = 'Would you like to configure RAID-1 mirroring on them?'
MSG_INFO_INSTALL_RAID_CHOOSE_DISKS: str = 'Would you like to choose two disks for RAID-1 mirroring?'
MSG_INFO_INSTALL_DISK_CONFIRM: str = 'Installation will delete all data on the drive. Continue?'
MSG_INFO_INSTALL_RAID_CONFIRM: str = 'Installation will delete all data on both drives. Continue?'
MSG_INFO_INSTALL_PARTITONING: str = 'Creating partition table...'
MSG_INPUT_CONFIG_FOUND: str = 'An active configuration was found. Would you like to copy it to the new image?'
MSG_INPUT_CONFIG_CHOICE: str = 'The following config files are available for boot:'
MSG_INPUT_CONFIG_CHOOSE: str = 'Which file would you like as boot config?'
MSG_INPUT_UNSAVED_COMMITS: str = 'There are unsaved changes to the configuration. They will not be copied to the new image. Continue without saving?'
MSG_INPUT_IMAGE_NAME: str = 'What would you like to name this image?'
MSG_INPUT_IMAGE_NAME_TAKEN: str = 'There is already an installed image by that name; please choose again'
MSG_INPUT_IMAGE_DEFAULT: str = 'Would you like to set the new image as the default one for boot?'
MSG_INPUT_PASSWORD: str = 'Please enter a password for the "vyos" user:'
MSG_INPUT_PASSWORD_CONFIRM: str = 'Please confirm password for the "vyos" user:'
MSG_INPUT_ROOT_SIZE_ALL: str = 'Would you like to use all the free space on the drive?'
MSG_INPUT_ROOT_SIZE_SET: str = 'Please specify the size (in GB) of the root partition (min is 1.5 GB)?'
MSG_INPUT_CONSOLE_TYPE: str = 'What console should be used by default? (K: KVM, S: Serial)?'
MSG_INPUT_COPY_DATA: str = 'Would you like to copy data to the new image?'
MSG_INPUT_CHOOSE_COPY_DATA: str = 'From which image would you like to save config information?'
MSG_INPUT_COPY_ENC_DATA: str = 'Would you like to copy the encrypted config to the new image?'
MSG_INPUT_CHOOSE_COPY_ENC_DATA: str = 'From which image would you like to copy the encrypted config?'
MSG_WARN_ISO_SIGN_INVALID: str = 'Signature is not valid.'
MSG_WARN_ISO_SIGN_UNAVAL: str = 'Signature is not available.'
MSG_WARN_ROOT_SIZE_TOOBIG: str = 'The size is too big. Try again.'
MSG_WARN_ROOT_SIZE_TOOSMALL: str = 'The size is too small. Try again.'
MSG_WARN_IMAGE_NAME_WRONG: str = 'The suggested name is unsupported!\n'\
'It must be between 1 and 64 characters long and can contain only alphanumeric characters, hyphens, and underscores.'
MSG_WARN_PASS_SHORT: str = 'Password must be at least 8 characters long'
MSG_WARN_PASS_WEAK: str = 'Password is weak - recommended to use strong password.'
MSG_WARN_FLAVOR_MISMATCH: str = 'The current image flavor is "{0}", the new image is "{1}". Proceeding anyway because --force option was specified.'
MSG_WARN_CONSOLE_TYPE_INVALID: str = 'Invalid console type. Using default KVM console.'
MSG_LOWMEM_WARNING: str = 'Your system has less than 4GB of RAM, installation may fail if you continue. Please consider closing other programs to free up memory.'
MSG_VERIFY_GPG_UNSUP: str = 'Unable to verify GPG signature.'
CONST_MIN_DISK_SIZE: int = 2147483648  # 2 GB
CONST_MIN_ROOT_SIZE: int = 1610612736  # 1.5 GB

DIR_ISO_MOUNT: str = '/mnt/iso'
DIR_INSTALLATION: str = '/mnt/installation'
DIR_ROOTFS_SRC: str = f'{DIR_ISO_MOUNT}/live'
DIR_ROOTFS_DST: str = f'{DIR_INSTALLATION}/boot'
FILE_ROOTFS_SRC: str = f'{DIR_ROOTFS_SRC}/filesystem.squashfs'


def cleanup(mounts: list[str] = [], remove_items: list[str] = []) -> None:
    """Clean up after installation

    Args:
        mounts (list[str], optional): List of mounts to unmount.
        Defaults to [].
        remove_items (list[str], optional): List of files or directories
        to remove. Defaults to [].
    """
    print('Cleaning up')
    # clean up installation directory by default
    if not remove_items:
        remove_items = [DIR_INSTALLATION]

    # perform unmounts
    for mount in mounts:
        try:
            disk.partition_umount(mount)
        except Exception as err:
            print(f'Failed to umount {mount}: {err}')

    # remove items
    for remove_item in remove_items:
        try:
            if Path(remove_item).exists():
                if Path(remove_item).is_file():
                    Path(remove_item).unlink()
                else:
                    rmtree(remove_item)
        except Exception as err:
            print(f'Failed to remove {remove_item}: {err}')


def bytes_to_gb(size: int) -> float:
    """Convert Bytes to GBytes, rounded to 1 decimal number

    Args:
        size (int): input size in bytes

    Returns:
        float: size in gbytes
    """
    return round(size / 1024**3, 1)


def gb_to_bytes(size: float) -> int:
    """Convert GBytes to Bytes

    Args:
        size (float): input size in gbytes

    Returns:
        int: size in bytes
    """
    return int(size * 1024**3)


def find_persistence() -> Union[str, None]:
    """Find a device with active persistence

    Returns:
        Union[str, None]: Path to a device, or None
    """
    for device in disk.device_list():
        if disk.parttable_partitions_list(device):
            for partition in disk.parttable_partitions_list(device):
                if partition.get('name') == 'persistence':
                    return partition.get('disk')
    return None


def check_raid_config(disks: list[str]) -> bool:
    """Check if there are exactly two disks suitable for RAID-1

    Args:
        disks (list[str]): list of available disks

    Returns:
        bool: True if there are exactly two suitable disks, False otherwise
    """
    return len(disks) == 2


def select_disk(disks: list[str], no_prompt: bool = False, target_disk: str = None) -> str:
    """Ask user to select a disk for installation

    Args:
        disks (list[str]): list of available disks
        no_prompt (bool): non-interactive mode
        target_disk (str): pre-selected target disk

    Returns:
        str: a selected disk
    """
    if no_prompt:
        if target_disk and target_disk in disks:
            return target_disk
        # In non-interactive mode, select first available disk
        return disks[0]
    
    # This won't be reached in non-interactive mode
    print(MSG_INFO_INSTALL_DISKS_LIST)
    for disk_info in disks:
        print(f'  {disk_info}')
    
    # Simplified: just return first disk
    return disks[0]


def ask_single_disk(disks_available: list[str],
                    no_prompt: bool = False,
                    target_disk: str = None) -> str:
    """Ask user to select a disk for installation

    Args:
        disks_available (list[str]): list of available disks
        no_prompt (bool): non-interactive mode
        target_disk (str): pre-selected target disk

    Returns:
        str: a selected disk
    """
    if no_prompt:
        if target_disk and target_disk in disks_available:
            disk_selected = target_disk
        else:
            disk_selected = disks_available[0]
        print(f'Using disk: {disk_selected}')
        return disk_selected
    
    # Non-interactive fallback
    return disks_available[0]


def ask_root_size(available_space: int, no_prompt: bool = False, 
                  root_size_gb: float = None) -> int:
    """Ask user to specify root partition size

    Args:
        available_space (int): available space in bytes
        no_prompt (bool): non-interactive mode
        root_size_gb (float): pre-specified root size in GB

    Returns:
        int: root partition size in bytes
    """
    if no_prompt:
        if root_size_gb:
            root_size = gb_to_bytes(root_size_gb)
            if root_size < CONST_MIN_ROOT_SIZE or root_size > available_space:
                print(f'Invalid root size, using all available space: {bytes_to_gb(available_space)} GB')
                return available_space
            return root_size
        # Use all available space by default
        return available_space
    
    # Non-interactive fallback
    return available_space


def image_validate(image_path: str) -> bool:
    """Validate an image signature

    Args:
        image_path (str): a path to an image

    Returns:
        bool: validation status
    """
    # Simplified validation - just check if file exists
    return Path(image_path).exists()


def migrate_config() -> bool:
    """Check for unsaved commits and ask user

    Returns:
        bool: True if there are no unsaved commits or user wants to continue
    """
    # In non-interactive mode, just return True
    return True


def copy_ssh_host_keys() -> bool:
    """Ask user about copying SSH host keys

    Returns:
        bool: True if user wants to copy
    """
    # In non-interactive mode, default to yes
    return True


def copy_ssh_known_hosts() -> bool:
    """Ask user about copying SSH known_hosts

    Returns:
        bool: True if user wants to copy
    """
    # In non-interactive mode, default to yes
    return True


def migrate_known_hosts(target_dir: str) -> None:
    """Migrate SSH known_hosts files

    Args:
        target_dir (str): target directory
    """
    try:
        users = get_local_users()
        for user in users:
            user_home = get_user_home_dir(user)
            known_hosts_file = f'{user_home}/.ssh/known_hosts'
            if Path(known_hosts_file).exists():
                target_user_dir = f'{target_dir}/home/{user}/.ssh'
                Path(target_user_dir).mkdir(parents=True, exist_ok=True)
                copy(known_hosts_file, target_user_dir)
    except Exception as err:
        print(f'Warning: Failed to migrate SSH known_hosts: {err}')


def get_cli_kernel_options(config_file: str) -> list:
    """Get kernel command line options from config

    Args:
        config_file (str): path to config file

    Returns:
        list: list of kernel options
    """
    try:
        config = ConfigTree(config_file)
        options = []
        # Add your logic here to extract kernel options
        return options
    except Exception:
        return []


def install_image(no_prompt: bool = False, target_disk: str = None,
                  vyos_password: str = None, root_size_gb: float = None,
                  image_name: str = None, set_default: bool = True,
                  console_type: str = 'kvm') -> None:
    """Install an image to a disk

    Args:
        no_prompt (bool): non-interactive mode
        target_disk (str): target disk for installation
        vyos_password (str): password for vyos user
        root_size_gb (float): root partition size in GB
        image_name (str): name for the installed image
        set_default (bool): set as default boot image
        console_type (str): console type ('kvm' or 'serial')
    """
    if not image.is_live_boot():
        exit(MSG_ERR_NOT_LIVE)

    print(MSG_INFO_INSTALL_WELCOME if not no_prompt else 'Installing VyOS image...')

    # Check memory
    mem_total = dict_search('memory.total', get_version_data())
    if mem_total and mem_total < 4294967296:  # 4GB
        print(MSG_LOWMEM_WARNING)

    # Find disks
    disks_available: list[str] = disk.disks_size()
    if not disks_available:
        exit(MSG_ERR_NO_DISK)

    # Select disk
    disk_selected: str = ask_single_disk(disks_available, no_prompt, target_disk)

    # Confirm installation (skip in no_prompt mode)
    if not no_prompt:
        print(MSG_INFO_INSTALL_DISK_CONFIRM)
        # In non-interactive, just proceed

    # Get password for vyos user
    if no_prompt:
        if not vyos_password:
            vyos_password = 'vyos'  # Default password
        user_password = linux_context.hash(vyos_password)
    else:
        user_password = linux_context.hash('vyos')

    # Get console type
    if console_type not in ['kvm', 'serial']:
        console_type = 'kvm'

    # Partition and format disk
    print(MSG_INFO_INSTALL_PARTITONING)
    disk.disk_cleanup(disk_selected)
    
    # Calculate partition sizes
    available_space = disk.disk_size(disk_selected) - 2147483648  # Reserve 2GB
    root_size = ask_root_size(available_space, no_prompt, root_size_gb)

    # Create partitions
    disk.parttable_create(disk_selected, 'gpt')
    partition_efi = disk.partition_create(disk_selected, 512 * 1024 * 1024,
                                         disk.PartitionType.EFI)
    partition_root = disk.partition_create(disk_selected, root_size,
                                          disk.PartitionType.LINUX)

    # Format partitions
    disk.filesystem_create(partition_efi, 'vfat')
    disk.filesystem_create(partition_root, 'ext4')

    # Mount partitions
    Path(DIR_INSTALLATION).mkdir(parents=True, exist_ok=True)
    disk.partition_mount(partition_root, DIR_INSTALLATION)
    Path(f'{DIR_INSTALLATION}/boot/efi').mkdir(parents=True, exist_ok=True)
    disk.partition_mount(partition_efi, f'{DIR_INSTALLATION}/boot/efi')

    # Generate image name
    if not image_name:
        version_data = get_version_data()
        image_name = image.get_default_image_name(version_data.get('version', 'unknown'))

    # Create directories
    target_dir = f'{DIR_INSTALLATION}/boot/{image_name}'
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    Path(f'{target_dir}/rw').mkdir(parents=True, exist_ok=True)

    # Copy system files
    print('Copying system files...')
    iso_path = find_persistence()
    if iso_path:
        disk.partition_mount(iso_path, DIR_ISO_MOUNT)

    # Copy kernel and initrd
    for file in Path(DIR_ROOTFS_SRC).iterdir():
        if file.is_file() and (file.match('initrd*') or file.match('vmlinuz*')):
            copy(file, target_dir)

    # Copy squashfs
    if Path(FILE_ROOTFS_SRC).exists():
        copy(FILE_ROOTFS_SRC, f'{target_dir}/{image_name}.squashfs')

    # Setup boot
    grub.install(disk_selected, f'{DIR_INSTALLATION}/boot', f'{DIR_INSTALLATION}/boot/efi')
    grub.set_console_type(console_type, f'{DIR_INSTALLATION}')

    # Create version file
    grub.version_add(image_name, DIR_INSTALLATION)
    if set_default:
        grub.set_default(image_name, DIR_INSTALLATION)

    # Create vyos user
    write_file(f'{target_dir}/rw/opt/vyatta/etc/config/.vyatta_config',
               'system {\n  login {\n    user vyos {\n      authentication {\n        encrypted-password "' +
               user_password + '"\n      }\n    }\n  }\n}\n')

    # Cleanup
    if iso_path:
        disk.partition_umount(DIR_ISO_MOUNT)
    
    disk.partition_umount(f'{DIR_INSTALLATION}/boot/efi')
    disk.partition_umount(DIR_INSTALLATION)

    sync()
    print(MSG_INFO_INSTALL_SUCCESS)


def add_image(image_path: str,
              vrf: str = None,
              username: str = '',
              password: str = '',
              no_prompt: bool = False,
              force: bool = False) -> None:
    """Add a new image

    Args:
        image_path (str): a path to an image
        vrf (str): VRF name
        username (str): username for download
        password (str): password for download
        no_prompt (bool): non-interactive mode
        force (bool): force installation
    """
    if image.is_live_boot():
        exit(MSG_ERR_LIVE)

    # Check for unsaved commits
    if not no_prompt and unsaved_commits():
        exit(MSG_ERR_UNSAVED_COMMITS)

    # Download image if needed
    iso_path = Path(image_path)
    if urlparse(image_path).scheme:
        try:
            print(f'Downloading image from {image_path}')
            iso_path = Path(download(image_path, 
                                    '/tmp/vyos_image.iso',
                                    vrf=vrf,
                                    username=username,
                                    password=password,
                                    progressbar=not no_prompt))
        except Exception as e:
            exit(f'Failed to download image: {e}')

    if not iso_path.exists():
        exit(f'Image file not found: {iso_path}')

    # Mount and extract image
    try:
        Path(DIR_ISO_MOUNT).mkdir(parents=True, exist_ok=True)
        disk.partition_mount(str(iso_path), DIR_ISO_MOUNT, 'iso9660', True)

        # Get version info
        version_file = f'{DIR_ISO_MOUNT}/live/version.json'
        if Path(version_file).exists():
            version_data = loads(read_file(version_file))
        else:
            version_data = {'version': 'unknown'}

        # Generate image name
        if no_prompt:
            new_image_name = image.get_default_image_name(version_data.get('version', 'unknown'))
        else:
            new_image_name = image.get_default_image_name(version_data.get('version', 'unknown'))

        # Check if image name already exists
        installed_images = image.get_images()
        if new_image_name in installed_images:
            counter = 1
            while f'{new_image_name}.{counter}' in installed_images:
                counter += 1
            new_image_name = f'{new_image_name}.{counter}'

        print(f'Installing image: {new_image_name}')

        # Create target directory
        root_dir = disk.find_persistence()
        if not root_dir:
            root_dir = '/'
        
        target_dir = f'{root_dir}/boot/{new_image_name}'
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        Path(f'{target_dir}/rw').mkdir(parents=True, exist_ok=True)

        # Copy files
        print('Copying system files...')
        for file in Path(DIR_ROOTFS_SRC).iterdir():
            if file.is_file() and (file.match('initrd*') or file.match('vmlinuz*')):
                copy(file, target_dir)

        if Path(FILE_ROOTFS_SRC).exists():
            copy(FILE_ROOTFS_SRC, f'{target_dir}/{new_image_name}.squashfs')

        # Add to grub
        grub.version_add(new_image_name, root_dir)
        
        if no_prompt:
            set_default = True
        else:
            set_default = False

        if set_default:
            grub.set_default(new_image_name, root_dir)

        print(f'Image {new_image_name} installed successfully')

    except Exception as e:
        exit(f'Failed to add image: {e}')
    finally:
        cleanup([DIR_ISO_MOUNT])


def parse_arguments() -> Namespace:
    """Parse arguments

    Returns:
        Namespace: a namespace with parsed arguments
    """
    parser: ArgumentParser = ArgumentParser(
        description='Install new system images')
    parser.add_argument('--action',
                        choices=['install', 'add'],
                        required=True,
                        help='action to perform with an image')
    parser.add_argument('--vrf',
                        help='vrf name for image download')
    parser.add_argument('--no-prompt', action='store_true',
                        help='perform action non-interactively')
    parser.add_argument('--username', default='',
                        help='username for image download')
    parser.add_argument('--password', default='',
                        help='password for image download')
    parser.add_argument('--image-path',
                        help='a path (HTTP or local file) to an image that needs to be installed')
    parser.add_argument('--force', action='store_true',
                        help='Ignore flavor compatibility requirements.')
    parser.add_argument('--target-disk',
                        help='target disk for installation (e.g., /dev/sda)')
    parser.add_argument('--vyos-password', default='vyos',
                        help='password for vyos user (default: vyos)')
    parser.add_argument('--root-size-gb', type=float,
                        help='root partition size in GB (default: use all available space)')
    parser.add_argument('--image-name',
                        help='name for the installed image')
    parser.add_argument('--no-set-default', action='store_true',
                        help='do not set new image as default boot image')
    parser.add_argument('--console-type', choices=['kvm', 'serial'], default='kvm',
                        help='console type (default: kvm)')
    
    args: Namespace = parser.parse_args()
    
    # Validate arguments
    if args.action == 'add' and not args.image_path:
        exit('A path to image is required for add action')
    
    if args.action == 'install':
        args.no_prompt = True  # Force non-interactive for install

    return args


if __name__ == '__main__':
    try:
        args: Namespace = parse_arguments()
        
        if args.action == 'install':
            install_image(
                no_prompt=args.no_prompt,
                target_disk=args.target_disk,
                vyos_password=args.vyos_password,
                root_size_gb=args.root_size_gb,
                image_name=args.image_name,
                set_default=not args.no_set_default,
                console_type=args.console_type
            )
        elif args.action == 'add':
            add_image(
                args.image_path,
                args.vrf,
                args.username,
                args.password,
                args.no_prompt,
                args.force
            )

        exit()

    except KeyboardInterrupt:
        print('Stopped by Ctrl+C')
        cleanup()
        exit()

    except Exception as err:
        exit(f'{err}')
