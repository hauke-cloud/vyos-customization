#!/bin/bash
# Helper script to generate encrypted passwords for VyOS config.boot.default
# Usage: ./generate-password.sh

if ! command -v mkpasswd &> /dev/null; then
    echo "Error: mkpasswd is not installed"
    echo "Install it with: sudo apt-get install whois"
    exit 1
fi

echo "Enter password to encrypt:"
read -s password
echo
echo "Confirm password:"
read -s password2
echo

if [ "$password" != "$password2" ]; then
    echo "Error: Passwords do not match"
    exit 1
fi

echo "Generating encrypted password..."
encrypted=$(echo "$password" | mkpasswd --method=sha-512 --rounds=656000 --stdin)

echo
echo "Encrypted password (copy this to config.boot.default):"
echo "$encrypted"
echo
echo "Example usage in config.boot.default:"
echo "system {"
echo "    login {"
echo "        user vyos {"
echo "            authentication {"
echo "                encrypted-password \"$encrypted\""
echo "            }"
echo "        }"
echo "    }"
echo "}"
