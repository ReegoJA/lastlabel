"""Select descriptive trajectories by a declared event and median-gap rule."""

import argparse
import collections
import hashlib
import json
import tarfile
from pathlib import Path


def select(runs):
    groups = collections.defaultdict(list)
    for run in runs:
        cfg = run['config']
        if (cfg['variant'], cfg['query'], cfg['noise'], cfg['budget']) != (
                'linear-svm-symmetric', 'uncertainty', .15, 400):
            continue
        for outcome in run['outcomes']:
            if outcome['rule'] in ('sp:fixed', 'sp:easy'):
                groups[run['dataset']['name'], outcome['rule']].append((run, outcome))
    cases = []
    for (dataset, rule), members in sorted(groups.items()):
        seeds = [run['config']['seed'] for run, _ in members]
        if len(seeds) != len(set(seeds)):
            raise ValueError('Duplicate trajectory seed in case selection.')
        early = [(r, o) for r, o in members if o['stopped'] and o['labels'] < 400]
        candidates = early or members
        ordered = sorted(candidates, key=lambda pair: (
            pair[1]['f1_gap_to_peak'], pair[0]['config']['seed']))
        run, outcome = ordered[(len(ordered) - 1) // 2]
        cases.append(dict(dataset=dataset, rule=rule, seed=run['config']['seed'],
                          selection='early-trigger median' if early else 'all-run median',
                          candidates=len(candidates), outcome=outcome,
                          trace=[{k: row[k] for k in ('labels', 'macro_f1',
                                  'positive_f1', 'statistics')} for row in run['trace']]))
    if not cases:
        raise ValueError('No matching trajectories.')
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tarfile.open(args.archive, 'r|gz') as archive:
        def records():
            for member in archive:
                if (member.isfile() and member.name.startswith(args.prefix + '/run-')
                        and member.name.endswith('.json')):
                    yield json.load(archive.extractfile(member))
        result = select(records())
    payload = dict(archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(),
                   selection='Per task and rule, lower median gap among early triggers, '
                   'otherwise among all runs. Ties use ascending seed. Descriptive only.',
                   cases=result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n')


if __name__ == '__main__':
    main()
