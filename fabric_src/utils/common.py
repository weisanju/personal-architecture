import logging
from fabric import Connection
import os
import tempfile
import shutil
from typing import Tuple
import requests
from urllib.parse import urlparse, unquote

from fabric_src.utils.cache_manager import DownloadCache

# 全局缓存管理器实例
_download_cache = DownloadCache()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


def download_file(url: str, use_cache: bool = True) -> Tuple[bool, str]:
    """
    下载文件到本地
    
    Args:
        url: 下载URL
        use_cache: 是否使用缓存
        
    Returns:
        Tuple[bool, str]: (是否成功, 本地文件路径)
    """
    temp_dir = None
    try:
        # 检查缓存
        if use_cache:
            cached_path = _download_cache.get(url)
            if cached_path:
                return True, cached_path

        # 从URL中提取文件名
        filename = unquote(os.path.basename(urlparse(url).path))
        if not filename:
            filename = 'downloaded_file'

        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)

        # 下载文件
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 添加到缓存
        if use_cache:
            cached_path = _download_cache.put(url, temp_path)
            os.unlink(temp_path)
            os.rmdir(temp_dir)
            return True, cached_path

        return True, temp_path

    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False, ""


def _create_temp_tgz(source_path: str) -> str:
    """
    将源文件或目录打包为临时tgz文件
    
    Args:
        source_path: 源文件或目录路径
        
    Returns:
        Tuple[bool, str]: (是否成功, 临时tgz文件路径)
    """
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        source_name = os.path.basename(source_path)

        tgz_path = os.path.join(temp_dir, f"{source_name}.tar.gz")

        # 如果是目录，直接打包
        if os.path.isdir(source_path):
            base_dir = os.path.dirname(source_path)
            shutil.make_archive(
                os.path.join(temp_dir, source_name),  # 不包含.tgz的路径
                'gztar',  # 格式为tar.gz
                root_dir=source_path,  # 要打包的目录
            )
        # 如果是文件，根据类型处理
        elif os.path.isfile(source_path):
            if source_path.endswith(('.tar.gz', '.tgz')):
                # 如果已经是tgz格式，直接复制
                shutil.copy2(source_path, tgz_path)
            elif source_path.endswith('.tar'):
                # 如果是tar文件，添加gzip压缩
                import tarfile
                import gzip
                with tarfile.open(source_path, 'r:') as tar:
                    with gzip.open(tgz_path, 'wb') as gz:
                        gz.write(tar.read())
            elif source_path.endswith('.zip'):
                # 如果是zip文件，先解压后重新打包为tgz
                temp_extract = os.path.join(temp_dir, 'extracted')
                shutil.unpack_archive(source_path, temp_extract, 'zip')
                shutil.make_archive(
                    os.path.splitext(tgz_path)[0],
                    'gztar',
                    root_dir=temp_extract
                )
            else:
                # 其他类型文件，直接打包
                shutil.make_archive(
                    os.path.splitext(tgz_path)[0],
                    'gztar',
                    root_dir=os.path.dirname(source_path),
                    base_dir=os.path.basename(source_path)
                )
        else:
            raise ValueError(f"Source path does not exist: {source_path}")
        return tgz_path
    except Exception as e:
        logger.exception(f"Error creating tgz: {str(e)}", exc_info=e)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise e


def extract_archive(conn: Connection,
                    source_path: str,
                    target_dir: str,
                    use_sudo: bool = False):
    """
    将本地文件或目录传输并解压到远程主机
    
    Args:
        conn: Fabric连接对象
        source_path: 源文件或目录路径（支持目录、.tar.gz、.tgz、.tar、.zip文件）
        target_dir: 目标解压目录
        use_sudo: 是否使用sudo权限
    Returns:
        bool: 操作是否成功
    """
    try:
        # 如果是HTTP URL，先下载到本地
        if source_path.startswith(('http://', 'https://')):
            success, local_path = download_file(source_path, True)
            if not success:
                return False
            source_path = local_path
        # 1. 创建临时tgz文件
        temp_tgz = _create_temp_tgz(source_path)

        # 2. 确保远程目标目录存在
        mkdir_cmd = f"mkdir -p {target_dir}"
        if use_sudo:
            conn.sudo(mkdir_cmd)
        else:
            conn.run(mkdir_cmd)

        try:
            # 3. 上传tgz文件到远程临时目录
            remote_temp = f"/tmp/{os.path.basename(temp_tgz)}"
            conn.put(temp_tgz, remote=remote_temp)

            # 4. 解压文件
            extract_cmd = f"tar -xzf {remote_temp} -C {target_dir}  --overwrite"
            if use_sudo:
                # 如果使用sudo，设置目录权限
                conn.sudo(extract_cmd)
                conn.sudo(f"chown -R root:root {target_dir}")
            else:
                conn.run(extract_cmd)

            # 5. 清理远程临时文件
            clean_cmd = f"rm -f {remote_temp}"
            if use_sudo:
                conn.sudo(clean_cmd)
            else:
                conn.run(clean_cmd)

        finally:
            if temp_tgz and os.path.exists(temp_tgz):
                os.unlink(temp_tgz)
            if os.path.exists(os.path.dirname(temp_tgz)):
                shutil.rmtree(os.path.dirname(temp_tgz))

    except Exception as e:
        logger.exception(f"Error in extract_archive", exc_info=e)
