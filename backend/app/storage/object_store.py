import io
from typing import Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.core.exceptions import StorageException
from app.core.logging import logger


class ObjectStore:
    """Object storage adapter wrapping S3 and MinIO via boto3."""

    def __init__(self):
        self.bucket_name = settings.MINIO_BUCKET
        endpoint_url = settings.MINIO_ENDPOINT
        # Ensure endpoint has protocol if not provided
        if endpoint_url and not endpoint_url.startswith("http://") and not endpoint_url.startswith("https://"):
            endpoint_url = f"http://{endpoint_url}"

        # Initialize S3 / MinIO client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url if endpoint_url else None,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def ensure_bucket_exists(self) -> None:
        """Verifies or creates the target bucket if it doesn't already exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ["404", "NoSuchBucket"]:
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created object storage bucket: {self.bucket_name}")
                except Exception as create_err:
                    logger.warning(f"Failed to create bucket {self.bucket_name}: {create_err}")
            else:
                logger.warning(f"Bucket check returned: {e}")

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Uploads a byte buffer to the object store at the designated key."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.info(f"Successfully stored object: {key} ({len(data)} bytes)")
            return key
        except Exception as e:
            logger.error(f"Failed to upload object {key} to {self.bucket_name}: {e}")
            raise StorageException(f"Failed to store file in object storage: {str(e)}")

    def get(self, key: str) -> bytes:
        """Fetches object content as raw bytes from the designated key."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to retrieve object {key} from {self.bucket_name}: {e}")
            raise StorageException(f"Failed to fetch file from object storage: {str(e)}")

    def delete(self, key: str) -> bool:
        """Removes the object at the specified key."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            logger.info(f"Successfully deleted object: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object {key} from {self.bucket_name}: {e}")
            raise StorageException(f"Failed to delete file from object storage: {str(e)}")


# Singleton instance
object_store = ObjectStore()
