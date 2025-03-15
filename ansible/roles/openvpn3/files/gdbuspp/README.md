# gdbuspp Repository Archive

This directory contains the gdbuspp repository archive downloaded from Codeberg.

- **Source**: https://codeberg.org/OpenVPN/gdbuspp.git
- **File**: gdbuspp-master.tar.gz
- **Version**: master branch

This archive is used by the OpenVPN3 Ansible role to build and install gdbuspp, which is a dependency for OpenVPN3.

## Updating the Archive

To update this archive with a newer version, run:

```bash
curl -L https://codeberg.org/OpenVPN/gdbuspp/archive/master.tar.gz -o gdbuspp-master.tar.gz
```

Or to download a specific version/tag:

```bash
curl -L https://codeberg.org/OpenVPN/gdbuspp/archive/TAG_NAME.tar.gz -o gdbuspp-TAG_NAME.tar.gz
```

Then update the Ansible task in `ansible/roles/openvpn3/tasks/main.yml` to use the new file name if necessary. 