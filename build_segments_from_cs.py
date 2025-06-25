#!/usr/bin/env python
"""
Użycie:
    python build_segments_from_cs.py packlib_original.cs
Tworzy segments_full.py z listą:
    SEGMENTS = [(kind, x0expr, y0expr, x1expr, y1expr), ...]
"""
import re, sys, pathlib, textwrap, pprint

if len(sys.argv) != 2 or not pathlib.Path(sys.argv[1]).exists():
    sys.exit("Podaj ścieżkę do pliku *.cs z listingiem PackLib")

SRC = pathlib.Path(sys.argv[1]).read_text(encoding="utf8")

kind_map = {'ltCut': 'CUT', 'ltFold': 'FOLD'}
segs, buf = [], {}

for line in SRC.splitlines():
    line = line.strip()
    if m := re.match(r'x([01])\s*=\s*(.+);', line):
        buf[f"x{m.group(1)}"] = m.group(2)
    elif m := re.match(r'y([01])\s*=\s*(.+);', line):
        buf[f"y{m.group(1)}"] = m.group(2)
    elif 'AddSegment' in line:
        kind = kind_map[ re.search(r'\((lt\w+),', line).group(1) ]
        segs.append((kind,
                     buf['x0'], buf['y0'],
                     buf['x1'], buf['y1']))
        buf.clear()

out = textwrap.dedent(f'''\
    # AUTO-GENERATED – nie edytuj ręcznie
    CUT, FOLD = "CUT", "FOLD"
    SEGMENTS = {pprint.pformat(segs, width=120)}
    ''')

path_out = pathlib.Path("segments_full.py")
path_out.write_text(out, encoding="utf8")
print(f"✓ zapisano {path_out}  ({len(segs)} segmenty, {path_out.stat().st_size//1024} KB)")
