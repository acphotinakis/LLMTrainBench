"""Dashboard calculations must preserve the saved evaluation's semantics."""
import json
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ui.financial_results import (
    DEFAULT_RUN,
    load_results,
    paired_changes,
    paired_questions,
)


class FinancialDashboardTests(unittest.TestCase):
    def test_saved_run_and_byte_weighted_scores(self):
        data = load_results(DEFAULT_RUN)
        self.assertEqual(len(data.rows), 6)
        self.assertEqual(len(data.qa), 120)
        self.assertEqual(len(data.prose), 120)
        for row in data.rows:
            samples = [s for s in data.prose if (s['model'], s['mode']) == (row['model'], row['mode'])]
            bpb = -sum(s['log_likelihood'] for s in samples) / (sum(s['bytes'] for s in samples) * math.log(2))
            self.assertAlmostEqual(bpb, row['bits_per_byte'])
        changes = {r['model']: r for r in paired_changes(data.rows)}
        self.assertAlmostEqual(changes['qwen']['qa_change_pp'], 40)
        self.assertAlmostEqual(changes['pythia']['qa_change_pp'], -15)
        self.assertEqual(data.issues, [])

    def test_pairs_join_by_question_id_and_preserve_response(self):
        data = load_results(DEFAULT_RUN)
        pairs = paired_questions(list(reversed(data.qa)), 'qwen')
        self.assertEqual(len(pairs), 20)
        self.assertEqual(sum(p['transition'] == 'Improved' for p in pairs), 8)
        self.assertTrue(any(p['adapted_response'].startswith(' ') for p in pairs))
        self.assertEqual(len(paired_changes([data.rows[0]])), 0)
        incomplete = paired_questions([r for r in data.qa if r['mode'] == 'baseline'], 'qwen')
        self.assertTrue(all(p['transition'] == 'Unpaired' for p in incomplete))

    def test_missing_samples_and_mixed_suites_are_reported(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            rows = [dict(r) for r in load_results(DEFAULT_RUN).rows[:2]]
            rows[1]['suite_sha256'] = 'different'
            (path / 'comparison.json').write_text(json.dumps(rows))
            data = load_results(path)
            self.assertTrue(any('suite' in issue.lower() for issue in data.issues))
            self.assertTrue(any('samples' in issue.lower() for issue in data.issues))
            self.assertEqual(paired_changes(rows), [])

    def test_dashboard_filters_and_question_inspection(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'ui/financial_dashboard.py')).run(timeout=20)
        self.assertFalse(app.exception)
        app.multiselect(key='models').set_value(['qwen']).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value), 2)
        app.selectbox(key='question_model').set_value('qwen').run()
        app.selectbox(key='transition').set_value('Improved').run()
        self.assertFalse(app.exception)
        self.assertIn('8 matching questions', ' '.join(c.value for c in app.caption))
        app.multiselect(key='models').set_value([]).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.info)


class CollectionTests(unittest.TestCase):
    def test_all_tests_weight_scores_and_keep_samples_and_pairs_separate(self):
        from unittest.mock import patch

        from ui.financial_results import aggregate_results, load_collection
        original = load_results(DEFAULT_RUN)
        second = load_results(DEFAULT_RUN)
        second.rows[0]['qa_accuracy'] = 1.0
        second.rows[0]['question_count'] = 40
        with patch('ui.financial_results.load_results', side_effect=[original, second]):
            data = load_collection([Path('first'), Path('second')])
        combined = aggregate_results(data)
        qwen = next(r for r in combined if r['model'] == 'qwen' and r['mode'] == 'baseline')
        self.assertAlmostEqual(qwen['qa_accuracy'], (0.25 * 20 + 40) / 60)
        self.assertEqual(qwen['test_count'], 2)
        self.assertEqual(qwen['seconds'], original.rows[0]['seconds'] * 2)
        self.assertEqual(qwen['peak_allocated_gib'], original.rows[0]['peak_allocated_gib'])
        self.assertEqual(len(paired_changes(data.rows)), 5)  # One pair has unequal question counts.
        self.assertEqual(len(paired_questions(data.qa, 'qwen')), 40)
        self.assertEqual({p['test'] for p in paired_questions(data.qa, 'qwen')}, {'first', 'second'})

    def test_discovery_and_all_tests_ui(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'ui/financial_dashboard.py')).run(timeout=20)
        app.selectbox(key='evaluation_test').set_value('All tests').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value), 6)
        self.assertIn('test_count', app.dataframe[0].value.columns)

    def test_byte_weighting_and_incomplete_samples(self):
        from ui.financial_results import (
            EvaluationResults,
            aggregate_results,
            discover_tests,
        )
        row = load_results(DEFAULT_RUN).rows[0]
        rows = [{**row, 'test': name, 'document_count': 1} for name in ['a', 'b']]
        prose = [{'test': 'a', 'model': 'qwen', 'mode': 'baseline', 'bytes': 10,
                  'log_likelihood': -10 * math.log(2)},
                 {'test': 'b', 'model': 'qwen', 'mode': 'baseline', 'bytes': 30,
                  'log_likelihood': -60 * math.log(2)}]
        data = EvaluationResults(rows, [], prose, {}, [])
        self.assertAlmostEqual(aggregate_results(data)[0]['bits_per_byte'], 1.75)
        data.prose.pop()
        self.assertIsNone(aggregate_results(data)[0]['bits_per_byte'])
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'nested' / 'test'
            folder.mkdir(parents=True)
            (folder / 'comparison.json').write_text('[]')
            self.assertEqual(discover_tests(Path(tmp)), [folder])
