"""Compact raw evidence for the public repository; extract at project root."""
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
with tarfile.open(ROOT / 'output/experiment_evidence.tar.gz', 'w:gz', compresslevel=9) as archive:
    for name in ['data', 'results']:
        for p in sorted((ROOT / name).rglob('*')):
            if p.is_file() and p.name != '.run.lock':
                archive.add(p, arcname=p.relative_to(ROOT).as_posix(), recursive=False)
print((ROOT / 'output/experiment_evidence.tar.gz').stat().st_size)
