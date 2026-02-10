import os
import re
import sys

# Allow importing from scripts/ directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts")))
import cogman_utils as butler

PUBLIC_DIR = "website/public"

def audit_file(filepath):
    issues = []
    with open(filepath, "r") as f:
        content = f.read()

    # 1. Check for broken internal links (simple check)
    links = re.findall(r'href=["\'](.*?)["\']', content)
    for link in links:
        if link.startswith("http"): continue
        if link.startswith("#"): continue
        if link.startswith("mailto:"): continue
        
        # Resolve path
        if link.startswith("/"):
            target = os.path.join(PUBLIC_DIR, link.lstrip("/"))
        else:
            target = os.path.join(os.path.dirname(filepath), link)
            
        if not os.path.exists(target):
            issues.append(f"Broken Link: {link}")

    # 2. Check for insecure external links
    http_links = re.findall(r'href=["\']http://.*?["\']', content)
    for link in http_links:
        issues.append(f"Insecure Link: {link}")

    # 3. Check for target=_blank without noopener
    unsafe_targets = re.findall(r'<a[^>]+target=["\']_blank["\'][^>]*>', content)
    for tag in unsafe_targets:
        if "rel=" not in tag or "noopener" not in tag:
            issues.append(f"Unsafe Target Blank: {tag}")

    return issues

def main():
    butler.log_info("Starting security and integrity audit...")
    total_issues = 0
    
    for root, _, files in os.walk(PUBLIC_DIR):
        for file in files:
            if not file.endswith(".html"): continue
            path = os.path.join(root, file)
            issues = audit_file(path)
            
            if issues:
                butler.log_error(f"Issues in {file}:")
                for issue in issues:
                    print(f"  - {issue}")
                total_issues += len(issues)
            else:
                butler.log_check(f"Verified {file}")

    if total_issues == 0:
        butler.log_success("Audit complete. Zero vulnerabilities found.")
    else:
        butler.log_error(f"Audit complete. {total_issues} issues found.")

if __name__ == "__main__":
    main()
