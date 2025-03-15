# OpenVPN3 Archive

This directory contains the OpenVPN3 source code archive.

- **Source**: https://github.com/OpenVPN/openvpn3-linux
- **File**: openvpn3-master.zip
- **Version**: master

This archive can be used as an alternative to cloning the Git repository during the OpenVPN3 installation process.

## Updating the Archive

To update this archive with a newer version, you can download it directly from GitHub:

```bash
curl -L https://github.com/OpenVPN/openvpn3-linux/archive/refs/heads/master.zip -o openvpn3-master.zip
```

Or for a specific tag/version:

```bash
curl -L https://github.com/OpenVPN/openvpn3-linux/archive/refs/tags/vX.Y.Z.zip -o openvpn3-vX.Y.Z.zip
```

Replace X.Y.Z with the desired version number.

Then update the Ansible task in `ansible/roles/openvpn3/tasks/main.yml` to use the local archive instead of Git cloning. 