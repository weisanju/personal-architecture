# OpenVPN3 Ansible Role

This role automates building and installing OpenVPN3 client from source using the Meson build system.

## Requirements

This role requires the following:

- Git installed on the managed nodes
- Meson build system
- Python 3 with required modules
- Development libraries for OpenVPN3 dependencies

## Role Structure

The role includes local copies of all required dependencies:

- `files/gdbuspp/` - Contains the gdbuspp library archive
- `files/xxhash/` - Contains the xxHash library archive
- `files/asio/` - Contains the ASIO library archive

## Role Variables

Available variables are listed below, along with default values:

```yaml
# Default OpenVPN3 build directory
build_dir: "/tmp/openvpn3-build"

# Version to checkout (can be a tag, branch or commit hash)
version: "master"

# Whether to clean the build directory before starting
clean_build: true

# Meson build options
meson_options:
  - "-Ddefault_library=both"
  - "-Ddco=disabled"
  - "-Dselinux=disabled"
  
# Enable DCO (Data Channel Offload) 
enable_dco: false

# Install configuration files
write_configs: true
```

## Example Playbooks

### Standard Build

```yaml
- hosts: servers
  roles:
    - role: openvpn3
      version: "master"
```

### Build with DCO support enabled

```yaml
- hosts: servers
  roles:
    - role: openvpn3
      enable_dco: true
```

## Command line usage

You can customize the build by passing these variables:

```bash
ansible-playbook ansible/build_openvpn3.yml -e "target_hosts=aliyun" -e "version=master" -e "enable_dco=true"
```

Available command line options:
- `target_hosts`: Target host(s) to build on (default: aliyun)
- `version`: Git tag, branch, or commit to build (default: master)
- `clean_build`: Whether to clean the build directory first (default: true)
- `build_dir`: Directory to build in (default: /tmp/openvpn3-build)
- `git_repo`: Git repository URL
- `enable_dco`: Enable Data Channel Offload support (default: false)
- `write_configs`: Install OpenVPN3 configuration files (default: true)

## Implementation Details

This role:

1. Uses local copies of all dependencies (gdbuspp, xxHash, ASIO) to avoid network dependencies
2. Builds and installs gdbuspp with Meson
3. Builds and installs xxHash
4. Clones the OpenVPN3 repository
5. Configures and builds OpenVPN3 with CMake
6. Installs the OpenVPN3 CLI and headers
7. Configures and starts the OpenVPN3 services

## Notes

Based on [OpenVPN3 Linux build documentation](https://github.com/OpenVPN/openvpn3-linux/blob/master/BUILD.md)

## License

MIT 