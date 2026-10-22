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


def parse_args():
    parser = argparse.ArgumentParser(description="Tokenize Parquet dataset into binary tokens.")
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
    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    eos_token_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 151643

    # Discover and sort shards sequentially
    shard_pattern = str(input_dir / "train-*.parquet")
    shards = sorted(glob.glob(shard_pattern))
    if not shards:
        raise FileNotFoundError(f"No parquet files matching '{shard_pattern}' found.")

    print(f"[2/4] Found {len(shards)} parquet shards to process.")

    total_tokens_accumulated = 0
    token_stats = {}

    print(f"[3/4] Processing shards into '{output_dir}'...")
    for shard_idx, shard_path in enumerate(shards):
        shard_name = Path(shard_path).stem
        out_bin_path = output_dir / f"{shard_name}.bin"
        
        # Read parquet in streaming batches to keep RAM strictly bounded
        pq_file = pq.ParquetFile(shard_path)
        shard_tokens = []
        shard_doc_count = 0

        with tqdm(total=pq_file.metadata.num_rows, desc=f"Shard {shard_idx + 1:02d}/{len(shards):02d}", unit="rows") as pbar:
            for batch in pq_file.iter_batches(batch_size=args.batch_size, columns=[args.text_col]):
                texts = batch[args.text_col].to_pylist()
                # Filter None or empty strings
                texts = [t for t in texts if t and len(t.strip()) > 0]
                if not texts:
                    pbar.update(len(batch))
                    continue

                shard_doc_count += len(texts)
                
                # Fast parallel tokenization via tokenizers rust backend
                encodings = tokenizer(
                    texts,
                    add_special_tokens=False,
                    return_attention_mask=False,
                    truncation=False,
                )["input_ids"]

                # Append tokens + EOS marker for continuous pretraining / causal LM packing
                for token_ids in encodings:
                    shard_tokens.extend(token_ids)
                    shard_tokens.append(eos_token_id)

                pbar.update(len(batch))

        # Convert to numpy uint32 (Qwen vocab is ~152k, easily fitting inside uint32)
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

    # Save metadata summary
    summary_path = output_dir / "tokenization_manifest.json"
    manifest = {
        "model_id": args.model_id,
        "text_column": args.text_col,
        "eos_token_id": eos_token_id,
        "dtype": "uint32",
        "total_tokens": int(total_tokens_accumulated),
        "total_shards": len(shards),
        "shards": token_stats,
    }
    with open(summary_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[4/4] Complete!")
    print(f"Total tokens encoded : {total_tokens_accumulated:,}")
    print(f"Manifest written to   : {summary_path}")


if __name__ == "__main__":
    main()