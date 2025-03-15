# xxHash Archive

This directory contains the xxHash library archive downloaded from GitHub.

- **Source**: https://github.com/Cyan4973/xxHash
- **File**: xxhash-0.8.1.tar.gz
- **Version**: v0.8.1

This archive is used by the OpenVPN3 Ansible role to build and install xxHash, which is a dependency for OpenVPN3.

## Updating the Archive

To update this archive with a newer version, run:

```bash
curl -L https://github.com/Cyan4973/xxHash/archive/refs/tags/vX.Y.Z.tar.gz -o xxhash-X.Y.Z.tar.gz
```

Replace X.Y.Z with the desired version number.

Then update the Ansible task in `ansible/roles/openvpn3/tasks/main.yml` to use the new file name if necessary. 