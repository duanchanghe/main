"""
MinIO 存储服务
用于存储音频文件和其他媒体资源
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO
from django.conf import settings

logger = logging.getLogger(__name__)


class MinIOStorageError(Exception):
    """MinIO 存储异常"""
    pass


class MinIOStorage:
    """MinIO 对象存储服务"""

    def __init__(self):
        self._client = None
        self._initialized = False

    @property
    def client(self):
        """延迟初始化 MinIO 客户端"""
        if not self._initialized:
            self._init_client()
        return self._client

    def _init_client(self):
        """初始化 MinIO 客户端"""
        try:
            from minio import Minio
            from minio.error import S3Error

            endpoint = getattr(settings, 'MINIO_ENDPOINT', 'localhost:9000')
            access_key = getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin')
            secret_key = getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin')
            secure = getattr(settings, 'MINIO_SECURE', False)

            self._client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            self._initialized = True
            logger.info(f"MinIO 客户端初始化成功: {endpoint}")

        except ImportError:
            logger.warning("minio 库未安装，将使用本地存储")
            self._initialized = True
        except Exception as e:
            logger.error(f"MinIO 客户端初始化失败: {e}")
            self._initialized = True

    def _get_bucket_name(self, bucket_type: str = 'audiobooks') -> str:
        """获取存储桶名称"""
        return getattr(settings, f'MINIO_BUCKET_{bucket_type.upper()}', f'novels-{bucket_type}')

    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"创建存储桶: {bucket_name}")
            return True
        except Exception as e:
            logger.error(f"检查/创建存储桶失败: {e}")
            return False

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        bucket_name: str = 'audiobooks',
        content_type: str = 'audio/mpeg',
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        上传文件到 MinIO

        Args:
            file_path: 本地文件路径
            object_name: 对象名称（不指定则自动生成）
            bucket_name: 存储桶名称
            content_type: 文件类型
            metadata: 元数据

        Returns:
            包含文件信息的字典
        """
        if not os.path.exists(file_path):
            raise MinIOStorageError(f"文件不存在: {file_path}")

        if object_name is None:
            ext = os.path.splitext(file_path)[1]
            object_name = f"{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4().hex}{ext}"

        try:
            if not self.ensure_bucket_exists(bucket_name):
                raise MinIOStorageError(f"无法访问存储桶: {bucket_name}")

            metadata_dict = metadata or {}
            metadata_headers = {f'x-amz-meta-{k}': str(v) for k, v in metadata_dict.items()}

            file_size = os.path.getsize(file_path)
            self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
                content_type=content_type,
                metadata=metadata_dict
            )

            logger.info(f"文件上传成功: {bucket_name}/{object_name}")

            return {
                'success': True,
                'bucket': bucket_name,
                'object_name': object_name,
                'size': file_size,
                'url': self.get_presigned_url(bucket_name, object_name),
                'path': f'{bucket_name}/{object_name}'
            }

        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise MinIOStorageError(f"上传失败: {e}")

    def upload_data(
        self,
        data: BinaryIO,
        object_name: str,
        bucket_name: str = 'audiobooks',
        content_type: str = 'audio/mpeg',
        size: int = 0,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        上传二进制数据到 MinIO

        Args:
            data: 二进制数据
            object_name: 对象名称
            bucket_name: 存储桶名称
            content_type: 文件类型
            size: 数据大小
            metadata: 元数据

        Returns:
            包含文件信息的字典
        """
        try:
            if not self.ensure_bucket_exists(bucket_name):
                raise MinIOStorageError(f"无法访问存储桶: {bucket_name}")

            metadata_dict = metadata or {}

            self.client.put_object(
                bucket_name,
                object_name,
                data,
                size,
                content_type=content_type,
                metadata=metadata_dict
            )

            logger.info(f"数据上传成功: {bucket_name}/{object_name}")

            return {
                'success': True,
                'bucket': bucket_name,
                'object_name': object_name,
                'url': self.get_presigned_url(bucket_name, object_name),
                'path': f'{bucket_name}/{object_name}'
            }

        except Exception as e:
            logger.error(f"数据上传失败: {e}")
            raise MinIOStorageError(f"上传失败: {e}")

    def download_file(self, object_name: str, bucket_name: str = 'audiobooks') -> str:
        """
        下载文件到临时目录

        Returns:
            临时文件路径
        """
        try:
            import tempfile

            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, os.path.basename(object_name))

            self.client.fget_object(bucket_name, object_name, local_path)
            logger.info(f"文件下载成功: {bucket_name}/{object_name} -> {local_path}")

            return local_path

        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            raise MinIOStorageError(f"下载失败: {e}")

    def get_presigned_url(
        self,
        object_name: str,
        bucket_name: str = 'audiobooks',
        expires: int = 3600
    ) -> str:
        """获取预签名 URL（用于下载/预览）"""
        try:
            url = self.client.presigned_get_object(bucket_name, object_name, expires=expires)
            return url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {e}")
            return f"/api/media/{bucket_name}/{object_name}"

    def get_presigned_put_url(
        self,
        object_name: str,
        bucket_name: str = 'uploads',
        expires: int = 3600
    ) -> str:
        """获取预签名上传 URL（用于客户端直接上传）"""
        try:
            url = self.client.presigned_put_object(bucket_name, object_name, expires=expires)
            return url
        except Exception as e:
            logger.error(f"生成预签名上传URL失败: {e}")
            raise MinIOStorageError(f"生成上传URL失败: {e}")

    def delete_object(self, object_name: str, bucket_name: str = 'audiobooks') -> bool:
        """删除对象"""
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"对象删除成功: {bucket_name}/{object_name}")
            return True
        except Exception as e:
            logger.error(f"对象删除失败: {e}")
            return False

    def list_objects(
        self,
        bucket_name: str = 'audiobooks',
        prefix: str = '',
        recursive: bool = True
    ) -> list:
        """列出对象"""
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
            return [
                {
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                }
                for obj in objects
            ]
        except Exception as e:
            logger.error(f"列出对象失败: {e}")
            return []

    def get_object_info(self, object_name: str, bucket_name: str = 'audiobooks') -> Optional[Dict]:
        """获取对象信息"""
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'name': stat.object_name,
                'size': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'metadata': stat.metadata
            }
        except Exception as e:
            logger.error(f"获取对象信息失败: {e}")
            return None


class LocalStorageFallback:
    """本地存储备用方案"""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or getattr(settings, 'LOCAL_MEDIA_ROOT', '/tmp/audiobooks')
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_full_path(self, bucket_name: str, object_name: str) -> str:
        """获取完整路径"""
        path = os.path.join(self.base_dir, bucket_name, object_name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def upload_file(self, file_path: str, object_name: str, bucket_name: str = 'audiobooks', **kwargs) -> Dict:
        """上传文件到本地"""
        import shutil

        dest_path = self._get_full_path(bucket_name, object_name)
        shutil.copy2(file_path, dest_path)

        return {
            'success': True,
            'bucket': bucket_name,
            'object_name': object_name,
            'path': dest_path,
            'url': f'/media/{bucket_name}/{object_name}'
        }

    def get_presigned_url(self, object_name: str, bucket_name: str = 'audiobooks', **kwargs) -> str:
        """获取本地 URL"""
        return f'/media/{bucket_name}/{object_name}'


def get_storage() -> Any:
    """获取存储服务实例"""
    use_minio = getattr(settings, 'USE_MINIO', False)

    if use_minio:
        return MinIOStorage()
    else:
        return LocalStorageFallback()


storage = get_storage()
