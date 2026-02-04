import sys

# ─────────────────────────────────────────────
# ANSI styling
# ─────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"

BLUE   = "\033[94m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"


def _prefix():
    # Cogman always announces himself properly
    return f"{BLUE}{BOLD}▐ COGMAN ▌{RESET}"


# ─────────────────────────────────────────────
# Cogman’s voice — British, dry, politely amused
# ─────────────────────────────────────────────
def info(message: str):
    """
    Neutral operational statement.
    """
    sys.stdout.write(
        f"{_prefix()} {WHITE}{message}, sir.{RESET}\n"
    )
    sys.stdout.flush()


def ok(message: str):
    """
    Successful outcome.
    """
    sys.stdout.write(
        f"{_prefix()} {GREEN}{message}. Quite satisfactory, sir.{RESET}\n"
    )
    sys.stdout.flush()


def warn(message: str):
    """
    Non-fatal concern.
    """
    sys.stdout.write(
        f"{_prefix()} {YELLOW}{message}. One raises an eyebrow, sir.{RESET}\n"
    )
    sys.stdout.flush()


def err(message: str):
    """
    Fatal or serious error.
    """
    sys.stderr.write(
        f"{_prefix()} {RED}{message}. Deeply unfortunate, sir.{RESET}\n"
    )
    sys.stderr.flush()
