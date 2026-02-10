"""
Generates 100+ synthetic Linux Command Q&A pairs for training/testing.
"""
import json
import random

COMMANDS = [
    ("ls", "list directory contents", ["-l", "-a", "-h", "-R"]),
    ("grep", "print lines that match patterns", ["-i", "-v", "-r", "-n"]),
    ("chmod", "change file mode bits", ["+x", "777", "644", "-R"]),
    ("chown", "change file owner and group", ["user:group", "-R"]),
    ("ps", "report a snapshot of the current processes", ["aux", "-ef"]),
    ("top", "display Linux processes", ["-b", "-n 1"]),
    ("kill", "send a signal to a process", ["-9", "-15"]),
    ("tar", "an archiving utility", ["-czvf", "-xzvf", "-tjvf"]),
    ("find", "search for files in a directory hierarchy", ["-name", "-type f", "--mtime"]),
    ("netstat", "print network connections", ["-tuln", "-pan"]),
    ("ss", "another utility to investigate sockets", ["-tuln", "-pl"]),
    ("iptables", "administration tool for IPv4 packet filtering and NAT", ["-L", "-A INPUT", "-F"]),
    ("systemctl", "Control the systemd system and service manager", ["start", "stop", "status", "enable"]),
    ("journalctl", "Query the systemd journal", ["-xe", "-u ssh", "-f"]),
    ("ip", "show / manipulate routing, network devices, interfaces", ["address show", "link set up", "route"]),
]

TEMPLATES = [
    "How do I use `{cmd}` to {desc}?",
    "Explain the usage of `{cmd}` command.",
    "What is the command to {desc} using `{cmd}`?",
    "I need to {desc}. Which tool should I use?",
    "Show me examples of `{cmd}`."
]

def generate_dataset():
    data = []
    
    # Generate per command
    for cmd, desc, flags in COMMANDS:
        # Base concept
        data.append({
            "instruction": f"Explain the purpose of the `{cmd}` command.",
            "input": "",
            "output": f"The `{cmd}` command is used to {desc}. It is a fundamental tool for Linux system administration."
        })
        
        # Flag variations
        for flag in flags:
            data.append({
                "instruction": f"How do I run `{cmd}` with the `{flag}` option?",
                "input": "",
                "output": f"You can run: `{cmd} {flag} <args>`. This modifies the behavior to include specific functionality related to {desc}."
            })
            
    # Mix and match for scale
    while len(data) < 120:
        cmd, desc, flags = random.choice(COMMANDS)
        template = random.choice(TEMPLATES)
        
        question = template.format(cmd=cmd, desc=desc)
        flag_str = " ".join(random.sample(flags, k=min(2, len(flags))))
        
        answer = (f"To {desc}, you can use `{cmd}`.\n"
                  f"Common flags include `{flag_str}`.\n"
                  f"Example: `{cmd} {flag_str} [arguments]`")
        
        data.append({
            "instruction": question,
            "input": "",
            "output": answer
        })

    return data

if __name__ == "__main__":
    dataset = generate_dataset()
    output_path = "training/data/debug_data_100.json"
    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"[+] Generated {len(dataset)} examples > {output_path}")
