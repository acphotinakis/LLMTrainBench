import json
import tempfile
import unittest
from pathlib import Path

from src.financial_eval import (
    audit_suite,
    aggregate_bpb,
    build_suite,
    canonical_answer,
    load_runs,
    normalized_hash,
    score_answer,
    suite_digest,
    make_tasks,
)


class FinancialEvaluationTests(unittest.TestCase):
    def test_byte_weighting_and_reference_validation(self):
        import math

        self.assertAlmostEqual(aggregate_bpb([(-2 * math.log(2), 2),
                                              (-4 * math.log(2), 4)]), 1.0)
        suite = build_suite([{"source": "Revenue amounted to $10 million. " * 4}],
                            set(), "revision", 1, 1)
        suite["questions"][0]["answers"] = ["$99 million"]
        with self.assertRaises(ValueError):
            audit_suite(suite, set())

    def test_task_definitions_preserve_documents_and_custom_scoring(self):
        import sys
        from types import ModuleType
        from unittest.mock import patch

        module = ModuleType("lm_eval.api.task")
        module.ConfigurableTask = lambda config: config
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {
            "lm_eval": ModuleType("lm_eval"), "lm_eval.api": ModuleType("lm_eval.api"),
            "lm_eval.api.task": module,
        }):
            suite = build_suite([{"source": "Revenue amounted to $10 million. " * 4}],
                                set(), "revision", 1, 1)
            path = Path(tmp) / "suite.json"
            path.write_text(json.dumps(suite))
            prose, qa = make_tasks(path)
            self.assertEqual(prose["output_type"], "loglikelihood_rolling")
            self.assertEqual(qa["output_type"], "generate_until")
            question = suite["questions"][0]
            self.assertIn(question["context"], qa["doc_to_text"](question))
            self.assertEqual(qa["process_results"](question, ["$10,000,000"]), {"acc": 1.0})
            self.assertEqual(qa["process_results"](question, ["$10"]), {"acc": 0.0})
            self.assertEqual(len((Path(tmp) / "financial_text.jsonl").read_text().splitlines()), 1)

    def test_numeric_answers_require_units_and_entire_response(self):
        self.assertEqual(canonical_answer("$1 million"), canonical_answer("$1,000,000"))
        self.assertEqual(score_answer("25%", ["25 %"]), 1.0)
        self.assertEqual(score_answer("25", ["25%"]), 0.0)
        self.assertEqual(score_answer("The answer is $25", ["$25"]), 0.0)
        self.assertEqual(score_answer("$25 billion", ["$25 million"]), 0.0)

    def test_sampling_excludes_normalized_training_documents(self):
        excluded = "Revenue was $100 million in the year. " * 4
        rows = [{"source": excluded, "index": 0}]
        rows += [{"source": f"Company {i} reported revenue of ${i + 1} million. " * 4,
                  "index": i + 1} for i in range(6)]
        suite = build_suite(rows, {normalized_hash(excluded)}, "revision", 3, 2)
        self.assertEqual(len(suite["documents"]), 3)
        self.assertEqual(len(suite["questions"]), 2)
        audit_suite(suite, {normalized_hash(excluded)})
        self.assertEqual(suite_digest(suite), suite_digest(json.loads(json.dumps(suite))))
        suite["questions"][0]["context"] = "changed"
        with self.assertRaises(ValueError):
            audit_suite(suite, set())

    def test_refuses_insufficient_data_or_new_overlap(self):
        rows = [{"source": "A company reported $12 million in sales. " * 4}]
        with self.assertRaises(ValueError):
            build_suite(rows, set(), "revision", 2, 1)
        suite = build_suite(rows, set(), "revision", 1, 1)
        with self.assertRaises(ValueError):
            audit_suite(suite, {suite["documents"][0]["document_sha256"]})

    def test_run_loader_requires_manifest_and_saved_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = root / "adapter"
            adapter.mkdir()
            config = {"MODEL_ID": "example/base", "model_sha": "a" * 40,
                      "DATASET_ID": "example/data", "dataset_sha": "b" * 40,
                      "MAX_DOC_CHARS": 32768}
            (root / "run_config.json").write_text(json.dumps(config))
            (root / "split_manifest.json").write_text(json.dumps(
                {"train": [{"sha256": "c" * 64}], "eval": []}))
            with self.assertRaises(ValueError):
                load_runs({"test": root})
            (adapter / "adapter_config.json").write_text(json.dumps(
                {"base_model_name_or_path": "example/base"}))
            (adapter / "adapter_model.safetensors").write_bytes(b"test")
            (adapter / "tokenizer_config.json").write_text("{}")
            runs, excluded = load_runs({"test": root})
            self.assertEqual(excluded, {"c" * 64})
            self.assertEqual(runs[0]["model_sha"], "a" * 40)
            (adapter / "adapter_config.json").write_text(json.dumps(
                {"base_model_name_or_path": "wrong/base"}))
            with self.assertRaises(ValueError):
                load_runs({"test": root})


if __name__ == "__main__":
    unittest.main()
