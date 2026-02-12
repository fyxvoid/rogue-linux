import os

packages = [
    "packages/toolchain/gcc/gcc.toml",
    "packages/toolchain/glibc/glibc.toml",
    "packages/toolchain/binutils/binutils.toml",
    "packages/toolchain/gmp/gmp.toml",
    "packages/toolchain/mpfr/mpfr.toml",
    "packages/toolchain/mpc/mpc.toml",
    "packages/toolchain/linux-headers/linux-headers.toml",
    "packages/system/zlib/zlib.toml",
    "packages/base/ncurses/ncurses.toml",
    "packages/base/readline/readline.toml",
    "packages/base/bash/bash.toml"
]

def safe_dummyfy(path):
    if not os.path.exists(path):
        return
    with open(path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = False
    
    # Sections to keep identity/depends but empty out steps
    # We want to keep anything until [build], then inject empty build,
    # skip until [installer], inject empty installer,
    # skip until next section like [policy].
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[build]'):
            new_lines.append('[build]\n')
            new_lines.append('system = "make"\n')
            new_lines.append('steps = ["echo \'Dummy step\'"]\n')
            skip = True
            continue
        if stripped.startswith('[installer]'):
            new_lines.append('[installer]\n')
            new_lines.append('steps = ["echo \'Dummy step\'"]\n')
            skip = True
            continue
        if stripped.startswith('[installer.verify]'):
            skip = True
            continue
        if stripped.startswith('[policy]') or stripped.startswith('[identity]') or stripped.startswith('[identity.source]') or stripped.startswith('[identity.depends]'):
            skip = False
        
        if not skip:
            new_lines.append(line)
            
    with open(path, 'w') as f:
        f.writelines(new_lines)
    print(f"Safe dummy-fied {path}")

for p in packages:
    safe_dummyfy(p)
