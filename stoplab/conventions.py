"""Replay SP with an alternative convention for constant predictions."""

import argparse
import collections
import hashlib
import json
import tarfile
from pathlib import Path

from stoplab.report import interval, write_csv
from stoplab.rules import StopRule


def replay(run, stop_set, constant_agreement=False):
    """Change only undefined noninitial, nonempty kappa comparisons."""
    config = run['config']
    rule = StopRule('sp', config['kappa'], config['window'])
    trace = run['trace']
    for index, row in enumerate(trace):
        stats = row['statistics'][stop_set]
        value = stats['kappa']
        if constant_agreement and index and stats['size'] and value is None:
            value = 1.0
        if rule.update(value):
            return index, True
    return len(trace) - 1, False


def compare(run):
    rows = []
    for stop_set in ('fixed', 'easy', 'remaining'):
        original_index, original_stopped = replay(run, stop_set)
        alternative_index, alternative_stopped = replay(run, stop_set, True)
        original = run['trace'][original_index]
        alternative = run['trace'][alternative_index]
        saved = next(o for o in run['outcomes'] if o['rule'] == 'sp:' + stop_set)
        if (saved['stopped'], saved['labels']) != (original_stopped, original['labels']):
            raise ValueError('Original replay does not match the archived outcome.')
        config = run['config']
        row = {key: config[key] for key in ('query', 'variant', 'noise', 'seed')}
        row.update(dataset=run['dataset']['name'], stop_set=stop_set,
                   changed_model=int(original_index != alternative_index),
                   changed_trigger=int(original_stopped != alternative_stopped))
        for metric in ('labels', 'macro_f1', 'positive_f1'):
            row[metric + '_delta'] = alternative[metric] - original[metric]
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    seen = set()
    with tarfile.open(args.archive, 'r|gz') as archive:
        for member in archive:
            if not (member.isfile() and member.name.startswith(args.prefix + '/run-')
                    and member.name.endswith('.json')):
                continue
            run = json.load(archive.extractfile(member))
            for row in compare(run):
                identity = tuple(row[k] for k in ('dataset', 'query', 'variant', 'noise', 'seed', 'stop_set'))
                if identity in seen:
                    raise ValueError('Duplicate trajectory outcome.')
                seen.add(identity)
                rows.append(row)
    if not rows:
        raise ValueError('No matching trajectories.')
    groups = collections.defaultdict(list)
    keys = ('dataset', 'query', 'variant', 'noise', 'stop_set')
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    summary = []
    for key, members in sorted(groups.items()):
        result = dict(zip(keys, key))
        result.update(seeds=len(members),
                      changed_models=sum(r['changed_model'] for r in members),
                      changed_triggers=sum(r['changed_trigger'] for r in members))
        for metric in ('labels', 'macro_f1', 'positive_f1'):
            mean, low, high = interval([r[metric + '_delta'] for r in members])
            result.update({metric + '_delta': mean, metric + '_low': low,
                           metric + '_high': high})
        summary.append(result)
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / 'paired.csv', summary)
    write_csv(args.output / 'runs.csv', rows)
    metadata = dict(archive_sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(),
                    outcomes=len(rows), changed_models=sum(r['changed_model'] for r in rows),
                    changed_triggers=sum(r['changed_trigger'] for r in rows),
                    convention='Noninitial undefined kappa on a nonempty set becomes 1. '
                    'Strict threshold, window, PCF, and trained models remain unchanged.',
                    interpretation='Alternative minus archived convention. Pointwise paired seed intervals.')
    (args.output / 'analysis.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
