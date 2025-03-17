#!/bin/bash

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# 创建日志目录
mkdir -p /var/log/openvpn3
install_log="/var/log/openvpn3/install.log"

echo "开始安装 OpenVPN3 Linux client..." | tee -a $install_log

# 首先安装 GDBus++
# ./build_gdbuspp.sh
# if [ $? -ne 0 ]; then
#     echo "GDBus++ 安装失败，终止安装" | tee -a $install_log
#     exit 1
# fi

# 添加 openvpn 用户和组
if ! getent group openvpn >/dev/null; then
    groupadd -r openvpn
    echo "创建 openvpn 组" | tee -a $install_log
fi

if ! getent passwd openvpn >/dev/null; then
    useradd -r -s /sbin/nologin -g openvpn openvpn
    echo "创建 openvpn 用户" | tee -a $install_log
fi

# 安装依赖包
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu 系统
    apt-get update
    apt-get install -y build-essential git pkg-config libglib2.0-dev \
        libjsoncpp-dev uuid-dev liblz4-dev libcap-ng-dev \
        libxml2-utils python3-minimal python3-dbus \
        python3-docutils python3-jinja2 libxml2-utils \
        libtinyxml2-dev policykit-1 libsystemd-dev \
        python3-systemd libssl-dev libssl1.1 libgdbuspp-dev  libnl-3-dev libnl-genl-3-dev protobuf-compiler libprotobuf-dev
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS/Fedora 系统
    yum install -y gcc-c++ git meson pkgconfig glib2-devel jsoncpp-devel \
        libuuid-devel libcap-ng-devel selinux-policy-devel \
        lz4-devel zlib-devel libxml2 tinyxml2-devel python3-dbus \
        python3-gobject python3-pyOpenSSL python3-jinja2 \
        python3-docutils bzip2 polkit systemd-devel \
        python3-systemd openssl-devel libnl3-devel.x86_64 libnl3.x86_64 protobuf.x86_64 protobuf-compiler.x86_64 
fi

# 克隆源码
cd /tmp
if [ -d "openvpn3-linux" ]; then
    rm -rf openvpn3-linux
fi
git clone https://github.com/OpenVPN/openvpn3-linux
cd openvpn3-linux

# 构建安装
./bootstrap.sh
meson setup --prefix=/usr _builddir
meson compile -C _builddir
meson install -C _builddir

# 初始化配置
openvpn3-admin init-config --write-configs

# 重新加载 D-Bus 配置
systemctl reload dbus

echo "OpenVPN3 Linux client 安装完成" | tee -a $install_log

# 验证安装
if command -v openvpn3 >/dev/null; then
    echo "验证：openvpn3 命令已安装成功" | tee -a $install_log
    openvpn3 version | tee -a $install_log
else
    echo "错误：openvpn3 命令安装失败" | tee -a $install_log
    exit 1
fi 