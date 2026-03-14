from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.config import get_settings
from app.services import bedrock
from app.services.chunking import split_into_paragraphs

logger = logging.getLogger(__name__)


def _parse_summary_json(raw: str) -> Dict[str, Any]:
   
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed

        return {"data": parsed}
    except Exception:
        logger.warning("Failed to parse summary JSON; returning raw text wrapper.")
        return {"raw": raw}


def summarize_by_paragraphs(text: str) -> Dict[str, Any]:
    
    settings = get_settings()
    paragraphs: List[str] = split_into_paragraphs(
        text,
        min_chars=settings.summarize_min_paragraph_chars,
        max_chars=settings.summarize_max_paragraph_chars,
    )
    if not paragraphs:
        return {"paragraphs": [], "combined_summary": None}

    results: List[Dict[str, Any]] = []

    for idx, para in enumerate(paragraphs):
        raw = bedrock.summarize_text(para)
        summary = _parse_summary_json(raw)

        results.append(
            {
                "index": idx,
                "text": para,
                "summary": summary,
            }
        )

    combined_short_parts: List[str] = []
    combined_detailed_parts: List[str] = []

    for r in results:
        summary = r.get("summary") or {}
        if not isinstance(summary, dict):
            continue
        short = summary.get("short_summary")
        detailed = summary.get("detailed_summary")
        if isinstance(short, str) and short.strip():
            combined_short_parts.append(short.strip())
        if isinstance(detailed, str) and detailed.strip():
            combined_detailed_parts.append(detailed.strip())

    combined_summary = {
        "short_summary": " ".join(combined_short_parts).strip(),
        "detailed_summary": " ".join(combined_detailed_parts).strip(),
    }

    return {
        "paragraphs": results,
        "combined_summary": combined_summary,
    }

