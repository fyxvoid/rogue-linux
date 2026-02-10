#!/usr/bin/env python3
"""
Rogue Scanner: Privacy & Security Audit Tool
Scans codebase for telemetry, secrets, and suspicious patterns.
"""
import os
import re
import sys
import fnmatch

# Configuration
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules', '.gemini', 'build', 'dist'}
IGNORE_FILES = {'scan.py', 'package-lock.json', 'yarn.lock'}

# Patterns to hunt
PATTERNS = {
    "TELEMETRY": [
        r"analytics\.google\.com",
        r"sentry\.io",
        r"segment\.io",
        r"telemetry",
        r"track_event",
        r"log_analytics"
    ],
    "SECRETS": [
        r"AKIA[0-9A-Z]{16}",  # AWS Key
        r"AIza[0-9A-Za-z-_]{35}", # Google API Key
        r"ghp_[0-9a-zA-Z]{36}", # GitHub Token
        r"PRIVATE KEY-----",
        r"password\s*=\s*['\"][^'\"]+['\"]"
    ],
    "SUSPICIOUS": [
        r"eval\(",
        r"exec\(",
        r"base64\.b64decode",
        r"subprocess\.call.*curl",
        r"subprocess\.call.*wget",
        r"os\.system"
    ]
}

def scan_file(filepath):
    """Scans a single file for patterns."""
    issues = []
    try:
        with open(filepath, 'r', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                # Check all patterns
                for category, regexes in PATTERNS.items():
                    for regex in regexes:
                        if re.search(regex, line, re.IGNORECASE):
                            # Filter false positives (e.g., this scanner itself)
                            if "Rogue Scanner" in line or "PATTERNS =" in line:
                                continue
                                
                            issues.append({
                                "file": filepath,
                                "line": i,
                                "category": category,
                                "match": line.strip()[:100] # Truncate long lines
                            })
    except Exception as e:
        print(f"[-] Error reading {filepath}: {e}")
    return issues

def scan_directory(root_dir):
    """Recursively scans a directory."""
    all_issues = []
    print(f"[*] Starting Deep Scan of: {root_dir}")
    print(f"[*] Privacy Patterns Loaded: {sum(len(v) for v in PATTERNS.values())}")
    
    file_count = 0
    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            
            filepath = os.path.join(root, file)
            # Skip non-text files heavily (simple check)
            if not any(filepath.endswith(ext) for ext in ['.py', '.js', '.html', '.css', '.md', '.txt', '.sh', '.c', '.toml']):
                continue
                
            file_count += 1
            issues = scan_file(filepath)
            all_issues.extend(issues)
            
    print(f"[*] Scanned {file_count} files.")
    return all_issues

def report(issues):
    """Generates a human-readable report."""
    print("\n" + "="*60)
    print("ROGUE SCANNER: AUDIT REPORT")
    print("="*60)
    
    if not issues:
        print("\n[+] STATUS: CLEAN")
        print("[+] No telemetry, secrets, or malware patterns found.")
        print("[+] Privacy Integrity: 100%")
        return

    print(f"\n[-] STATUS: ALERT ({len(issues)} findings)")
    
    # Group by category
    by_cat = {}
    for i in issues:
        by_cat.setdefault(i['category'], []).append(i)
        
    for cat, items in by_cat.items():
        print(f"\n[{cat}]")
        for item in items:
            print(f"  - {item['file']}:{item['line']}")
            print(f"    Code: {item['match']}")

    print("\n" + "="*60)
    print("ACTION REQUIRED: Review findings manually.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "."
        
    findings = scan_directory(target)
    report(findings)
