import boto3
import os

class StorageService:
    """
    Handles file uploads/downloads using S3 or MinIO.
    """
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=os.getenv('S3_ENDPOINT', None), # Used for MinIO
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin')
        )
        self.bucket = os.getenv('S3_BUCKET', 'bughunter-evidence')

    def upload_file(self, file_path: str, object_name: str = None):
        if object_name is None:
            object_name = os.path.basename(file_path)
            
        try:
            self.s3.upload_file(file_path, self.bucket, object_name)
            return True
        except Exception as e:
            print(e)
            return False

    def download_file(self, object_name: str, file_path: str):
        try:
            self.s3.download_file(self.bucket, object_name, file_path)
            return True
        except Exception as e:
            print(e)
            return False
