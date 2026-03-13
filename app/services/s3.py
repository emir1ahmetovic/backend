from __future__ import annotations

from app.config import get_settings


def generate_upload_url(bucket: str, key: str, content_type: str | None = None, expires_in: int = 3600) -> str:
    settings = get_settings()
    _ = settings
    try:
        import boto3 
    except Exception:
        return "https://example.com/upload-url"

    client = boto3.client("s3", region_name=settings.aws_region)
    params = {"Bucket": bucket, "Key": key}
    if content_type:
        params["ContentType"] = content_type
    return client.generate_presigned_url("put_object", Params=params, ExpiresIn=expires_in)


def delete_file(bucket: str, key: str) -> None:
    settings = get_settings()
    try:
        import boto3  
    except Exception:
        return None

    client = boto3.client("s3", region_name=settings.aws_region)
    try:
        client.delete_object(Bucket=bucket, Key=key)
    except Exception:
        return None