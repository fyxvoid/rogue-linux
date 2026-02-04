from core.log.voice import info
from core.personality.cogman import CogmanPersonality


def ask_once(question: str, *, default: bool = True) -> bool:
    """
    Ask a single, restrained question.

    Rules:
    - Asked only when authorised by personality
    - Asked once
    - Default assumed on empty input
    """

    if not CogmanPersonality.may_ask_question("destructive"):
        return default

    suffix = "[Y/n]" if default else "[y/N]"
    info(f"{question} {suffix}")

    try:
        reply = input("> ").strip().lower()
    except EOFError:
        return default

    if not reply:
        return default

    return reply in ("y", "yes")
