"""
Tokenize local Parquet shards into a single flat-token HDF5 for pretraining.
Streams row groups/batches with pyarrow to avoid loading entire Parquet files
into RAM, batch-tokenizes with tiktoken across threads, and flushes tokens
to HDF5 in large aligned chunks.

Examples:
    # Tokenize 3 training parquet shards
    python scripts/prepare_pretrain_data.py --split train --num_shards 3 \
        --out data/preprocessed/train.h5
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import h5py
import numpy as np
import pyarrow.parquet as pq
import tiktoken
from tqdm import tqdm

TOTAL_SHARDS = 23
TRAIN_FILES = [
    f"train-{i:05d}-of-{TOTAL_SHARDS:05d}.parquet" for i in range(TOTAL_SHARDS)
]
EOT_ID = 50256
WRITE_CHUNK = 8_000_000  # Flush tokens to HDF5 in ~8M-token chunks
ENC_BATCH = 2048         # Rows per batch to send to tiktoken


def iter_parquet_texts(parquet_path: str | Path, text_column: str = "text", batch_size: int = 4096):
    """
    Stream text rows in batches from a Parquet file without loading
    the full table into RAM.
    """
    parquet_file = pq.ParquetFile(parquet_path)
    # Read only the target column in streaming record batches
    for batch in parquet_file.iter_batches(batch_size=batch_size, columns=[text_column]):
        texts = batch[text_column].to_pylist()
        for txt in texts:
            if txt:
                yield txt


def tokenize_to_h5(
    parquet_paths: list[Path], 
    out_path: str, 
    text_column: str = "source",
    max_tokens: int | None = None
) -> int:
    enc = tiktoken.get_encoding("r50k_base")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    
    total = 0
    buf: list[int] = []

    with h5py.File(out_path, "w") as f:
        # uint16 is sufficient for r50k_base (vocab size 50,257 <= 65,535)
        # Halves disk space and write overhead compared to int32 (i4)
        dset = f.create_dataset(
            "tokens",
            shape=(0,),
            maxshape=(None,),
            dtype="u2",
            chunks=(WRITE_CHUNK,),
            compression="lzf",
        )

        def flush():
            nonlocal total, buf
            if not buf:
                return
            arr = np.asarray(buf, dtype=np.uint16)
            curr_size = dset.shape[0]
            dset.resize(curr_size + arr.size, axis=0)
            dset[curr_size:] = arr
            total += arr.size
            buf = []

        for p_path in parquet_paths:
            print(f"Tokenizing {p_path}")
            docs: list[str] = []
            pbar = tqdm(iter_parquet_texts(p_path, text_column=text_column), unit="doc", desc=p_path.name)
            
            for txt in pbar:
                docs.append(txt)
                if len(docs) >= ENC_BATCH:
                    # num_threads=0 enables Rust multi-threading in tiktoken
                    for ids in enc.encode_ordinary_batch(docs):
                        buf.extend(ids)
                        buf.append(EOT_ID)
                    docs = []

                    if len(buf) >= WRITE_CHUNK:
                        flush()
                        pbar.set_postfix(tokens=f"{total/1e6:.1f}M")

                    if max_tokens and total >= max_tokens:
                        break

            # Handle remainder for this file
            if docs and not (max_tokens and total >= max_tokens):
                for ids in enc.encode_ordinary_batch(docs):
                    buf.extend(ids)
                    buf.append(EOT_ID)

            flush()
            pbar.close()

            if max_tokens and total >= max_tokens:
                break

    print(f"Successfully wrote {total:,} tokens -> {out_path}")
    return total


def main():
    p = argparse.ArgumentParser(description="Preprocess Parquet dataset into an HDF5 token file.")
    p.add_argument("--split", choices=["train", "val"], required=True)
    p.add_argument("--num_shards", type=int, default=23, help="Number of shards to process")
    p.add_argument("--raw_dir", default="data/raw/financial-english-source-corpus", help="Path to raw parquet files")
    p.add_argument("--out", default="data/preprocessed/tokens.h5", help="Path to output HDF5 file")
    p.add_argument("--text_column", default="source", help="Name of the text column in the Parquet files")
    p.add_argument("--max_tokens", type=int, default=None, help="Stop after writing this many tokens")
    args = p.parse_args()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    # Resolve target parquet shard paths
    if args.split == "train":
        selected_shards = TRAIN_FILES[: args.num_shards]
        shard_paths = [raw_dir / name for name in selected_shards]
    else:
        # Check for common val patterns or all val parquet files
        val_shards = sorted(raw_dir.glob("*val*.parquet"))
        if not val_shards:
            val_shards = sorted(raw_dir.glob("*.parquet"))
        shard_paths = val_shards[: args.num_shards]

    # Verify files exist
    missing = [str(p) for p in shard_paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing parquet shards in {raw_dir}:\n" + "\n".join(missing[:5]))

    print(f"Selected {len(shard_paths)} parquet files for '{args.split}' split.")
    tokenize_to_h5(shard_paths, args.out, text_column=args.text_column, max_tokens=args.max_tokens)


if __name__ == "__main__":
    main()