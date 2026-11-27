"""Static design checks only; not application/TDD test code. Requires jsonschema."""
import csv
import json
import re
from pathlib import Path
from collections import Counter
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent

def load_csv(name):
    with (ROOT / 'planning' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

requirements = load_csv('REQUIREMENTS.csv')
tests = load_csv('TEST_CATALOG.csv')
rids = {r['requirement_id'] for r in requirements}
tids = {t['test_id'] for t in tests}
assert len(rids) == len(requirements) and len(tids) == len(tests)
by_test = {t['test_id']: t for t in tests}
scenarios = set(re.findall(r'\|\s*(S\d{2})\b', (ROOT / 'docs/13_SCENARIOS.md').read_text()))
covered = set()
for req in requirements:
    links = req['test_ids'].split(',')
    sc = set(req['scenario_ids'].split(','))
    assert sc <= scenarios, (req['requirement_id'], sc - scenarios)
    covered |= sc
    assert len(links) >= 2
    assert {by_test[t]['kind'] for t in links} == {'positive', 'negative_or_recovery'}
    assert all(by_test[t]['requirement_id'] == req['requirement_id'] and by_test[t]['priority'] == req['priority'] for t in links)
    assert len(list(ROOT.glob(req['design_doc']+'*.md'))) == 1
for t in tests:
    assert t['requirement_id'] in rids
    assert t['status'] == 'NOT_RUN'
    assert t['given'] and t['when'] and t['then']
assert {t for req in requirements for t in req['test_ids'].split(',')} == tids
assert covered == scenarios, scenarios - covered
print(f'PASS traceability: {len(requirements)} requirements / {len(tests)} planned tests / {len(scenarios)} scenarios; priorities={dict(Counter(r["priority"] for r in requirements))}')

valid_count = 0
invalid_count = 0
for path in sorted((ROOT / 'contracts').glob('*.schema.json')):
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    stem = path.name.removesuffix('.schema.json')
    example = ROOT / 'examples' / (stem+'.example.json')
    validator.validate(load_json(example))
    valid_count += 1
    invalid = ROOT / 'examples' / (stem+'.invalid.json')
    if invalid.exists():
        assert not validator.is_valid(load_json(invalid)), invalid
        invalid_count += 1
print(f'PASS schema syntax + positive examples: {valid_count}; intentionally invalid examples rejected: {invalid_count}')
for p in sorted(ROOT.rglob('*.md')):
    for link in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
        if '://' in link or link.startswith('#'): continue
        link=link.split('#')[0]
        if link: assert (p.parent / link).exists(), (p, link)
print('PASS relative Markdown link existence')
print('NOT_RUN all application, host, GPU, API, security and real render tests; no implementation claimed.')
