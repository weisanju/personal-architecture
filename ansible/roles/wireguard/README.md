# Ansible Role: WireGuard

这个 Ansible 角色用于自动部署和配置 WireGuard VPN，支持一个服务端多个客户端的场景。角色支持客户端的添加、更新和下线，以及服务端的更新。

## 要求

- Ansible 2.9 或更高版本
- 支持的操作系统:
  - Ubuntu 18.04 (Bionic), 20.04 (Focal), 22.04 (Jammy)
  - Debian 10 (Buster), 11 (Bullseye)
  - CentOS/RHEL 8, 9

## 角色变量

可用变量及其默认值如下（参见 `defaults/main.yml`）:

```yaml
# WireGuard 接口名称
wireguard_interface: wg0

# WireGuard 网络设置
wireguard_network: 10.8.0.0/24
wireguard_server_ip: 10.8.0.1
wireguard_port: 51820

# WireGuard 服务器公网 IP 或域名
# 这必须在清单文件中手动设置
wireguard_server_public_ip: ""

# 客户端使用的 DNS 服务器
wireguard_dns_servers:
  - 1.1.1.1
  - 8.8.8.8

# 客户端 IP 分配
# 这应该在 host_vars 中为每个客户端设置
wireguard_client_ip: 10.8.0.2

# 客户端允许的 IP (通过 VPN 路由的流量)
wireguard_client_allowed_ips: "0.0.0.0/0"

# 客户端状态 (active, absent)
# - active: 客户端配置并启用
# - absent: 移除客户端配置
wireguard_client_state: active

# 启用 NAT 使客户端可以通过服务器访问互联网
wireguard_enable_nat: true
```

## 必须配置的变量

在使用此角色之前，您必须在清单文件中设置以下变量：

- `wireguard_server_public_ip`: 服务器的公网 IP 地址或域名，客户端将使用此地址连接到服务器

## 工作原理

该角色会：

1. 在服务端生成 WireGuard 密钥对
2. 在每个客户端生成 WireGuard 密钥对
3. 收集所有客户端的公钥
4. 在服务端创建包含所有客户端公钥的配置文件
5. 在每个客户端创建连接到服务端的配置文件
6. 启用并启动 WireGuard 服务

## 客户端管理

### 添加新客户端

1. 在清单文件中添加新客户端到 `wireguard_clients` 组
2. 为新客户端设置唯一的 `wireguard_client_ip`
3. 运行 `update_clients.yml` playbook

```yaml
# 示例：添加新客户端
- hosts: new_client
  vars:
    wireguard_client_ip: 10.8.0.4
    wireguard_client_state: active
  roles:
    - wireguard
```

### 更新客户端

修改客户端的变量（如 IP 地址），然后运行 `update_clients.yml` playbook。

### 下线客户端

设置客户端的 `wireguard_client_state` 为 `absent`，然后运行 `update_clients.yml` playbook。

```yaml
# 示例：下线客户端
- hosts: client_to_remove
  vars:
    wireguard_client_state: absent
  roles:
    - wireguard
```

## 更新服务端

如果需要更新服务端配置（如端口、NAT 设置等），修改相关变量后运行 `update_server.yml` playbook。

## 示例清单

```yaml
all:
  children:
    wireguard_server:
      hosts:
        vpn-server:
          ansible_host: 203.0.113.1
      vars:
        wireguard_server_public_ip: "203.0.113.1"  # 服务器公网 IP 地址
    wireguard_clients:
      hosts:
        client1:
          ansible_host: 192.168.1.10
          wireguard_client_ip: 10.8.0.2
          wireguard_client_state: active
        client2:
          ansible_host: 192.168.1.11
          wireguard_client_ip: 10.8.0.3
          wireguard_client_state: active
        client3:
          ansible_host: 192.168.1.12
          wireguard_client_ip: 10.8.0.4
          wireguard_client_state: absent  # 这个客户端将被下线
```

## 示例 Playbook

### 初始部署

```yaml
---
- name: 部署 WireGuard VPN
  hosts: wireguard_server:wireguard_clients
  become: true
  roles:
    - wireguard
```

### 更新客户端

```yaml
---
- name: 更新 WireGuard 客户端
  hosts: wireguard_clients
  become: true
  roles:
    - wireguard

- name: 更新 WireGuard 服务端配置
  hosts: wireguard_server
  become: true
  roles:
    - wireguard
```

### 更新服务端

```yaml
---
- name: 更新 WireGuard 服务端
  hosts: wireguard_server
  become: true
  roles:
    - wireguard
```

## 许可证

MIT

## 作者信息

Your Name 