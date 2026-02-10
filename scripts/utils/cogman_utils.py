#!/usr/bin/env python3
# cogman_utils.py - Butler personality for Python scripts

import sys

BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"
WHITE = "\033[97m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"

def prefix():
    return f"{BLUE}{BOLD}\u2590 COGMAN \u258c{RESET}"

def log_info(msg):
    print(f"{prefix()} {WHITE}{msg}, sir.{RESET}", file=sys.stderr)

def log_success(msg):
    print(f"{prefix()} {GREEN}{msg}, sir. Most satisfactory.{RESET}", file=sys.stderr)

def log_error(msg):
    print(f"{prefix()} {RED}{msg}, sir. I am afraid this is rather unfortunate.{RESET}", file=sys.stderr)

def log_check(msg):
    print(f"{prefix()} {BLUE}Checking {msg}, sir...{RESET}", file=sys.stderr)

def advice(msg):
    print(f"{prefix()} {YELLOW}I have taken the liberty of analyzing the situation:{RESET}", file=sys.stderr)
    print(f"{YELLOW}{msg}{RESET}", file=sys.stderr)
