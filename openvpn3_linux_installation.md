# OpenVPN 3 Client for Linux - Installation and Usage Guide

This guide provides instructions for installing and using the OpenVPN 3 client on various Linux distributions.

## Supported Distributions

| Distribution | Release | Release Name | Architecture |
|--------------|---------|--------------|--------------|
| Debian | 11 | bullseye | amd64, arm64 |
| Debian | 12 | bookworm | amd64, arm64 |
| Fedora | - | - | Recent stable releases |
| Red Hat Enterprise Linux | 8 | - | aarch64, ppc64le, s390x, x86_64 |
| Red Hat Enterprise Linux | 9 | - | aarch64, ppc64le, s390x, x86_64 |
| Ubuntu | 20.04 | focal | amd64, arm64 |
| Ubuntu | 22.04 | jammy | amd64, arm64 |

## Installation

### For Debian and Ubuntu

1. Add the OpenVPN repository GPG key:
```bash
sudo apt install apt-transport-https
wget https://swupdate.openvpn.net/repos/openvpn-repo-pkg-key.pub
sudo apt-key add openvpn-repo-pkg-key.pub
```

2. Add the OpenVPN repository:
```bash
sudo wget -O /etc/apt/sources.list.d/openvpn3.list https://swupdate.openvpn.net/community/openvpn3/repos/openvpn3-$DISTRO.list
```
Replace `$DISTRO` with your distribution name (focal, jammy, bullseye, or bookworm).

3. Update and install:
```bash
sudo apt update
sudo apt install openvpn3
```

### For Fedora, Red Hat Enterprise Linux, AlmaLinux, or Rocky Linux

1. Add the OpenVPN repository:
```bash
sudo dnf config-manager --add-repo https://pkgs.openvpn.net/openvpn3/repos/repos-openvpn3-fedora.repo
```

2. Install the package:
```bash
sudo dnf install openvpn3-client
```

## Using OpenVPN 3 Client

### Importing and Starting a VPN Connection

1. Import a configuration profile:
```bash
openvpn3 config-import --config /path/to/profile.ovpn --name MyConnection --persistent
```
The `--persistent` flag ensures the profile is preserved after system reboot.

2. Start a VPN session:
```bash
openvpn3 session-start --config MyConnection
```

### Setting Up Auto-start on Boot

1. Import a connection profile:
```bash
openvpn3 config-import --config /path/to/profile.ovpn --name CloudConnexa --persistent
```

2. Grant root access to the profile:
```bash
openvpn3 config-acl --show --lock-down true --grant root --config CloudConnexa
```
Add `--transfer-owner-session true` to make the current user the "VPN session owner".

3. Enable and start the systemd service:
```bash
sudo systemctl enable --now openvpn3-session@CloudConnexa.service
```

### Common Commands

#### One-time Connection
```bash
openvpn3 session-start --config /path/to/profile.ovpn
```

#### List Available Profiles
```bash
openvpn3 configs-list
```

#### List Active Sessions
```bash
openvpn3 sessions-list
```

#### Manage Sessions
- Restart a connection:
```bash
openvpn3 session-manage --config MyConnection --restart
```

- Disconnect a session:
```bash
openvpn3 session-manage --config MyConnection --disconnect
```
or
```bash
openvpn3 session-manage --session-path /net/openvpn/v3/sessions/... --disconnect
```

#### View Statistics and Logs
- View session statistics:
```bash
openvpn3 session-stats --config MyConnection
```

- View real-time logs:
```bash
openvpn3 log --config MyConnection
```
Add `--log-level 6` for more verbose logging (levels range from 0 to 6).

### Changing an Auto-loading Profile (RHEL-7 only)

1. List active sessions:
```bash
sudo openvpn3 sessions-list
```

2. Disconnect the active session:
```bash
sudo openvpn3 session-manage --session-path YOUR_PATH --disconnect
```

3. Remove the existing configuration:
```bash
sudo openvpn3 config-remove --config "YOUR_CONFIG_NAME"
```

4. Edit the autoload profile:
```bash
sudo nano /etc/openvpn3/autoload/Connector.conf
```

5. Import the new configuration:
```bash
sudo openvpn3 config-import --config /etc/openvpn3/autoload/Connector.conf --name "YOUR_CONFIG_NAME"
```

6. Start the new session:
```bash
sudo openvpn3 session-start --config "YOUR_CONFIG_NAME"
```

7. Restart the computer to verify autostart works with the new profile. 



https://github.com/OpenVPN/openvpn3-linux/blob/master/BUILD.md