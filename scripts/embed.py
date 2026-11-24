"""Embed data/players.json and data/sample_overs.json into index.html (between the /*PLAYERS*/ and /*OVERS*/ markers)."""
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
html = (root / "index.html").read_text()
for key, fname in (("PLAYERS", "players.json"), ("OVERS", "sample_overs.json")):
    data = (root / "data" / fname).read_text().strip()
    html, n = re.subn(rf"/\*{key}\*/.*?/\*END_{key}\*/", lambda m: f"/*{key}*/{data}/*END_{key}*/", html, flags=re.S)
    assert n == 1, f"marker {key} not found"
(root / "index.html").write_text(html)
print("embedded", len(html) // 1024, "KB")
