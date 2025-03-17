from fabric import Connection
from invoke import UnexpectedExit
from enum import Enum
from typing import Dict


class PackageManager(Enum):
    """包管理器类型枚举"""
    APT = "apt"
    YUM = "yum"
    DNF = "dnf"
    UNKNOWN = "unknown"


class PackageManagerCommands:
    """包管理器命令映射"""
    COMMANDS: Dict[PackageManager, Dict[str, str]] = {
        PackageManager.APT: {
            "install": "apt-get install -y",
            "remove": "apt-get remove -y",
            "update": "apt-get update",
            "check": "dpkg -l"
        },
        PackageManager.YUM: {
            "install": "yum install -y",
            "remove": "yum remove -y",
            "update": "yum update -y",
            "check": "rpm -q"
        },
        PackageManager.DNF: {
            "install": "dnf install -y",
            "remove": "dnf remove -y",
            "update": "dnf update -y",
            "check": "rpm -q"
        }
    }

    @classmethod
    def get_command(cls, pkg_manager: PackageManager, action: str) -> str:
        """
        获取特定包管理器的命令
        
        Args:
            pkg_manager: 包管理器类型
            action: 操作类型 (install/remove/update/check)
        
        Returns:
            str: 对应的命令
        """
        return cls.COMMANDS.get(pkg_manager, {}).get(action, "")


class PackageManagerDetector:
    """包管理器检测器"""

    @staticmethod
    def detect(conn: Connection) -> PackageManager:
        """
        检测远程系统使用的包管理器类型
        
        Args:
            conn: Fabric连接对象
        
        Returns:
            PackageManager: 包管理器类型
        """
        try:
            result = conn.run(
                "if command -v dnf >/dev/null 2>&1; then "
                "   echo 'dnf';"
                "elif command -v yum >/dev/null 2>&1; then "
                "   echo 'yum';"
                "elif command -v apt >/dev/null 2>&1; then "
                "   echo 'apt';"
                "else "
                "   echo 'unknown';"
                "fi",
                hide=True
            )

            pkg_manager = result.stdout.strip()
            if pkg_manager == 'dnf':
                return PackageManager.DNF
            elif pkg_manager == 'yum':
                return PackageManager.YUM
            elif pkg_manager == 'apt':
                return PackageManager.APT
            else:
                return PackageManager.UNKNOWN
        except UnexpectedExit:
            return PackageManager.UNKNOWN


class PackageManagerOperator:
    """包管理器操作类"""

    def __init__(self, conn: Connection):
        self.conn = conn
        self.pkg_manager = PackageManagerDetector.detect(conn)
        if self.pkg_manager == PackageManager.UNKNOWN:
            raise RuntimeError("Unable to detect package manager")

    def install(self, package_name: str, use_sudo: bool = False) -> bool:
        """
        安装软件包
        
        Args:
            package_name: 要安装的包名
            use_sudo: 是否使用sudo权限
        
        Returns:
            bool: 安装是否成功
        """
        try:
            install_cmd = f"{PackageManagerCommands.get_command(self.pkg_manager, 'install')} {package_name}"
            if use_sudo:
                self.conn.sudo(install_cmd)
            else:
                self.conn.run(install_cmd)
            return True
        except UnexpectedExit:
            return False

    def uninstall(self, package_name: str, use_sudo: bool = False) -> bool:
        """
        卸载软件包
        
        Args:
            package_name: 要卸载的包名
            use_sudo: 是否使用sudo权限
        
        Returns:
            bool: 卸载是否成功
        """
        try:
            remove_cmd = f"{PackageManagerCommands.get_command(self.pkg_manager, 'remove')} {package_name}"
            if use_sudo:
                self.conn.sudo(remove_cmd)
            else:
                self.conn.run(remove_cmd)
            return True
        except UnexpectedExit:
            return False

    def is_installed(self, package_name: str) -> bool:
        """
        检查软件包是否已安装
        
        Args:
            package_name: 包名
        
        Returns:
            bool: 是否已安装
        """
        try:
            check_cmd = f"{PackageManagerCommands.get_command(self.pkg_manager, 'check')} {package_name}"
            self.conn.run(check_cmd, hide=True)
            return True
        except UnexpectedExit:
            return False

    def update(self, use_sudo: bool = False) -> bool:
        """
        更新包列表
        
        Args:
            use_sudo: 是否使用sudo权限
        
        Returns:
            bool: 更新是否成功
        """
        try:
            update_cmd = PackageManagerCommands.get_command(self.pkg_manager, 'update')
            if use_sudo:
                self.conn.sudo(update_cmd)
            else:
                self.conn.run(update_cmd)
            return True
        except UnexpectedExit:
            return False
