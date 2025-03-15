# Ansible Inventory 组织结构说明

## 1. 基本结构

Ansible inventory 可以使用 YAML 格式组织，基本结构如下：

```yaml
all:                    # 顶级组，包含所有主机
  children:             # 子组的集合
    group1:            # 自定义组
      hosts:           # 组内主机列表
        host1:         # 具体主机
          ansible_host: 192.168.1.1
```

## 2. 实际示例

### 2.1 按操作系统分组

```yaml
all:
  children:
    linux:
      hosts:
        duicloud:
          ansible_host: 192.168.2.2
          ansible_user: root
        aliyun:
          ansible_host: 192.168.2.3
          ansible_user: root
    
    macos:
      hosts:
        macos-host:
          ansible_host: 192.168.1.10
          ansible_user: admin
    
    windows:
      hosts:
        windows-host:
          ansible_host: 192.168.1.20
          ansible_user: administrator
          ansible_connection: winrm
          ansible_winrm_server_cert_validation: ignore
```

### 2.2 按环境和功能分组

```yaml
all:
  children:
    production:
      children:
        web_servers:
          hosts:
            web1:
              ansible_host: 192.168.1.101
            web2:
              ansible_host: 192.168.1.102
        db_servers:
          hosts:
            db1:
              ansible_host: 192.168.1.201
            db2:
              ansible_host: 192.168.1.202
    
    staging:
      children:
        web_servers:
          hosts:
            web-staging:
              ansible_host: 192.168.2.101
        db_servers:
          hosts:
            db-staging:
              ansible_host: 192.168.2.201
```

## 3. 常用主机变量

主机可以定义多个变量，常用的包括：

```yaml
host1:
  ansible_host: 192.168.1.1        # 主机 IP 或域名
  ansible_port: 22                 # SSH 端口
  ansible_user: root              # 登录用户
  ansible_password: secret        # 登录密码（建议使用 vault 加密）
  ansible_connection: ssh         # 连接方式（ssh/winrm/local）
  ansible_python_interpreter: /usr/bin/python3  # Python 解释器路径
```

## 4. 使用方法

### 4.1 命令行使用

```bash
# 针对特定组执行
ansible linux -m ping

# 针对特定主机执行
ansible duicloud -m ping

# 针对多个组执行
ansible 'linux,macos' -m ping
```

### 4.2 在 Playbook 中使用

```yaml
---
- name: Example Playbook
  hosts: linux          # 使用组名
  tasks:
    - name: Some task
      # ...

- name: Another Playbook
  hosts: duicloud      # 使用主机名
  tasks:
    - name: Some task
      # ...
```

## 5. 最佳实践

1. **命名规范**：
   - 使用有意义的名称
   - 保持命名一致性
   - 避免使用特殊字符

2. **组织结构**：
   - 按照合理的层级组织
   - 避免过深的嵌套
   - 保持结构清晰

3. **变量管理**：
   - 敏感信息使用 vault 加密
   - 合理使用组变量和主机变量
   - 避免重复定义变量

4. **文档维护**：
   - 添加必要的注释
   - 保持文档更新
   - 说明特殊配置的用途

## 6. 注意事项

1. YAML 格式要求严格，注意缩进
2. 主机名必须唯一
3. 变量名区分大小写
4. 密码等敏感信息建议加密
5. 定期检查和更新 inventory

## 7. 调试技巧

```bash
# 查看 inventory 中的所有主机
ansible-inventory --list

# 查看特定主机的所有变量
ansible-inventory --host duicloud

# 图形化显示 inventory 结构
ansible-inventory --graph
``` 