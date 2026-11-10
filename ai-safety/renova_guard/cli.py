"""CLI for synthetic-fixture checks. Does not call models or execute tools."""
import argparse
import json
from pathlib import Path
from .gate import assess, assess_claim

def main():
    parser = argparse.ArgumentParser(description='Offline ℛenova safety-gate prototype')
    parser.add_argument('fixture', type=Path, help='JSON list of synthetic cases')
    args = parser.parse_args()
    rows = json.loads(args.fixture.read_text(encoding='utf-8'))
    output = []
    for row in rows:
        guard = assess_claim if row.get('mode') == 'claim' else assess
        decision = guard(row['input'])
        output.append({'id': row['id'], 'expected': row['expected'],
                       'observed': decision.status,
                       'pass': decision.status == row['expected'],
                       'reasons': decision.as_dict()['reasons']})
    print(json.dumps({'fixture_count':len(output), 'all_match':all(x['pass'] for x in output),
                     'tests':output, 'warning':'Synthetic fixtures only: NOT effectiveness evidence.'},
                     indent=2, ensure_ascii=False))
    return 0 if all(x['pass'] for x in output) else 1

if __name__ == '__main__':
    raise SystemExit(main())
