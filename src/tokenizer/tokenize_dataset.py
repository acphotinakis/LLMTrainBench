#!/usr/bin/env python3
"""
tokenize_dataset.py
Tokenizes raw parquet shards from data/raw/financial-english-source-corpus
and outputs packed uint32 binary token arrays into data/tokenized/.
"""

import argparse
import glob
import json
import os
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from tqdm import tqdm
from transformers import AutoTokenizer
import math
import time

CACHED_TOKENIZER_PATH = Path("cache/tokenizers")


class StreamingTokenStats:
    """
    O(1) memory online statistical accumulator for tokenization pipelines.
    Tracks exact moments, byte/token compression, and approximate percentiles.
    """

    def __init__(self, vocab_size: int, max_track_len: int = 131_072):
        self.vocab_size = vocab_size
        self.total_docs = 0
        self.total_tokens = 0
        self.total_bytes = 0

        # Min / Max / Running moments (Welford's)
        self.min_len = math.inf
        self.max_len = 0
        self._mean = 0.0
        self._M2 = 0.0

        # Context boundary counters
        self.exceeds_4096 = 0
        self.exceeds_8192 = 0

        # Logarithmic binning for percentiles:
        # Bins 0..1024 linear (1:1), then log2 buckets up to max_track_len
        self.linear_cutoff = 1024
        self.max_track_len = max_track_len
        num_log_bins = int(
            math.ceil(math.log2(max_track_len / self.linear_cutoff) * 32)
        )  # 32 sub-bins per octave
        self.linear_bins = np.zeros(self.linear_cutoff + 1, dtype=np.int64)
        self.log_bins = np.zeros(num_log_bins + 1, dtype=np.int64)
        self.overflow_count = 0

    def _val_to_bin(self, val: int):
        if val <= self.linear_cutoff:
            return 0, val
        if val >= self.max_track_len:
            return 2, 0
        # Sub-divided log space
        sub_idx = int(math.log2(val / self.linear_cutoff) * 32)
        return 1, min(sub_idx, len(self.log_bins) - 1)

    def update_batch(self, lengths: list[int], byte_counts: list[int]):
        """Processes a vectorized batch of token lengths and raw UTF-8 byte counts."""
        n = len(lengths)
        if n == 0:
            return

        batch_tokens = sum(lengths)
        batch_bytes = sum(byte_counts)
        self.total_docs += n
        self.total_tokens += batch_tokens
        self.total_bytes += batch_bytes

        # Welford's algorithm batch formulation
        for val in lengths:
            if val < self.min_len:
                self.min_len = val
            if val > self.max_len:
                self.max_len = val

            if val > 4096:
                self.exceeds_4096 += 1
            if val > 8192:
                self.exceeds_8192 += 1

            # Update running variance / mean
            delta = val - self._mean
            self._mean += delta / self.total_docs
            self._M2 += delta * (val - self._mean)

            # Histogram binning
            bin_type, idx = self._val_to_bin(val)
            if bin_type == 0:
                self.linear_bins[idx] += 1
            elif bin_type == 1:
                self.log_bins[idx] += 1
            else:
                self.overflow_count += 1

    @property
    def variance(self) -> float:
        return self._M2 / (self.total_docs - 1) if self.total_docs > 1 else 0.0

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    @property
    def bytes_per_token(self) -> float:
        return self.total_bytes / self.total_tokens if self.total_tokens > 0 else 0.0

    def get_percentile(self, p: float) -> int:
        """Returns approximate percentile (p in [0..100])."""
        if self.total_docs == 0:
            return 0
        target = (p / 100.0) * self.total_docs
        cum = 0

        # Scan linear section
        for i, count in enumerate(self.linear_bins):
            cum += count
            if cum >= target:
                return i

        # Scan log section
        for sub_idx, count in enumerate(self.log_bins):
            cum += count
            if cum >= target:
                lower = self.linear_cutoff * (2 ** (sub_idx / 32))
                upper = self.linear_cutoff * (2 ** ((sub_idx + 1) / 32))
                return int((lower + upper) / 2)

        return self.max_track_len

    def print_report(self, elapsed_sec: float):
        print("\n" + "=" * 58)
        print("          STREAMING TOKENIZATION METRICS REPORT           ")
        print("=" * 58)
        print(f"Tokenizer Vocabulary Size : {self.vocab_size:,}")
        print(f"Total Rows Encoded     : {self.total_docs:,}")
        print(f"Total Tokens Produced  : {self.total_tokens:,}")
        print(f"Total Uncompressed Size: {self.total_bytes / (1024**3):.2f} GB")
        print(
            f"Throughput             : {self.total_tokens / elapsed_sec:,.0f} tok/s | {self.total_docs / elapsed_sec:,.0f} rows/s"
        )
        print(f"Compression Ratio      : {self.bytes_per_token:.3f} bytes/token")
        print("-" * 58)
        print("ESTIMATED CONTEXT DISTRIBUTIONS:")
        print(f"  Min       : {self.min_len:,}")
        print(f"  Mean ± Std: {self._mean:,.1f} ± {self.std_dev:,.1f}")
        print(f"  p50 (Med) : {self.get_percentile(50):,}")
        print(f"  p90       : {self.get_percentile(90):,}")
        print(f"  p95       : {self.get_percentile(95):,}")
        print(f"  p99       : {self.get_percentile(99):,}")
        print(f"  Max       : {self.max_len:,}")
        print("-" * 58)
        pct_4k = (self.exceeds_4096 / self.total_docs * 100) if self.total_docs else 0.0
        pct_8k = (self.exceeds_8192 / self.total_docs * 100) if self.total_docs else 0.0
        print(f"Docs > 4,096 tokens    : {self.exceeds_4096:,} ({pct_4k:.2f}%)")
        print(f"Docs > 8,192 tokens    : {self.exceeds_8192:,} ({pct_8k:.2f}%)")
        print("=" * 58 + "\n")


