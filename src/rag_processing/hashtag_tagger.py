from transformers import pipeline
from loguru import logger
from datetime import datetime

from src.rag_processing.rag_config import HASHTAG_TAGGER_MODEL

_SYSTEM_PROMPT = (
    "You are a content tagger. Given a text excerpt, output 3-7 single-word hashtags "
    "that describe its domain and main topics. Output ONLY hashtags like #medical #legal, "
    "nothing else."
)


def get_hashtag_tagger():
    logger.info(f"Loading hashtag tagger: {HASHTAG_TAGGER_MODEL}")
    tagger = pipeline(
        "text-generation",
        model=HASHTAG_TAGGER_MODEL,
        device="cpu",
        torch_dtype="auto",
    )
    logger.info("Hashtag tagger loaded")
    return tagger


def tag_chunk(text: str) -> list[str]:
    logger.debug(f"Tagging chunk: {text[:100]!r}...")
    start_time = datetime.now()
    from app.core import GlobalDeps

    tagger = GlobalDeps.hashtag_tagger
    if tagger is None:
        return []

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": text[:600]},
    ]

    output = tagger(messages, max_new_tokens=40, do_sample=False)
    raw = output[0]["generated_text"][-1]["content"]

    words = raw.strip().split()
    hashtags = [w if w.startswith("#") else f"#{w}" for w in words if w.strip("#,. ")]
    logger.debug(f"Tagging completed in {(datetime.now() - start_time).total_seconds():.2f}s | hashtags={hashtags}")
    return hashtags[:7]
