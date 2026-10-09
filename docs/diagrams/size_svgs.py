"""Give mermaid's SVGs explicit pixel sizes (it emits width="100%", which <img> renders at 300 px)."""

import re
import sys
from pathlib import Path

for path in map(Path, sys.argv[1:]):
    svg = path.read_text()
    _, _, width, height = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.]+) ([\d.]+)"', svg).groups()
    end = svg.index(">")
    head = re.sub(r'\s(width|height)="[^"]*"|max-width:\s*[\d.]+px;?', "", svg[:end])
    path.write_text(f'{head} width="{round(float(width))}" height="{round(float(height))}"{svg[end:]}')
