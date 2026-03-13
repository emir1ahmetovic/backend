from __future__ import annotations

from typing import List


def split_into_paragraphs(
    text: str,
    *,
    min_chars: int = 50,
    max_chars: int = 4000,
) -> List[str]:
    """
    Split text into paragraph-like chunks, primarily using blank lines as
    boundaries, with basic merging of very short paragraphs and an upper
    bound on chunk size.
    """
    if not text or not text.strip():
        return []

    # Normalize newlines so we can reliably split on blank lines.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # First split on blank lines (paragraph boundaries).
    raw_paragraphs = [p.strip() for p in normalized.split("\n\n")]

    # Filter out empty entries.
    paragraphs = [p for p in raw_paragraphs if p]

    # Merge very short paragraphs into their neighbors to avoid tiny chunks.
    merged: list[str] = []
    buffer = ""
    for p in paragraphs:
        candidate = (buffer + "\n\n" + p).strip() if buffer else p
        if len(candidate) < min_chars:
            buffer = candidate
            continue
        if buffer:
            merged.append(buffer)
            buffer = ""
        merged.append(p)
    if buffer:
        merged.append(buffer)

    # Enforce a maximum size by hard-splitting overly long paragraphs.
    final: list[str] = []
    for p in merged:
        if len(p) <= max_chars:
            final.append(p)
            continue

        start = 0
        while start < len(p):
            final.append(p[start : start + max_chars])
            start += max_chars

    return final

