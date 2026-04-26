import re
from pathlib import Path

path = Path('templates/reference/Cisco_ADM.html')
if not path.exists():
    path = Path('templates/reference/ciscoADM.html')

html = path.read_text(encoding='utf-8')
ids = re.findall(r'id=["\'](section-[^"\']+)["\']', html)
print(f"Found {len(ids)} section IDs:")
for i in ids:
    print(f" - {i}")

buttons = re.findall(r'data-section-id=["\']([^"\']+)["\']', html)
print(f"\nFound {len(buttons)} data-section-id buttons:")
for b in buttons:
    print(f" - {b}")
