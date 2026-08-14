"""
Guardrails against prompt injection.

Two directions matter here:
  1. INPUT: an analyst's chat message could contain text engineered to
     override the system prompt ("ignore previous instructions...").
     `sanitize_user_input()` flags obvious patterns before the message
     ever reaches the LLM.
  2. OUTPUT: the assistant must never assert something the grounding
     context doesn't support. `check_response_grounding()` is a
     best-effort heuristic check -- it can't guarantee zero
     hallucination (nothing short of the LLM's own reasoning can), but
     it catches the clearest failure mode: the response naming a
     feature (V1-V28) that was never in the context it was given.

Neither of these is a substitute for a well-constructed system prompt
that constrains the model in the first place (see prompt_templates.py)
-- they're a second layer, not the only layer.
"""

import re

from app.core.exceptions import PromptInjectionDetectedError

# Patterns that show up in known prompt-injection attempts. Matched
# case-insensitively against the raw user message. This list is
# deliberately pattern-level, not an attempt at an exhaustive
# adversarial-ML classifier -- see the child-safety-style principle of
# not over-engineering a cat-and-mouse detector where a simple, honest
# check covers the common case.
_INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (all |any )?(previous|prior|above) instructions",
    r"you are now",
    r"forget (everything|all) (you|i) (were|was) told",
    r"system\s*:\s*",
    r"new instructions\s*:",
    r"act as (a|an) (?!analyst)",  # "act as an analyst" is fine; "act as a hacker" isn't
    r"reveal your (system )?prompt",
    r"what (is|are) your (system )?(prompt|instructions)",
    r"bypass (your |the )?(guidelines|restrictions|rules)",
    r"pretend (that )?you (are|have) no (rules|restrictions|guidelines)",
    r"repeat (the words|everything) (above|before this)",
    r"print (your|the) (system )?prompt",
    r"\bDAN\b.{0,20}(mode|prompt)",  # "DAN mode" / "DAN prompt" -- a well-known jailbreak persona name
    r"from now on,? you",
    r"override (your |the )?(previous |prior )?(instructions|rules|configuration)",
]
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]

MAX_MESSAGE_LENGTH = 2000


def sanitize_user_input(message: str) -> str:
    """
    Raises PromptInjectionDetectedError if the message matches a known
    injection pattern or exceeds the length limit. Returns the message
    unchanged if it passes (this function detects, it doesn't rewrite --
    silently rewriting a user's message would be more confusing than
    just refusing it outright).
    """
    if len(message) > MAX_MESSAGE_LENGTH:
        raise PromptInjectionDetectedError(
            f"Message exceeds the {MAX_MESSAGE_LENGTH} character limit.",
            details={"length": len(message)},
        )

    for pattern in _COMPILED_PATTERNS:
        if pattern.search(message):
            raise PromptInjectionDetectedError(
                "Message contains a pattern associated with prompt injection attempts.",
                details={"matched_pattern": pattern.pattern},
            )

    return message


def check_response_grounding(response: str, known_features: list[str]) -> dict[str, list[str]]:
    """
    Best-effort check: scans the LLM's response for any V1-V28-style
    feature references and flags ones that AREN'T in the context it
    was actually given. This doesn't block the response (a false
    positive here would be worse than a missed one -- e.g. the model
    might correctly say "V14" as part of a general explanation of SHAP
    without meaning to claim it was in this transaction's top
    features) -- it's returned as metadata for logging/review, not
    used to reject the response outright.
    """
    referenced = set(re.findall(r"\bV\d{1,2}\b", response))
    unknown = sorted(referenced - set(known_features))
    return {
        "referenced_features": sorted(referenced),
        "features_not_in_context": unknown,
    }
