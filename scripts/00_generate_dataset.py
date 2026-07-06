"""
Stage 0: Dataset generation.

Reads intent definitions from intents.py, calls Gemini to fabricate
realistic customer support messages for each intent, and writes the
result to conversations.jsonl.

Each output row:
{
  "text": "the customer's opening message",
  "true_intent": "billing_charges",           # ground truth, for evaluation later
  "was_resolved_by_fin": true|false           # probabilistic based on intent's resolution_rate
}
"""

import json
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from intents import INTENTS

# ─── Config ─────────────────────────────────────────────────
MODEL_NAME = "gemini-2.5-flash"
MESSAGES_PER_INTENT = 50  # ~900 total across 18 intents
OUTPUT_FILE = "conversations.jsonl"
SEED = 42                 # for reproducible resolved/unresolved assignment


# ─── Prompt template ─────────────────────────────────────────
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


def build_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment.")
    return genai.Client(api_key=api_key)


def generate_for_intent(client, intent, n=MESSAGES_PER_INTENT):
    """Ask Gemini for n messages for one intent. Returns list of strings."""
    prompt = GENERATION_PROMPT.format(
        n=n,
        intent_name=intent["name"],
        description=intent["description"],
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    lines = [ln.strip() for ln in response.text.strip().splitlines() if ln.strip()]
    return lines


def assign_resolution(intent, rng):
    """Probabilistically mark this conversation as resolved-by-Fin."""
    return rng.random() * 100 < intent["resolution_rate"]


def main():
    client = build_client()
    rng = random.Random(SEED)
    output_path = Path(OUTPUT_FILE)

    total_written = 0
    with output_path.open("w") as f:
        for intent in INTENTS:
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
                total_written += 1

            print(f"got {len(messages)} messages")
            time.sleep(1)  # be polite to the API

    print(f"\nDone. Wrote {total_written} conversations to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()