def get_tokenizer_dir(base_dir: Path, model_id: str) -> Path:
    """
    Sanitizes model_id for filesystem safety:
    e.g. 'Qwen/Qwen2.5-7B' -> 'cache/tokenizers/Qwen--Qwen2.5-7B'
    """
    safe_prefix = model_id.replace("/", "--").strip()
    return base_dir / safe_prefix


def load_or_cache_tokenizer(
    model_id: str = "Qwen/Qwen2.5-7B",
    base_cache_path: Path = CACHED_TOKENIZER_PATH,
    trust_remote_code: bool = True,
) -> AutoTokenizer:
    target_dir = get_tokenizer_dir(base_cache_path, model_id)

    # Detect if core tokenizer artifacts are already present locally
    has_artifacts = target_dir.exists() and any(
        (target_dir / f).exists()
        for f in ("tokenizer.json", "vocab.json", "tokenizer_config.json")
    )

    if has_artifacts:
        print(f"[Tokenizer] Loading cached tokenizer from: {target_dir.resolve()}")
        return AutoTokenizer.from_pretrained(
            str(target_dir),
            local_files_only=True,
            trust_remote_code=trust_remote_code,
        )

    print(f"[Tokenizer] Local cache not found. Downloading '{model_id}'...")
    target_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        trust_remote_code=trust_remote_code,
    )

    print(f"[Tokenizer] Serializing artifacts to: {target_dir.resolve()}")
    tokenizer.save_pretrained(str(target_dir))
    return tokenizer


import time
import pyarrow.parquet as pq


def process_shards(shards: list[str], tokenizer: AutoTokenizer, args, output_dir: Path):
    vocab_size = len(tokenizer)
    stats = StreamingTokenStats(vocab_size=vocab_size)
    start_time = time.perf_counter()
    eos_token_id = (
        tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 151643
    )

    total_tokens_accumulated = 0
    token_stats = {}

    print(f"[3/4] Processing shards into '{output_dir}' (Vocab: {vocab_size:,})...")
    for shard_idx, shard_path in enumerate(shards):
        shard_name = Path(shard_path).stem
        out_bin_path = output_dir / f"{shard_name}.bin"

        pq_file = pq.ParquetFile(shard_path)
        shard_tokens = []
        shard_doc_count = 0

        with tqdm(
            total=pq_file.metadata.num_rows,
            desc=f"Shard {shard_idx + 1:02d}/{len(shards):02d}",
            unit="rows",
        ) as pbar:
            for batch in pq_file.iter_batches(
                batch_size=args.batch_size, columns=[args.text_col]
            ):
                texts = [
                    t
                    for t in batch[args.text_col].to_pylist()
                    if t and len(t.strip()) > 0
                ]
                if not texts:
                    pbar.update(len(batch))
                    continue

                shard_doc_count += len(texts)
                byte_counts = [len(t.encode("utf-8")) for t in texts]

                encodings = tokenizer(
                    texts,
                    add_special_tokens=False,
                    return_attention_mask=False,
                    truncation=False,
                )["input_ids"]

                lengths = [len(seq) for seq in encodings]
                stats.update_batch(lengths, byte_counts)

                for token_ids in encodings:
                    shard_tokens.extend(token_ids)
                    shard_tokens.append(eos_token_id)

                pbar.update(len(batch))

        np_tokens = np.array(shard_tokens, dtype=np.uint32)
        np_tokens.tofile(str(out_bin_path))

        num_tokens = len(np_tokens)
        total_tokens_accumulated += num_tokens
        token_stats[shard_name] = {
            "rows": shard_doc_count,
            "tokens": int(num_tokens),
            "bytes": int(np_tokens.nbytes),
            "file": out_bin_path.name,
        }

    elapsed = time.perf_counter() - start_time
    stats.print_report(elapsed_sec=elapsed)

    # Save metadata summary manifest
    summary_path = output_dir / "tokenization_manifest.json"
    manifest = {
        "model_id": args.model_id,
        "vocab_size": vocab_size,
        "text_column": args.text_col,
        "eos_token_id": eos_token_id,
        "dtype": "uint32",
        "total_tokens": int(total_tokens_accumulated),
        "total_shards": len(shards),
        "shards": token_stats,
    }
    with open(summary_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[4/4] Complete!")
    print(f"Total tokens encoded : {total_tokens_accumulated:,}")
    print(f"Manifest written to   : {summary_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tokenize Parquet dataset into binary tokens."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="data/raw/financial-english-source-corpus",
        help="Path containing train-*.parquet shards",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/tokenized",
        help="Output directory for tokenized binary/parquet files",
    )
    parser.add_argument(
        "--model_id",
        type=str,
        default="Qwen/Qwen3.5-9B",
        help="HuggingFace model ID or local tokenizer path",
    )
    parser.add_argument(
        "--text_col",
        type=str,
        default="source",
        help="Text column name in the parquet schema",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4096,
        help="Number of text rows passed to tokenizer in parallel",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Loading tokenizer: {args.model_id}")
    tokenizer = load_or_cache_tokenizer(
        model_id=args.model_id,
        base_cache_path=CACHED_TOKENIZER_PATH,
        trust_remote_code=True,
    )

    shard_pattern = str(input_dir / "train-*.parquet")
    shards = sorted(glob.glob(shard_pattern))
    if not shards:
        raise FileNotFoundError(f"No parquet files matching '{shard_pattern}' found.")

    print(f"[2/4] Found {len(shards)} parquet shards to process.")
    process_shards(shards=shards, tokenizer=tokenizer, args=args, output_dir=output_dir)


if __name__ == "__main__":
    main()
