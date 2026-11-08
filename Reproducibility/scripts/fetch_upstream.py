"""Fetch the exact public upstream archive and verify its commit marker."""
import json
from pathlib import Path
import urllib.request
import zipfile
root = Path(__file__).resolve().parents[1]
sha = json.loads((root / 'configs/experiment.json').read_text())['upstream_commit']
target = root / 'upstream/ace-main'
if target.exists():
    raise SystemExit('Upstream exists; refusing to overwrite it.')
archive = root / 'upstream' / (sha + '.zip')
archive.parent.mkdir(exist_ok=True)
urllib.request.urlretrieve('https://codeload.github.com/ace-agent/ace/zip/' + sha, archive)
with zipfile.ZipFile(archive) as z:
    if z.comment.decode() != sha:
        raise RuntimeError('Unexpected upstream commit')
    for item in z.infolist():
        if not (archive.parent / item.filename).resolve().is_relative_to(archive.parent.resolve()):
            raise RuntimeError('Archive path escapes upstream directory')
    z.extractall(archive.parent)
(archive.parent / ('ace-' + sha)).rename(target)
print('Fetched pinned ACE source:', sha)
