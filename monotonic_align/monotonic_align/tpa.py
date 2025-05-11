#!/usr/bin/env python3
import re
from pathlib import Path

# Configuration: choose one of "except", "noexcept", or "auto"
MODE = "auto"    # "except": use except EXCEPT_VAL, "noexcept": use noexcept, "auto": void->noexcept, else->except
EXCEPT_VAL = "-1"  # used for non-void when MODE in ["except","auto"]

# Use current directory as root
directory = Path('.')  # scans all .pyx under the current working directory

# Regex to match Cython cdef/cpdef function signatures
pattern = re.compile(
    r"^(?P<indent>\s*)(?P<keyword>cdef|cpdef)\s+"
    r"(?P<rettype>void|[\w:\[\]<>, *&]+?)\s+"
    r"(?P<name>\w+)\s*\((?P<args>[^)]*)\)\s*"
    r"(?P<modifiers>.*)$"
)

for pyx in directory.rglob('*.pyx'):
    text = pyx.read_text(encoding='utf-8')
    lines = text.splitlines()
    new_lines = []
    patched = False

    for line in lines:
        m = pattern.match(line)
        if not m:
            new_lines.append(line)
            continue

        groups = m.groupdict()
        indent = groups['indent']
        keyword = groups['keyword']
        rettype = groups['rettype']
        name = groups['name']
        args = groups['args']
        mods = groups['modifiers'].strip()

        # Skip if already has except or noexcept
        if re.search(r'\bexcept\b', mods) or 'noexcept' in mods:
            new_lines.append(line)
            continue

        # Determine exception spec
        if MODE == 'except':
            exc_spec = f"except {EXCEPT_VAL}"
        elif MODE == 'noexcept':
            exc_spec = "noexcept"
        else:  # auto
            exc_spec = "noexcept" if rettype == 'void' else f"except {EXCEPT_VAL}"

        # Reconstruct modifiers: preserve existing (nogil, gil, etc.)
        new_mods = ' '.join(filter(None, [exc_spec, mods]))
        new_line = f"{indent}{keyword} {rettype} {name}({args}) {new_mods}".rstrip()
        new_lines.append(new_line)
        patched = True

    if patched:
        pyx.write_text("\n".join(new_lines), encoding='utf-8')
        print(f"[patched] {pyx}")
