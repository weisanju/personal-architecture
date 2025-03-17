#!/bin/bash

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# 创建日志目录
mkdir -p /var/log/openvpn3
install_log="/var/log/openvpn3/gdbuspp_install.log"

echo "开始安装 GDBus++" | tee -a $install_log

# 安装依赖
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu 系统
    apt-get update
    apt-get install -y build-essential git pkg-config meson \
        libglib2.0-dev
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS/Fedora 系统
    yum install -y gcc-c++ git meson pkgconfig glib2-devel
fi

# 克隆源码
cd /tmp
if [ -d "gdbuspp" ]; then
    rm -rf gdbuspp
fi
git clone https://github.com/OpenVPN/gdbuspp
cd gdbuspp

# 构建安装
meson setup --prefix=/usr _builddir
cd _builddir
meson compile
meson test
meson install

# 更新动态链接库缓存
ldconfig

echo "GDBus++ 安装完成" | tee -a $install_log

# 验证安装
if [ -f "/usr/include/gdbuspp/connection.hpp" ]; then
    echo "验证：GDBus++ 头文件安装成功" | tee -a $install_log
else
    echo "错误：GDBus++ 头文件安装失败" | tee -a $install_log
    exit 1
fi 