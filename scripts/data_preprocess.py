#!/usr/bin/env python3
"""
Tokenize partitioned Parquet shards into a flat-token HDF5 file for pretraining.
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

EOT_ID = 50256
WRITE_CHUNK = 8_000_000  # Flush to HDF5 in ~8M token chunks
ENC_BATCH = 2048  # Rows per batch to send to tiktoken


def iter_parquet_texts(
    parquet_path: Path, text_column: str = "source", batch_size: int = 4096
):
    """Streams rows from a parquet file without loading the entire table into RAM."""
    parquet_file = pq.ParquetFile(parquet_path)
    for batch in parquet_file.iter_batches(
        batch_size=batch_size, columns=[text_column]
    ):
        texts = batch[text_column].to_pylist()
        for txt in texts:
            if txt:
                yield txt


def tokenize_to_h5(
    parquet_paths: list[Path],
    out_path: Path,
    text_column: str = "source",
    max_tokens: int | None = None,
) -> int:
    enc = tiktoken.get_encoding("r50k_base")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    buf: list[int] = []

    with h5py.File(out_path, "w") as f:
        dset = f.create_dataset(
            "tokens",
            shape=(0,),
            maxshape=(None,),
            dtype="u2",  # uint16 is sufficient for r50k_base (vocab <= 65535)
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
            buf.clear()

        for p_path in parquet_paths:
            docs: list[str] = []
            pbar = tqdm(
                iter_parquet_texts(p_path, text_column=text_column),
                unit="doc",
                desc=p_path.name,
            )

            for txt in pbar:
                docs.append(txt)
                if len(docs) >= ENC_BATCH:
                    # Let ThreadPoolExecutor auto-detect CPU cores
                    for ids in enc.encode_ordinary_batch(docs):
                        buf.extend(ids)
                        buf.append(EOT_ID)
                    docs.clear()

                    if len(buf) >= WRITE_CHUNK:
                        flush()
                        pbar.set_postfix(tokens=f"{total / 1e6:.1f}M")

                    if max_tokens and total >= max_tokens:
                        break

            if docs and not (max_tokens and total >= max_tokens):
                for ids in enc.encode_ordinary_batch(docs):
                    buf.extend(ids)
                    buf.append(EOT_ID)

            flush()
            pbar.set_postfix(tokens=f"{total / 1e6:.1f}M")  # <--- Add this line
            pbar.close()

            if max_tokens and total >= max_tokens:
                break

    print(f"\nSuccessfully wrote {total:,} tokens -> {out_path}")
    return total


def main():
    p = argparse.ArgumentParser(
        description="Preprocess Parquet into an HDF5 token file."
    )
    p.add_argument("--split", choices=["train", "val"], required=True)
    p.add_argument(
        "--base_dir",
        type=Path,
        default=Path("data/financial-english-source-corpus"),
        help="Root directory of the dataset",
    )
    p.add_argument(
        "--num_shards",
        type=int,
        default=None,
        help="Max shards to process (train only)",
    )
    p.add_argument(
        "--text_column", default="source", help="Name of text column in Parquet"
    )
    p.add_argument(
        "--max_tokens",
        type=int,
        default=None,
        help="Stop after writing this many tokens",
    )
    args = p.parse_args()

    partitioned_dir = args.base_dir / "partitioned"
    preprocessed_dir = args.base_dir / "preprocessed"

    if args.split == "train":
        train_dir = partitioned_dir / "train"
        shard_paths = sorted(train_dir.glob("*.parquet"))
        if not shard_paths:
            raise FileNotFoundError(
                f"No train shards found in {train_dir}. Did you run download_and_split.py?"
            )
        if args.num_shards is not None:
            shard_paths = shard_paths[: args.num_shards]
        out_path = preprocessed_dir / "train.h5"
    else:
        val_file = partitioned_dir / "val" / "val.parquet"
        if not val_file.is_file():
            raise FileNotFoundError(f"Val file not found at {val_file}")
        shard_paths = [val_file]
        out_path = preprocessed_dir / "val.h5"

    print(f"Selected {len(shard_paths)} parquet files for '{args.split}' split.")
    tokenize_to_h5(
        shard_paths, out_path, text_column=args.text_column, max_tokens=args.max_tokens
    )


if __name__ == "__main__":
    main()
