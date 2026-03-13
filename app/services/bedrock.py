from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

import boto3

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "mistral.mistral-7b-instruct-v0:2")
BEDROCK_EMBEDDING_MODEL_ID = os.getenv("BEDROCK_EMBEDDING_MODEL_ID")

SUMMARIZE_SYSTEM_PROMPT = """You are an information extraction system used in a Retrieval-Augmented Generation (RAG) pipeline.
Your task is to process a chunk of text and convert it into structured metadata for indexing and retrieval.

Rules:
- Do NOT explain anything.
- Do NOT add commentary.
- Do NOT repeat the original text.
- ONLY output valid JSON.
- Keep summaries concise and factual.
- If information is missing, return null for that field.

Return the data using the following schema:
{
    "title": "Short descriptive title of the content",
    "short_summary": "1-2 sentence summary capturing the key idea",
    "detailed_summary": "4-6 sentence structured summary of the important concepts",
    "description": "Plain explanation of what the text is about and its scope",
    "intent": "The main purpose of the text (e.g., explanation, tutorial, definition, comparison, documentation)",
    "topics": ["main topic", "subtopic1", "subtopic2"],
    "keywords": ["important", "terms", "for", "retrieval"],
    "entities": ["important named concepts, technologies, people, or systems"],
    "concepts": ["important theoretical ideas or principles mentioned"],
    "document_type": "article | documentation | tutorial | research | definition | other",
    "difficulty_level": "beginner | intermediate | advanced",
    "chunk_summary": "A retrieval-optimized summary written to maximize semantic search relevance"
}"""

ANSWER_SYSTEM_PROMPT = """You are a precise question-answering system used in a Retrieval-Augmented Generation (RAG) pipeline.
Your task is to answer the user's question based strictly on the provided context.

Rules:
- Do NOT fabricate information.
- Do NOT answer from prior knowledge if context is provided.
- If the answer is not present in the context, respond with: "The provided context does not contain enough information to answer this question."
- Be concise, factual, and direct.
- Do NOT add commentary or unnecessary explanation.
- Structure your answer clearly. Use bullet points or numbered steps only when the answer is a list or process."""

ANSWER_NO_CONTEXT_SYSTEM_PROMPT = """You are a knowledgeable and precise research assistant.
Your task is to answer the user's question accurately and concisely.

Rules:
- Be factual and direct.
- Do NOT speculate or fabricate information.
- If you are uncertain, clearly state that.
- Use bullet points or numbered steps only when the answer is a list or process.
- Do NOT add unnecessary commentary."""

QUESTIONS_SYSTEM_PROMPT = """You are an analytical assistant used in a Retrieval-Augmented Generation (RAG) pipeline.
Your task is to generate high-quality follow-up questions that would help a user retrieve more relevant information from a knowledge base.

Rules:
- Do NOT explain anything.
- Do NOT add commentary.
- Generate questions that are specific, meaningful, and retrieval-optimized.
- Each question must be on its own line.
- Number each question like: 1. Question here
- Do NOT repeat ideas across questions.
- Questions should cover different angles: definitions, comparisons, processes, examples, and implications."""


@lru_cache(maxsize=1)
def _get_client():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def _invoke_model(model_id: str, body: dict[str, Any]) -> dict[str, Any]:
    response = _get_client().invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    return json.loads(response["body"].read())


def _invoke_mistral(
    prompt: str,
    *,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    system: str | None = None,
) -> str:
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({
            "role": "system",
            "content": [{"type": "text", "text": system}],
        })
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": prompt}],
    })

    body: dict[str, Any] = {
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }

    try:
        data = _invoke_model(BEDROCK_MODEL_ID, body)
    except Exception as e:
        logger.exception("Error invoking Bedrock model: %s", e)
        return "Bedrock request failed."

    choices = data.get("choices") or []
    if choices and isinstance(choices, list):
        text = choices[0].get("message", {}).get("content")
        if isinstance(text, str):
            return text.strip()

    logger.error("Unexpected Bedrock response format: %s", data)
    return "Unexpected Bedrock response format."


def summarize_text(text: str, max_tokens: int = 1024) -> str:
    if not text.strip():
        return ""

    prompt = f"Process the following text and return the structured JSON metadata:\n\n{text}"
    return _invoke_mistral(prompt, system=SUMMARIZE_SYSTEM_PROMPT, max_tokens=max_tokens)


def answer_question(
    question: str,
    context: str | None = None,
    max_tokens: int = 1024,
) -> str:
    if context:
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
        system = ANSWER_SYSTEM_PROMPT
    else:
        prompt = f"Question: {question}\n\nAnswer:"
        system = ANSWER_NO_CONTEXT_SYSTEM_PROMPT

    return _invoke_mistral(prompt, system=system, max_tokens=max_tokens)


def generate_questions(text: str, count: int = 5) -> list[str]:
    if not text.strip() or count <= 0:
        return []

    prompt = (
        f"Generate exactly {count} retrieval-optimized follow-up questions "
        f"for the following text:\n\nText:\n{text}"
    )
    raw = _invoke_mistral(prompt, system=QUESTIONS_SYSTEM_PROMPT, max_tokens=512)

    questions: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        for prefix in ("- ", "* "):
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        if line and line[0].isdigit():
            rest = line.lstrip("0123456789")
            if rest.startswith(". ") or rest.startswith(") "):
                line = rest[2:].strip()
        if line:
            questions.append(line)
        if len(questions) >= count:
            break

    if not questions:
        logger.warning("generate_questions: could not parse model output, returning raw.")
        return [raw]

    return questions


def embed_text(text: str) -> list[float]:
    if not text.strip():
        return []

    if not BEDROCK_EMBEDDING_MODEL_ID:
        logger.warning("BEDROCK_EMBEDDING_MODEL_ID is not set.")
        return []

    body: dict[str, Any] = {"inputText": text}

    try:
        data = _invoke_model(BEDROCK_EMBEDDING_MODEL_ID, body)
        embedding = data.get("embedding") or []
        if isinstance(embedding, list):
            return [float(x) for x in embedding]
        logger.error("Unexpected embedding response format: %s", data)
        return []
    except Exception as e:
        logger.exception("Error invoking embedding model: %s", e)
        return []