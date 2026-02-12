"""
cogman/src/advisor/training/scripts/collect_data.py - Data Collection Pipeline

This script automates the scraping and formatting of man pages and 
system documentation for fine-tuning the Cogman AI.

Why: To build the knowledge base required for the AI Advisor to 
understand Rogue Linux internals.
"""
import os
import subprocess
import urllib.request
from pathlib import Path

DATA_DIR = Path("training/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def collect_man_pages():
    """Converts local man pages to text for training."""
    print("[*] Collecting Man Pages...")
    output_file = DATA_DIR / "man_pages.txt"
    
    man_path = Path("/usr/share/man/man1")
    count = 0
    
    if not man_path.exists():
        print("[-] /usr/share/man/man1 not found. Skipping local man collection.")
        return

    with open(output_file, "w", encoding="utf-8") as out:
        for f in man_path.glob("*.gz"):
            try:
                # zcat the man page | groff -Tutf8 -man
                cmd = f"zcat {f} | groff -Tutf8 -man"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    out.write(f"--- START MAN PAGE: {f.name} ---\n")
                    out.write(result.stdout)
                    out.write(f"--- END MAN PAGE ---\n\n")
                    count += 1
            except Exception as e:
                print(f"[-] Error processing {f}: {e}")
                
    print(f"[+] Processed {count} man pages.")

def fetch_online_resources():
    """Downloads real Linux documentation and guides."""
    print("[*] Downloading Online Documentation...")
    
    sources = {
        "linux_command_guide.txt": "https://tldp.org/LDP/abs/html/abs-guide.html", # Mock URL for example, using a reliable text source would be better
        "rogue_kernel_design.txt": "https://www.kernel.org/doc/html/latest/_sources/process/1.Intro.rst.txt",
        "basic_pentesting.txt": "https://raw.githubusercontent.com/enaqx/awesome-pentest/master/README.md"
    }

    for filename, url in sources.items():
        print(f"  - Fetching {filename} from {url}...")
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8', errors='ignore')
                with open(DATA_DIR / filename, "w") as f:
                    f.write(f"--- SOURCE: {url} ---\n")
                    f.write(content)
        except Exception as e:
            print(f"  [-] Failed to fetch {url}: {e}")

    print("[+] Online resources downloaded.")

if __name__ == "__main__":
    collect_man_pages()
    fetch_online_resources()
