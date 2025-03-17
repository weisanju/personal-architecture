import logging
import json
from pathlib import Path
from fabric import Connection
from invoke import UnexpectedExit
from enum import Enum
from typing import Dict, Optional, Union, Tuple, List, Any
from dataclasses import dataclass
import os
import tempfile
import requests
from urllib.parse import urlparse, unquote
from .common import extract_archive
from .package_manager import PackageManagerOperator
import jsonschema

logger = logging.getLogger(__name__)


class ServiceManager(Enum):
    """服务管理器类型枚举"""
    SYSTEMD = "systemd"
    SERVICE = "service"
    UNKNOWN = "unknown"


class ServiceSource(Enum):
    """服务源类型枚举"""
    LOCAL_FILE = "local_file"  # 本地文件 (file:// 或本地路径)
    HTTP = "http"  # HTTP(S)源
    FTP = "ftp"  # FTP源
    UNKNOWN = "unknown"  # 未知源类型

    @classmethod
    def detect_source_type(cls, source_path: str) -> "ServiceSource":
        """
        根据源路径判断源类型
        
        Args:
            source_path: 源路径（本地文件路径或URL）
            
        Returns:
            ServiceSource: 源类型
        """
        try:
            parsed = urlparse(source_path)
            if parsed.scheme in ['http', 'https']:
                return cls.HTTP
            elif parsed.scheme == 'ftp':
                return cls.FTP
            elif parsed.scheme == 'file' or not parsed.scheme:
                return cls.LOCAL_FILE
            else:
                return cls.UNKNOWN
        except Exception:
            # 如果解析失败，假定为本地文件
            return cls.LOCAL_FILE


@dataclass
class ServiceDefinition:
    """服务定义类"""
    name: str  # 服务名称
    description: str  # 服务描述
    exec_start: str  # 服务启动命令
    working_directory: str  # 工作目录
    user: str = "root"  # 运行用户
    after: str = "network.target"  # 服务依赖
    restart: str = "always"  # 重启策略
    restart_sec: int = 3  # 重启间隔

    def generate_systemd_unit(self) -> str:
        """生成systemd服务单元文件内容"""
        return f"""[Unit]
Description={self.description}
After={self.after}

[Service]
Type=simple
User={self.user}
ExecStart={self.exec_start}
WorkingDirectory={self.working_directory}
Restart={self.restart}
RestartSec={self.restart_sec}

[Install]
WantedBy=multi-user.target
"""


