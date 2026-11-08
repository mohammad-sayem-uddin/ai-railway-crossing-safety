#!/usr/bin/env python3
"""Read-only integrity check of this package; never runs research or source code."""
from pathlib import Path
from urllib.parse import unquote
import collections
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(name):
    path = ROOT / name
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Nonlocal or symbolic artifact: {name}")
    return path


def verify():
    index = {}
    for line in (ROOT / 'PACKAGE_FILES.sha256').read_text().splitlines():
        value, name = line.split('  ', 1)
        if not re.fullmatch(r'[a-f0-9]{64}', value) or name in index:
            raise ValueError('Invalid or repeated checksum index entry')
        index[name] = value
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()}
    if actual != set(index) | {'PACKAGE_FILES.sha256'}:
        raise ValueError('Missing or extra packaged files')
    for name, value in index.items():
        if digest(inside(name)) != value:
            raise ValueError(f'Checksum mismatch: {name}')
    with (ROOT / 'EVIDENCE_MANIFEST.csv').open(newline='') as stream:
        manifest = list(csv.DictReader(stream))
    names = [r['package_location'] for r in manifest]
    if len(set(names)) != len(names) or set(names) != set(index) - {'EVIDENCE_MANIFEST.csv'}:
        raise ValueError('Manifest coverage differs from checksum inventory')
    for row in manifest:
        if digest(inside(row['package_location'])) != row['sha256']:
            raise ValueError('Manifest identity mismatch')
        if row['artifact_kind'] == 'COPIED_ORIGINAL' and row['sha256'] != row['original_sha256']:
            raise ValueError('Original copy differs from recorded source identity')
        if not all(row.values()):
            raise ValueError('Missing manifest field')
    parsed = collections.Counter()
    for name in index:
        path = inside(name)
        if path.suffix == '.json':
            json.loads(path.read_text()); parsed['json'] += 1
        elif path.suffix == '.jsonl':
            for line in path.read_text().splitlines():
                if line.strip(): json.loads(line)
            parsed['jsonl'] += 1
        elif path.suffix == '.csv':
            rows = list(csv.reader(io.StringIO(path.read_text())))
            if not rows or len(set(rows[0])) != len(rows[0]) or any(len(r) != len(rows[0]) for r in rows):
                raise ValueError(f'Invalid CSV structure: {name}')
            parsed['csv'] += 1
        elif path.suffix == '.xml' or path.name.endswith('.xml.gz'):
            ET.fromstring(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())
            parsed['xml'] += 1
        elif path.suffix == '.gz':
            gzip.decompress(path.read_bytes()); parsed['other_gzip'] += 1
    links = 0
    for name in index:
        path = inside(name)
        if path.suffix != '.md' or '/originals/' in '/' + name or '/source_snapshot/' in '/' + name:
            continue
        for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', path.read_text()):
            target = target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            destination = (path.parent / unquote(target.split('#', 1)[0])).resolve()
            if not destination.is_relative_to(ROOT) or not destination.is_file():
                raise ValueError(f'Broken package link: {name}: {target}')
            links += 1
    source_map = json.loads((ROOT / '10_REPRODUCIBILITY/ARTIFACT_SOURCE_MAP.json').read_text())['originals']
    outcomes = collections.Counter()
    ids = []
    for source, name in source_map.items():
        if 'mission40/software_validation/groups/' not in source or not source.endswith('/pytest.xml.gz'):
            continue
        xml = ET.fromstring(gzip.decompress(inside(name).read_bytes()))
        for case in xml.iter('testcase'):
            ids.append((case.get('classname'), case.get('name')))
            state = 'errors' if case.find('error') is not None else 'failures' if case.find('failure') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
            outcomes[state] += 1
    if len(ids) != 3815 or len(set(ids)) != 3815 or dict(outcomes) != {'passed': 3700, 'failures': 84, 'errors': 31}:
        raise ValueError('Retained Mission40 JUnit counts or uniqueness differ')
    return {'valid': True, 'files': len(actual), 'checksummed_files': len(index), 'manifest_entries': len(manifest), 'portable_links': links, 'parsed': dict(parsed), 'Mission40_retained_JUnit': {'tests': len(ids), **dict(outcomes), 'skipped': 0}, 'new_tests_or_inference_executed': 0, 'scope': 'Package-local integrity only; not independent authenticity, GT acceptance or empirical correctness'}


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), indent=2))
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        print(f'Package verification failed: {exc}', file=sys.stderr)
        sys.exit(1)
