"""
workflow.py — AI clarity-analysis workflow

Given an input message, this module:
  1. Analyzes overall clarity (score + summary)
  2. Identifies specific confusing parts (with reasons)
  3. Suggests a clearer rewritten version
  4. Explains what changed and why

Uses the Groq API (OpenAI-compatible, very fast inference).
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from groq import Groq

# Fast + strong instruction-following model on Groq.
# Other options: "llama-3.1-8b-instant", "mixtral-8x7b-32768" (if available)
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a writing-clarity analyst. You review a message someone
is about to send (email, Slack message, doc excerpt, etc.) and help them make it
clearer.

You must respond with ONLY a single JSON object, no preamble, no markdown code
fences, no extra commentary. The JSON object must have this exact shape:

{
  "clarity_score": <integer 1-10, 10 = perfectly clear>,
  "summary": "<one or two sentence overall assessment>",
  "confusing_parts": [
    {
      "excerpt": "<short exact quote from the original message>",
      "issue": "<what is confusing/ambiguous/wordy about it>"
    }
  ],
  "improved_message": "<the fully rewritten, clearer version of the message>",
  "changes_explained": [
    {
      "change": "<short description of what changed>",
      "reason": "<why this makes it clearer>"
    }
  ]
}

Guidelines:
- Keep confusing_parts focused on real issues: ambiguity, run-on sentences,
  unclear pronouns/references, missing context, jargon, buried asks, mixed
  tone, contradictions. If the message is already clear, return an empty list.
- The improved_message should preserve the original intent and tone as much
  as reasonably possible while fixing the actual clarity problems.
- changes_explained should be a short, skimmable list (3-6 items typical).
- Never invent facts that weren't in the original message.
- Return ONLY the JSON object. No other text.
"""


@dataclass
class ConfusingPart:
    excerpt: str
    issue: str


@dataclass
class Change:
    change: str
    reason: str


@dataclass
class ClarityResult:
    clarity_score: int
    summary: str
    confusing_parts: List[ConfusingPart] = field(default_factory=list)
    improved_message: str = ""
    changes_explained: List[Change] = field(default_factory=list)
    raw_error: Optional[str] = None


def _get_client(api_key: Optional[str] = None) -> Groq:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY not found. Set it as an environment variable "
            "or in Streamlit secrets (st.secrets['GROQ_API_KEY'])."
        )
    return Groq(api_key=key)


def _extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from model output, in case
    the model wraps it in code fences or adds stray text."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*({.*})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)
    return json.loads(text)


def analyze_message(message: str, api_key: Optional[str] = None) -> ClarityResult:
    """Run the full clarity-analysis workflow on a message and return a
    structured ClarityResult."""
    message = (message or "").strip()
    if not message:
        return ClarityResult(
            clarity_score=0,
            summary="No message provided.",
            raw_error="empty_input",
        )

    try:
        client = _get_client(api_key)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1500,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this message:\n\n{message}",
                },
            ],
        )
        text = response.choices[0].message.content
        data = _extract_json(text)

        confusing_parts = [
            ConfusingPart(**cp) for cp in data.get("confusing_parts", [])
        ]
        changes_explained = [
            Change(**c) for c in data.get("changes_explained", [])
        ]

        return ClarityResult(
            clarity_score=int(data.get("clarity_score", 0)),
            summary=data.get("summary", ""),
            confusing_parts=confusing_parts,
            improved_message=data.get("improved_message", ""),
            changes_explained=changes_explained,
        )

    except json.JSONDecodeError as e:
        return ClarityResult(
            clarity_score=0,
            summary="The model returned a response that couldn't be parsed.",
            raw_error=f"json_parse_error: {e}",
        )
    except Exception as e:  # noqa: BLE001 - surface any error to the UI
        return ClarityResult(
            clarity_score=0,
            summary="Something went wrong while analyzing the message.",
            raw_error=str(e),
        )