@dataclass
class DeployConfig:
    """服务部署配置"""
    name: str  # 服务名称
    description: str  # 服务描述
    exec_start: str  # 服务启动命令
    source_path: str  # 源文件路径
    install_path: str  # 安装路径
    user: str = "root"  # 运行用户
    merge_config_dir: str = None  # 合并配置目录
    dependencies: List[str] = None  # 依赖包列表
    use_sudo: bool = True  # 是否使用sudo权限
    # systemd特定配置
    after: str = "network.target"  # 服务依赖
    restart: str = "always"  # 重启策略
    restart_sec: int = 3  # 重启间隔
    source_type: Optional[ServiceSource] = None  # 源类型（可选，如果不指定则自动检测）
    binary: str = None  # 可执行文件路径（可选，如果不指定则自动检测）

    # JSON Schema for validation
    SCHEMA = {
        "type": "object",
        "required": ["name", "description", "exec_start", "source_path", "install_path"],
        "properties": {
            "name": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
            "description": {"type": "string"},
            "exec_start": {"type": "string"},
            "source_path": {"type": "string"},
            "install_path": {"type": "string", "pattern": "^/"},
            "user": {"type": "string"},
            "merge_config_dir": {"type": ["string", "null"]},
            "dependencies": {
                "type": ["array", "null"],
                "items": {"type": "string"}
            },
            "use_sudo": {"type": "boolean"},
            "after": {"type": "string"},
            "restart": {"type": "string"},
            "restart_sec": {"type": "integer", "minimum": 1}
        }
    }

    @classmethod
    def from_json(cls, json_path: Union[str, Path]) -> "DeployConfig":
        """
        从JSON文件创建部署配置
        
        Args:
            json_path: JSON配置文件路径
            
        Returns:
            DeployConfig: 部署配置对象
            
        Raises:
            ValueError: 配置文件格式错误
            FileNotFoundError: 配置文件不存在
        """
        try:
            # 读取JSON文件
            with open(json_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 验证JSON Schema
            jsonschema.validate(instance=config_data, schema=cls.SCHEMA)

            # 处理相对路径
            json_dir = Path(json_path).parent

            # 处理source_path
            if not (config_data['source_path'].startswith('/') or
                    config_data['source_path'].startswith('http://') or
                    config_data['source_path'].startswith('https://') or
                    config_data['source_path'].startswith('file://')):
                config_data['source_path'] = str(json_dir / config_data['source_path'])

            # 处理merge_config_dir
            if config_data.get('merge_config_dir'):
                if not config_data['merge_config_dir'].startswith('/'):
                    config_data['merge_config_dir'] = str(json_dir / config_data['merge_config_dir'])

            # 创建配置对象
            return cls(**config_data)

        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {str(e)}")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "DeployConfig":
        """
        从字典创建部署配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            DeployConfig: 部署配置对象
        """
        # 验证JSON Schema
        try:
            jsonschema.validate(instance=config_dict, schema=cls.SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Invalid configuration: {str(e)}")

        return cls(**config_dict)

    def __post_init__(self):
        """初始化后处理，验证路径和设置源类型"""
        # 验证安装路径
        if not self.install_path.startswith('/'):
            raise ValueError(f"Install path must be absolute: {self.install_path}")

        # 验证本地源路径
        if self.source_path.startswith('file://'):
            local_path = self.source_path[7:]
            if not local_path.startswith('/'):
                raise ValueError(f"Local source path must be absolute: {local_path}")

        # 自动检测源类型
        if self.source_type is None:
            self.source_type = ServiceSource.detect_source_type(self.source_path)

    def to_service_definition(self) -> ServiceDefinition:
        """转换为服务定义"""
        return ServiceDefinition(
            name=self.name,
            description=self.description,
            exec_start=self.exec_start,
            working_directory=self.install_path,
            user=self.user,
            after=self.after,
            restart=self.restart,
            restart_sec=self.restart_sec
        )


class ServiceManagerDetector:
    """服务管理器检测器"""

    @staticmethod
    def detect(conn: Connection) -> ServiceManager:
        """检测远程系统使用的服务管理器类型"""
        try:
            result = conn.run(
                "if command -v systemctl >/dev/null 2>&1; then "
                "   echo 'systemd';"
                "elif command -v service >/dev/null 2>&1; then "
                "   echo 'service';"
                "else "
                "   echo 'unknown';"
                "fi",
                hide=True
            )

            manager = result.stdout.strip()
            if manager == 'systemd':
                return ServiceManager.SYSTEMD
            elif manager == 'service':
                return ServiceManager.SERVICE
            else:
                return ServiceManager.UNKNOWN
        except UnexpectedExit:
            return ServiceManager.UNKNOWN


class ServiceManagerCommands:
    """服务管理器命令映射"""
    COMMANDS: Dict[ServiceManager, Dict[str, str]] = {
        ServiceManager.SYSTEMD: {
            "start": "systemctl start",
            "stop": "systemctl stop",
            "restart": "systemctl restart",
            "status": "systemctl status",
            "enable": "systemctl enable",
            "disable": "systemctl disable",
            "reload": "systemctl daemon-reload"
        },
        ServiceManager.SERVICE: {
            "start": "service start",
            "stop": "service stop",
            "restart": "service restart",
            "status": "service status",
            "enable": "chkconfig on",
            "disable": "chkconfig off"
        }
    }

    @classmethod
    def get_command(cls, svc_manager: ServiceManager, action: str) -> str:
        """获取特定服务管理器的命令"""
        return cls.COMMANDS.get(svc_manager, {}).get(action, "")


class ServiceManagerOperator:
    """服务管理器操作类"""

    # 系统保护的服务列表
    PROTECTED_SERVICES = {
        'sshd',  # SSH服务
        'systemd',  # 系统服务管理器
        'network',  # 网络服务
        'NetworkManager',  # 网络管理器
        'dbus',  # 系统消息总线
        'rsyslog',  # 系统日志
        'crond',  # 定时任务服务
        'firewalld',  # 防火墙
        'getty',  # 终端管理
        'udev',  # 设备管理
        'journald',  # 日志管理
        'polkit',  # 权限管理
        'accounts-daemon',  # 账户服务
        'sudo',  # sudo服务
        'docker',  # Docker服务
        'kubelet',  # Kubernetes服务
    }

    def __init__(self, conn: Connection):
        self.conn = conn
        self.svc_manager = ServiceManagerDetector.detect(conn)
        if self.svc_manager == ServiceManager.UNKNOWN:
            raise RuntimeError("Unable to detect service manager")

    def _is_protected_service(self, service_name: str) -> bool:
        """
        检查服务是否是受保护的系统服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否是受保护的服务
        """
        # 移除.service后缀进行比较
        base_name = service_name.replace('.service', '')

        # 检查是否在保护列表中
        if base_name in self.PROTECTED_SERVICES:
            return True

        # 检查是否以系统服务常见前缀开头
        protected_prefixes = ('system-', 'sys-', 'systemd-', 'dbus-', 'polkit-', 'network-')
        if any(base_name.startswith(prefix) for prefix in protected_prefixes):
            return True

        return False

    def _execute_cmd(self, cmd: str, use_sudo: bool = True) -> bool:
        """执行命令"""
        try:
            if use_sudo:
                self.conn.sudo(cmd)
            else:
                self.conn.run(cmd)
            return True
        except UnexpectedExit:
            return False

    @classmethod
    def _ensure_path_validate(cls, path: str) -> str:
        # 确保路径不能为空
        if not path:
            raise ValueError("Path cannot be empty")

        # 确保路径不能为常用的敏感路径
        sensitive_paths = ["/etc", "/usr", "/var"]
        if any(path.startswith(sensitive) for sensitive in sensitive_paths):
            raise ValueError(f"Path cannot start with sensitive directories: {sensitive_paths}")
        # 确保路径不能包含特殊字符
        if any(char in path for char in [';', '&', '|', '>', '<', '$', '`', ' ']):
            raise ValueError(f"Path contains invalid characters: {path}")

        # 不能为根目录
        if path == "/":
            raise ValueError("Path cannot be root directory: /")

        # 确保路径不能包含 ..
        if ".." in path:
            raise ValueError(f"Path cannot contain '..': {path}")

        # 确保路径为绝对路径
        if not path.startswith('/'):
            raise ValueError(f"Path must be absolute: {path}")

        return path

    def _download_to_local(self, url: str) -> Tuple[bool, str]:
        """
        下载文件到本地临时目录
        
        Args:
            url: 下载URL
            
        Returns:
            Tuple[bool, str]: (是否成功, 本地文件路径)
        """
        try:
            # 从URL中提取文件名
            filename = unquote(os.path.basename(urlparse(url).path))
            if not filename:
                filename = 'downloaded_file.tar.gz'

            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            local_path = os.path.join(temp_dir, filename)

            # 下载文件
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True, local_path
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False, ""

    def _transfer_file(self, local_path: str, remote_path: str, use_sudo: bool = True) -> bool:
        """
        将本地文件传输到远程服务器
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            use_sudo: 是否使用sudo权限
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保本地文件存在
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")

            # 如果需要sudo权限，先上传到临时目录再移动
            if use_sudo:
                temp_remote_path = f"/tmp/{os.path.basename(local_path)}"
                self.conn.put(local_path, temp_remote_path)
                self._execute_cmd(f"mv {temp_remote_path} {remote_path}", use_sudo=True)
                self._execute_cmd(f"chown root:root {remote_path}", use_sudo=True)
            else:
                self.conn.put(local_path, remote_path)

            return True
        except Exception as e:
            print(f"Error transferring file: {str(e)}")
            return False

    def _download_source(self, source_path: str, target_path: str, use_sudo: bool = True) -> bool:
        """
        下载或复制源文件到目标路径
        
        Args:
            source_path: 源路径
            target_path: 目标路径（必须是绝对路径）
            use_sudo: 是否使用sudo权限
        
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目标路径是绝对路径
            target_path = self._ensure_path_validate(target_path)
            source_type = ServiceSource.detect_source_type(source_path)

            if source_type == ServiceSource.HTTP:
                # 下载到本地临时目录
                success, local_path = self._download_to_local(source_path)
                if not success:
                    return False

                # 传输到远程服务器
                try:
                    return self._transfer_file(local_path, target_path, use_sudo)
                finally:
                    # 清理临时文件
                    if os.path.exists(local_path):
                        os.unlink(local_path)
                    if os.path.exists(os.path.dirname(local_path)):
                        os.rmdir(os.path.dirname(local_path))

            elif source_type == ServiceSource.LOCAL_FILE:
                # 处理 file:// 协议
                if source_path.startswith('file://'):
                    source_path = source_path[7:]
                # 直接传输本地文件
                return self._transfer_file(source_path, target_path, use_sudo)
            else:
                raise ValueError(f"Unsupported source type for path: {source_path}")

        except Exception as e:
            print(f"Error handling source: {str(e)}")
            return False

    def _upload_service_file(self, service_name: str, content: str) -> str:
        """
        上传服务文件
        
        Args:
            service_name: 服务名称
            content: 服务文件内容
            
        Returns:
            str: 服务文件在远程主机上的路径
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.service', delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            # 构建目标路径
            remote_path = f"/etc/systemd/system/{service_name}.service"

            try:
                # 上传文件
                self.conn.put(temp_file.name, remote=remote_path, preserve_mode=False)
                # 设置正确的权限
                self.conn.sudo(f"chown root:root {remote_path}")
                self.conn.sudo(f"chmod 644 {remote_path}")
                return remote_path
            finally:
                # 清理临时文件
                os.unlink(temp_file.name)

    def deploy_service_with_service_dir(self, service_dir: str):
        # 判断定义文件是否存在
        if not os.path.exists(os.path.join(service_dir, 'definitions.json')):
            raise FileNotFoundError(f"Service definitions.json not found in {service_dir}")

        config = DeployConfig.from_json(os.path.join(service_dir, 'definitions.json'))

        config.merge_config_dir = os.path.join(service_dir, 'deploy')

        self.deploy_service(config)

    def deploy_service(self, config: DeployConfig):
        """部署服务"""
        try:
            # 检查是否是受保护的服务
            if self._is_protected_service(config.name):
                raise ValueError(f"Cannot deploy protected system service: {config.name}")

            # 确保安装路径是绝对路径
            install_path = self._ensure_path_validate(config.install_path)

            # 1. 创建安装目录
            self._execute_cmd(f"mkdir -p {install_path}", config.use_sudo)

            # 2. 下载或复制源文件到安装目录并解压
            extract_archive(
                self.conn,
                config.source_path,
                install_path,
                use_sudo=config.use_sudo,
            )

            # 3.copy本地目录等配置到安装目录：必须是相对路径
            if config.merge_config_dir and os.path.exists(config.merge_config_dir):
                extract_archive(self.conn, config.merge_config_dir, install_path, use_sudo=config.use_sudo)

            # 4. 安装依赖
            if config.dependencies:
                pkg_operator = PackageManagerOperator(self.conn)
                for dep in config.dependencies:
                    pkg_operator.install(dep, config.use_sudo)

            # 5. 确保binary文件可执行
            if config.binary:
                binary_path = os.path.join(install_path, config.binary)
                self._execute_cmd(f"chmod +x {binary_path}", config.use_sudo)

            # 6. 创建systemd服务文件
            if self.svc_manager == ServiceManager.SYSTEMD:
                service_content = config.to_service_definition().generate_systemd_unit()

                # 上传服务文件
                self._upload_service_file(config.name, service_content)

                # 重新加载systemd
                self.control_service("", "reload", config.use_sudo)

                # 启用并启动服务
                self.control_service(config.name, "enable", config.use_sudo)
                self.control_service(config.name, "start", config.use_sudo)

        except Exception as e:
            logger.exception(f"Error deploying service: {str(e)}", exc_info=e)
            raise e

    def control_service(self, service_name: str, action: str, use_sudo: bool = True) -> bool:
        """控制服务"""
        # 对于reload操作，不需要检查服务名称（因为是重新加载systemd本身）
        if action != "reload" and service_name:
            # 检查是否是受保护的服务
            if self._is_protected_service(service_name):
                if action in ["stop", "disable", "restart"]:
                    raise ValueError(f"Cannot {action} protected system service: {service_name}")

        cmd = f"{ServiceManagerCommands.get_command(self.svc_manager, action)} {service_name}"
        return self._execute_cmd(cmd, use_sudo)

    def remove_service(self, service_name: str, install_path: Optional[str] = None, use_sudo: bool = True) -> bool:
        """移除服务"""
        try:
            # 检查是否是受保护的服务
            if self._is_protected_service(service_name):
                raise ValueError(f"Cannot remove protected system service: {service_name}")

            # 1. 停止并禁用服务
            self.control_service(service_name, "stop", use_sudo)
            self.control_service(service_name, "disable", use_sudo)

            # 2. 删除服务文件
            if self.svc_manager == ServiceManager.SYSTEMD:
                service_file = f"/etc/systemd/system/{service_name}.service"
                self._execute_cmd(f"rm -f {service_file}", use_sudo)
                self.control_service("", "reload", use_sudo)

            # 3. 删除安装目录（如果提供）
            if install_path:
                # 确保安装路径是绝对路径
                install_path = self._ensure_path_validate(install_path)
                self._execute_cmd(f"rm -rf {install_path}", use_sudo)

            return True
        except Exception as e:
            print(f"Error removing service: {str(e)}")
            return False
