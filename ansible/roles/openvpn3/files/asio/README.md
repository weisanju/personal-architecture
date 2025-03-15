# ASIO Archive

This directory contains the ASIO library archive downloaded from GitHub.

- **Source**: https://github.com/chriskohlhoff/asio
- **File**: asio-1-24-0.tar.gz
- **Version**: asio-1-24-0

This archive is used by the OpenVPN3 Ansible role to build and install OpenVPN3, which requires the ASIO library.

## Updating the Archive

To update this archive with a newer version, run:

```bash
curl -L https://github.com/chriskohlhoff/asio/archive/asio-X-Y-Z.tar.gz -o asio-X-Y-Z.tar.gz
```

Replace X-Y-Z with the desired version number.

Then update the Ansible task in `ansible/roles/openvpn3/tasks/main.yml` to use the new file name if necessary. 