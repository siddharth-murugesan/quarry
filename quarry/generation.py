"""Stage 0: Synthesize customer support conversations for each intent."""

import json
import os
import random
import time
from typing import Iterable

from dotenv import load_dotenv
from google import genai

from quarry.intents import INTENTS
from quarry.paths import CONVERSATIONS, ensure_dirs

MODEL_NAME = "gemini-2.5-flash"
MESSAGES_PER_INTENT = 50
SEED = 42

GENERATION_PROMPT = """You are generating realistic customer support messages for Meridian, a mid-market SaaS project management tool (similar in shape to Asana or Monday.com).

Generate exactly {n} distinct opening messages that customers might send to support, all about the following underlying issue:

INTENT: {intent_name}
DESCRIPTION: {description}

Requirements for variety:
- Vary length: some 1 sentence, some 3-4 sentences.
- Vary tone: some polite, some frustrated, some terse, some rambling.
- Vary phrasing significantly — do not repeat the same sentence structure.
- Include some with typos or informal writing (like a real support inbox).
- A few should include specifics (fake names, fake IDs, fake dates) — do NOT use real people or companies.
- Do NOT number them, do NOT add commentary, do NOT include greetings like "Dear Support".
- Each message is ONE line only. Separate messages with a newline.
- Output ONLY the {n} messages, nothing else.

Begin:"""


def build_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment.")
    return genai.Client(api_key=api_key)


def generate_for_intent(
    client: genai.Client,
    intent: dict,
    n: int = MESSAGES_PER_INTENT,
) -> list[str]:
    prompt = GENERATION_PROMPT.format(
        n=n,
        intent_name=intent["name"],
        description=intent["description"],
    )
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return [ln.strip() for ln in response.text.strip().splitlines() if ln.strip()]


def assign_resolution(intent: dict, rng: random.Random) -> bool:
    return rng.random() * 100 < intent["resolution_rate"]


def generate_dataset(
    intents: Iterable[dict] = INTENTS,
    output_path=CONVERSATIONS,
) -> int:
    """Full dataset generation. Returns count of conversations written."""
    ensure_dirs()
    client = build_client()
    rng = random.Random(SEED)
    total = 0

    with output_path.open("w") as f:
        for intent in intents:
            print(f"→ {intent['id']:30s} ", end="", flush=True)
            try:
                messages = generate_for_intent(client, intent)
            except Exception as e:
                print(f"FAILED: {e}")
                continue

            for msg in messages:
                row = {
                    "text": msg,
                    "true_intent": intent["id"],
                    "was_resolved_by_fin": assign_resolution(intent, rng),
                }
                f.write(json.dumps(row) + "\n")
                total += 1

            print(f"got {len(messages)} messages")
            time.sleep(1)

    return total