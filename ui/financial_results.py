"""Read saved financial evaluations without loading models or executing snapshots."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ROOT / 'llm_flow_evaluation/results'
DEFAULT_RUN = RESULTS_ROOT / 'financial_pilot_v1_20261127_213759_273737'
Record = dict[str, Any]


@dataclass
class EvaluationResults:
    rows: list[Record]
    qa: list[Record]
    prose: list[Record]
    config: Record
    issues: list[str]


def load_results(path: Path) -> EvaluationResults:
    """Load summaries and normalized samples; flag incomplete or mismatched runs."""
    rows = json.loads((path / 'comparison.json').read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError('comparison.json must contain a nonempty list of results.')
    required = {'model', 'mode', 'suite_sha256', 'qa_accuracy', 'bits_per_byte',
                'seconds', 'peak_allocated_gib', 'question_count', 'document_count'}
    for row in rows:
        if not required.issubset(row):
            raise ValueError('A comparison row is missing required evaluation fields.')
    keys = [(r['model'], r['mode']) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate model/mode rows in comparison.json.')
    config_path = path / 'evaluation_config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    qa, prose, issues = [], [], []
    hashes = {r['suite_sha256'] for r in rows}
    if len(hashes) != 1 or (config.get('suite_sha256') and config['suite_sha256'] not in hashes):
        issues.append('Suite hashes differ. Cross-suite adaptation deltas are disabled.')
    for row in rows:
        # Discover only immediate run folders; model labels never become arbitrary paths.
        folders = {p.name: p for p in path.iterdir() if p.is_dir()}
        folder = folders.get(f"{row['model']}_{row['mode']}")
        sample_path = folder / 'samples.jsonl' if folder else None
        if sample_path is None or not sample_path.exists():
            issues.append(f"Missing samples for {row['model']} / {row['mode']}.")
            continue
        counts = {'financial_qa': 0, 'financial_prose': 0}
        with sample_path.open() as stream:
            for line in stream:
                if not line.strip():
                    continue
                sample = json.loads(line)
                doc = sample['doc']
                common = {'model': row['model'], 'mode': row['mode'], 'id': doc['id']}
                task = sample['task']
                if task == 'financial_qa':
                    responses = sample.get('filtered_resps', [])
                    qa.append({**common, 'context': doc['context'], 'question': doc['question'],
                               'answers': doc['answers'], 'response': responses[0] if responses else '',
                               'correct': sample['acc'], 'category': doc.get('category', 'Unknown')})
                elif task == 'financial_prose':
                    ll, size = sample['bits_per_byte']
                    prose.append({**common, 'text': doc['text'], 'log_likelihood': ll,
                                  'bytes': size, 'bits_per_byte': -ll / (size * math.log(2))})
                if task in counts:
                    counts[task] += 1
        if counts['financial_qa'] != row['question_count'] or counts['financial_prose'] != row['document_count']:
            issues.append(f"Sample counts disagree with summary for {row['model']} / {row['mode']}.")
    return EvaluationResults(rows, qa, prose, config, issues)


def paired_changes(rows: list[Record]) -> list[Record]:
    """Compute adapted minus baseline only for matching suites and sample counts."""
    if any('test' in r for r in rows):
        return [{**change, 'test': test}
                for test in sorted({r.get('test', '') for r in rows})
                for change in paired_changes([{k: v for k, v in r.items() if k != 'test'}
                                              for r in rows if r.get('test', '') == test])]
    indexed = {(r['model'], r['mode']): r for r in rows}
    changes = []
    for model in sorted({r['model'] for r in rows}):
        base, adapted = indexed.get((model, 'baseline')), indexed.get((model, 'adapted'))
        if base is None or adapted is None:
            continue
        if any(base[k] != adapted[k] for k in ('suite_sha256', 'question_count', 'document_count')):
            continue
        changes.append({'model': model, 'qa_change_pp': 100 * (adapted['qa_accuracy'] - base['qa_accuracy']),
                        'bpb_change': adapted['bits_per_byte'] - base['bits_per_byte'],
                        'bpb_reduction_pct': 100 * (1 - adapted['bits_per_byte'] / base['bits_per_byte'])
                        if base['bits_per_byte'] else None,
                        'seconds_change': adapted['seconds'] - base['seconds'],
                        'memory_change_gib': adapted['peak_allocated_gib'] - base['peak_allocated_gib']})
    return changes


def paired_questions(samples: list[Record], model: str) -> list[Record]:
    """Align question IDs, keeping missing or changed questions explicitly unpaired."""
    if any('test' in r for r in samples):
        return [{**question, 'test': test}
                for test in sorted({r.get('test', '') for r in samples})
                for question in paired_questions([{k: v for k, v in r.items() if k != 'test'}
                                                  for r in samples if r.get('test', '') == test], model)]
    groups: dict[str, dict[str, Record]] = {}
    for sample in samples:
        if sample['model'] == model:
            groups.setdefault(sample['id'], {})[sample['mode']] = sample
    rows = []
    for question_id, modes in sorted(groups.items()):
        base, adapted = modes.get('baseline'), modes.get('adapted')
        doc = base or adapted
        assert doc is not None
        transition = 'Unpaired'
        if base is not None and adapted is not None and all(base[k] == adapted[k] for k in ('context', 'question', 'answers')):
            before, after = base['correct'], adapted['correct']
            transition = ('Improved' if after > before else 'Regressed' if after < before
                          else 'Both correct' if after else 'Both incorrect')
        rows.append({'id': question_id, 'question': doc['question'], 'context': doc['context'],
                     'answers': doc['answers'], 'transition': transition,
                     'baseline_response': base['response'] if base else None,
                     'adapted_response': adapted['response'] if adapted else None,
                     'baseline_correct': base['correct'] if base else None,
                     'adapted_correct': adapted['correct'] if adapted else None})
    return rows


def discover_tests(root: Path = RESULTS_ROOT) -> list[Path]:
    """Find completed or partial comparison exports, including nested test folders."""
    return sorted({p.parent for p in root.rglob('comparison.json')}, reverse=True)


def load_collection(paths: list[Path], root: Path = RESULTS_ROOT) -> EvaluationResults:
    """Combine runs while retaining test identity on every row and sample."""
    combined = EvaluationResults([], [], [], {'tests': {}}, [])
    for path in paths:
        test = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        try:
            data = load_results(path)
        except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError) as error:
            combined.issues.append(f'{test}: Could not load results: {error}')
            continue
        for field in ('rows', 'qa', 'prose'):
            getattr(combined, field).extend({**row, 'test': test} for row in getattr(data, field))
        combined.config['tests'][test] = data.config
        combined.issues.extend(f'{test}: {issue}' for issue in data.issues)
    return combined


def aggregate_results(data: EvaluationResults) -> list[Record]:
    """Pool QA by question count and prose by actual UTF-8 bytes across tests.

    Repeated questions count as repeated observations. Keep model IDs and dtypes
    separate; duration is summed and memory is the maximum observed allocation.
    Missing prose samples make pooled BPB unavailable rather than biasing its mean.
    """
    groups: dict[tuple, list[Record]] = {}
    for row in data.rows:
        key = (row['model'], row['mode'], row.get('model_id'), row.get('dtype'))
        groups.setdefault(key, []).append(row)
    pooled = []
    for rows in groups.values():
        first = rows[0]
        identities = {(r['test'], r['model'], r['mode']) for r in rows}
        passages = [p for p in data.prose if (p['test'], p['model'], p['mode']) in identities]
        questions = sum(r['question_count'] for r in rows)
        documents = sum(r['document_count'] for r in rows)
        byte_count = sum(p['bytes'] for p in passages)
        bpb = (-sum(p['log_likelihood'] for p in passages) / (byte_count * math.log(2))
               if byte_count and len(passages) == documents else None)
        pooled.append({
            'model': first['model'], 'mode': first['mode'], 'model_id': first.get('model_id'),
            'dtype': first.get('dtype'), 'test_count': len(rows),
            'suite_count': len({r['suite_sha256'] for r in rows}),
            'qa_accuracy': sum(r['qa_accuracy'] * r['question_count'] for r in rows) / questions if questions else None,
            'bits_per_byte': bpb, 'question_count': questions, 'document_count': documents,
            'seconds': sum(r['seconds'] for r in rows),
            'peak_allocated_gib': max(r['peak_allocated_gib'] for r in rows),
        })
    return pooled
