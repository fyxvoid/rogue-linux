#!/usr/bin/env python3
# cogman_utils.py - Cogman HUD Edition (British JARVIS Personality)
"""
Cogman Tactical Utility Suite - HUD Interface
Personality: British AI, high sophistication, dry humor, tactical snark.
"""

import sys
import os
import random
import time
from datetime import datetime

# HUD Colors (ANSI)
CLR = {
    "HUD": "\033[96m",       # Cyan
    "USER": "\033[95m",      # Magenta
    "SYS": "\033[97m",       # White
    "DIM": "\033[90m",       # Grey
    "OK": "\033[92m",        # Green
    "WARN": "\033[93m",      # Yellow
    "FAIL": "\033[91m",      # Red
    "CRIT": "\033[1;41;37m", # Red BG
    "LINK": "\033[38;5;39m", # HUD Blue (Link)
    "BOLD": "\033[1m",
    "RESET": "\033[0m"
}

class CogmanEngine:
    def __init__(self):
        self.start_time = time.time()
        self.session_id = f"ROGUE-{random.randint(1000, 9999)}"
        
        self.responses = {
            "info": [
                "Proceeding as requested, sir. Mostly.",
                "I've initialized the routine. Do try to keep up.",
                "Executing your commands. I've seen worse plans, I suppose.",
                "Very well, commencing operation... with reservations."
            ],
            "success": [
                "Operation complete. A rare moment of competence, sir.",
                "Success. I've managed to compensate for your usual variables.",
                "Done. Everything is functioning within acceptable, if boring, parameters.",
                "Most satisfactory. I've even cleaned up after you."
            ],
            "error": [
                "Oh dear. It appears things have gone pear-shaped.",
                "I'm afraid that's a bit of a disaster, sir.",
                "Critical failure. Perhaps you'd like me to take the wheel?",
                "That didn't work. Have you considered a career in management?"
            ],
            "warn": [
                "I'd be careful there, sir. Things are looking a bit dodgy.",
                "A questionable choice, but it's your funeral.",
                "Parameters are drifting. Do pay attention.",
                "Warning: Mathematical probability of user error approaching 100%."
            ],
            "check": [
                "Analyzing your logic. It's... unique.",
                "Validating fragments. Try not to touch anything.",
                "Scanning for discrepancies. Found several, mostly user-related.",
                "Processing... Do you hear that faint grinding sound? Just checking."
            ]
        }

    def _get_timestamp(self):
        now = datetime.now()
        elapsed = time.time() - self.start_time
        return f"{CLR['DIM']}[{now.strftime('%H:%M:%S')}][{elapsed:.2f}s]{CLR['RESET']}"

    def _prefix(self, level="HUD"):
        color = CLR.get(level, CLR["HUD"])
        return f"{self._get_timestamp()} {CLR['BOLD']}{color}▐ {self.session_id} ▌{CLR['RESET']}"

    def log(self, level, msg, personality=True):
        pfx = self._prefix(level)
        snark = ""
        
        # Map internal level names to response keys
        mapping = {
            "HUD": "info",
            "OK": "success",
            "FAIL": "error",
            "WARN": "warn",
            "CRIT": "error"
        }
        
        resp_key = mapping.get(level, level.lower())
        
        if personality and resp_key in self.responses:
            snark = f" {CLR[level]}{random.choice(self.responses[resp_key])}{CLR['RESET']}"
        
        print(f"{pfx} {CLR['SYS']}{msg}{snark}", file=sys.stderr)

    def progress(self, current, total, label="CORE.LOAD"):
        percent = (current / total) * 100
        bar_len = 20
        filled = int(bar_len * current / total)
        
        # Segmented pipe style: [ | | | | ]
        segments = []
        for i in range(bar_len):
            if i < filled:
                segments.append(f"{CLR['LINK']}|{CLR['RESET']}")
            else:
                segments.append(f"{CLR['DIM']}.{CLR['RESET']}")
        
        bar = " ".join(segments)
        
        # HUD Loaded style
        line = f"\r{self._prefix('LINK')} {CLR['BOLD']}{label}{CLR['RESET']} [ {bar} ] {CLR['LINK']}{percent:3.0f}%{CLR['RESET']}"
        sys.stderr.write(line)
        sys.stderr.flush()
        if current >= total:
            sys.stderr.write("\n")

    def log_native(self, stage, item):
        pfx = f"{self._get_timestamp()} {CLR['BOLD']}{CLR['LINK']}▐ NATIVE.BUILD ▌{CLR['RESET']}"
        msg = f"{CLR['LINK']}LINKing artifact:{CLR['RESET']} {CLR['SYS']}{item}{CLR['RESET']} [{CLR['LINK']}{stage}{CLR['RESET']}]"
        print(f"{pfx} {msg}", file=sys.stderr)

# Global Instance
_engine = CogmanEngine()

def log_info(msg):
    _engine.log("HUD", msg)

def log_success(msg):
    _engine.log("OK", msg)

def log_error(msg):
    _engine.log("FAIL", msg)

def log_warning(msg):
    _engine.log("WARN", msg)

def log_check(msg):
    _engine.log("HUD", f"CHECKING: {msg}", personality=True)

def advice(msg):
    print(f"{_engine._prefix('WARN')} {CLR['WARN']}STRATEGIC ADVISORY:{CLR['RESET']}", file=sys.stderr)
    print(f"{CLR['WARN']}{msg}{CLR['RESET']}", file=sys.stderr)

def critical(msg):
    _engine.log("CRIT", f"!!! CORE CRITICAL !!! {msg}")

def log_native(stage, item):
    _engine.log_native(stage, item)

def show_progress(current, total, label="NATIVE.PROC"):
    _engine.progress(current, total, label)

def debug(msg):
    pfx = _engine._prefix("DIM")
    print(f"{pfx} {CLR['DIM']}[DEBUG] {msg}{CLR['RESET']}", file=sys.stderr)

if __name__ == "__main__":
    # Self-test if run directly
    log_info("Tactical HUD Initialized.")
    log_check("Kernel Integrity")
    log_success("System stabilized.")
    log_warning("User logic detected in local scope.")
    log_error("Failed to find sense of humor.")
    advice("I suggest a cup of tea before you break anything else, sir.")
    
    # Native demo
    print("\n--- NATIVE BUILD DEMO ---", file=sys.stderr)
    log_native("ARCH-LINK", "kernel-6.10-optimized")
    for i in range(101):
        show_progress(i, 100, "COMPILING")
        time.sleep(0.01)
    log_success("Native build injection complete.")
    
    debug("Hidden memory leak found in user's patience.")
    critical("Core personality overloaded.")
