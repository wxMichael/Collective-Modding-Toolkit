"""Convert a CHANGELOG.md version section into flat Nexus changelog lines.

Each bullet becomes one line prefixed by its headers, e.g. "Removed: Scanner: Complex Sorter ...".
Usage: nexus_changelog.py <release-notes.md>  (writes to stdout)
"""

import re
import sys
from pathlib import Path

entries: list[str] = []
section = ""
subsection = ""
last_is_entry = False

for raw in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
	line = raw.rstrip()
	if not line.strip():
		last_is_entry = False
		continue

	if m := re.match(r"^###\s+(.+)$", line):
		section, subsection, last_is_entry = m.group(1).strip(), "", False
	elif m := re.match(r"^(?:-\s+)?####\s+(.+)$", line):
		subsection, last_is_entry = m.group(1).strip(), False
	elif m := re.match(r"^(\s*)[-*]\s+(.+)$", line):
		indent, text = len(m.group(1)), m.group(2).strip()
		if indent == 0:
			subsection = ""
		prefix = ": ".join(p for p in (section, subsection) if p)
		entries.append(f"{prefix}: {text}" if prefix else text)
		last_is_entry = True
	elif last_is_entry:  # wrapped continuation of the previous bullet
		entries[-1] += " " + line.strip()

print("\n".join(entries))
