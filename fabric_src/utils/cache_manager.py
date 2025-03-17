import hashlib
import os
import shutil
import time
from typing import Optional
from urllib.parse import unquote, urlparse


class DownloadCache:
    """下载缓存管理器"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化下载缓存管理器

        Args:
            cache_dir: 缓存目录路径，如果为None则使用默认路径
        """
        if cache_dir is None:
            # 默认缓存目录在用户目录下
            cache_dir = os.path.expanduser("~/.fabric_cache/downloads")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, url: str) -> str:
        """
        生成URL的缓存键

        Args:
            url: 下载URL

        Returns:
            str: 缓存键（URL的MD5值）
        """
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache_path(self, url: str) -> str:
        """
        获取URL对应的缓存文件路径

        Args:
            url: 下载URL

        Returns:
            str: 缓存文件路径
        """
        # 获取原始文件名
        filename = unquote(os.path.basename(urlparse(url).path))
        if not filename:
            filename = 'downloaded_file'

        # 使用URL的MD5值作为子目录，避免文件名冲突
        cache_key = self._get_cache_key(url)
        cache_subdir = os.path.join(self.cache_dir, cache_key[:2], cache_key[2:4])
        os.makedirs(cache_subdir, exist_ok=True)

        # 组合最终的缓存文件路径
        return os.path.join(cache_subdir, filename)

    def get(self, url: str) -> Optional[str]:
        """
        从缓存中获取文件

        Args:
            url: 下载URL

        Returns:
            Optional[str]: 缓存文件路径，如果不存在则返回None
        """
        cache_path = self._get_cache_path(url)
        return cache_path if os.path.exists(cache_path) else None

    def put(self, url: str, file_path: str) -> str:
        """
        将文件添加到缓存

        Args:
            url: 下载URL
            file_path: 源文件路径

        Returns:
            str: 缓存文件路径
        """
        cache_path = self._get_cache_path(url)
        shutil.copy2(file_path, cache_path)
        return cache_path

    def clear(self, max_age: Optional[int] = None):
        """
        清理缓存

        Args:
            max_age: 最大缓存时间（秒），如果为None则清理所有缓存
        """
        if max_age is None:
            # 清理所有缓存
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
        else:
            # 清理过期缓存
            now = time.time()
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if now - os.path.getmtime(file_path) > max_age:
                        os.unlink(file_path)

            # 清理空目录
            for root, dirs, files in os.walk(self.cache_dir, topdown=False):
                for _dir in dirs:
                    dir_path = os.path.join(root, _dir)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)

