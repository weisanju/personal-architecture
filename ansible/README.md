# Mihomo Party Ansible Deployment

This Ansible playbook automates the deployment of Mihomo Party across Linux, macOS, and Windows systems.

## Prerequisites

- Ansible 2.9 or higher installed on the control node
- For Windows targets:
  - WinRM configured on Windows hosts
  - `pywinrm` Python package installed on the control node
- SSH access to Linux/macOS targets
- Sudo/Administrator privileges on target systems

## Configuration

1. Edit the `inventory.yml` file to specify your target hosts:
   - Update IP addresses
   - Set correct usernames
   - Configure connection settings

2. Modify variables in `roles/mihomo-party/defaults/main.yml`:
   - Set desired version in `mihomo_version`
   - Adjust installation directory in `install_dir`
   - Modify user/group settings if needed

## Usage

1. Test connection to hosts:
```bash
ansible all -m ping -i inventory.yml
```

2. Run the playbook:
```bash
ansible-playbook -i inventory.yml mihomo-party.yml
```

## Features

- Automatic architecture detection
- OS-specific installation and service configuration
- Supports Linux (systemd), macOS (LaunchAgent), and Windows (Windows Service)
- Automatic service management

## Service Management

### Linux
- Start: `sudo systemctl start mihomo-party`
- Stop: `sudo systemctl stop mihomo-party`
- Status: `sudo systemctl status mihomo-party`

### macOS
- Start: `launchctl load ~/Library/LaunchAgents/com.mihomo.party.plist`
- Stop: `launchctl unload ~/Library/LaunchAgents/com.mihomo.party.plist`

### Windows
- Start: `Start-Service MihomoParty`
- Stop: `Stop-Service MihomoParty`
- Status: `Get-Service MihomoParty` 