from __future__ import annotations

from app.config import get_settings


def extract_text_from_s3(s3_bucket: str, s3_key: str) -> str:
    settings = get_settings()
    _ = settings
    try:
        import boto3  # type: ignore
    except Exception:
        return ""

    client = boto3.client("textract", region_name=settings.aws_region)
    try:
        resp = client.detect_document_text(Document={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}})
        blocks = resp.get("Blocks") or []
        lines: list[str] = []
        for b in blocks:
            if b.get("BlockType") == "LINE" and b.get("Text"):
                lines.append(b["Text"])
        return "\n".join(lines)
    except Exception:
        return ""

