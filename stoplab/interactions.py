"""Estimate changes in stop-set effects between noisy and clean conditions."""

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

from stoplab.report import interval, write_csv


def compare(rows):
    """Pair four outcomes per seed before bootstrapping the interaction."""
    indexed = {}
    groups = collections.defaultdict(set)
    for row in rows:
        if row['rule'] not in {f'{m}:{s}' for m in ('sp', 'pcf')
                               for s in ('fixed', 'easy', 'remaining')}:
            continue
        condition = (row['dataset'], row['query'], row['variant'])
        noise, seed = float(row['noise']), int(row['seed'])
        key = (*condition, noise, seed, row['rule'])
        if key in indexed:
            raise ValueError('Duplicate outcome.')
        indexed[key] = row
        groups[(*condition, noise)].add(seed)
    output = []
    for (*condition, noise), seeds in sorted(groups.items()):
        if noise == 0:
            continue
        if groups.get((*condition, 0)) != seeds:
            raise ValueError('Clean and noisy seed sets must match.')
        for method in ('sp', 'pcf'):
            for stop_set in ('easy', 'remaining'):
                differences = collections.defaultdict(list)
                for seed in sorted(seeds):
                    try:
                        four = [indexed[(*condition, n, seed, f'{method}:{s}')]
                                for n, s in ((noise, stop_set), (noise, 'fixed'),
                                             (0, stop_set), (0, 'fixed'))]
                    except KeyError as error:
                        raise ValueError('Missing paired stopping outcome.') from error
                    for metric in ('labels', 'macro_f1', 'positive_f1'):
                        a, b, c, d = [float(r[metric]) for r in four]
                        differences[metric].append((a - b) - (c - d))
                result = dict(zip(('dataset', 'query', 'variant'), condition))
                result.update(noise=noise, method=method, stop_set=stop_set,
                              seeds=len(seeds))
                for metric, values in differences.items():
                    mean, low, high = interval(values)
                    result.update({metric + '_interaction': mean,
                                   metric + '_low': low, metric + '_high': high})
                output.append(result)
    if not output:
        raise ValueError('No matched noisy conditions.')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.runs.open(newline='', encoding='utf-8') as stream:
        result = compare(list(csv.DictReader(stream)))
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / 'interactions.csv', result)
    metadata = dict(runs_sha256=hashlib.sha256(args.runs.read_bytes()).hexdigest(),
                    contrast='(alternative - fixed) noisy minus (alternative - fixed) clean',
                    interpretation='Exploratory paired seed bootstrap, pointwise 95% intervals.')
    (args.output / 'analysis.json').write_text(json.dumps(metadata, indent=2) + '\n')


if __name__ == '__main__':
    main()
