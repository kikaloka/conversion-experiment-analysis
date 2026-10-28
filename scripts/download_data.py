"""Download the public source locally. Never overwrite a different original."""
from pathlib import Path
import hashlib, urllib.request, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.analysis import URL,SHA
p=ROOT/'data/original/ab_data.csv'
p.parent.mkdir(parents=True,exist_ok=True)
payload=p.read_bytes() if p.exists() else urllib.request.urlopen(URL,timeout=60).read()
assert hashlib.sha256(payload).hexdigest()==SHA,'Source differs from reviewed version'
if not p.exists(): p.write_bytes(payload)
print('Original source present and SHA-256 verified.')
