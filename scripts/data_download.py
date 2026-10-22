#!/usr/bin/env python3
"""
Downloads raw Parquet shards from Hugging Face and splits them deterministically
into train shards and a consolidated validation file.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

REPO_ID = "alwaysgood/financial-english-source-corpus"
BASE_URL = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main"

METADATA_FILES = [
    "README.md",
    "_bundle_manifest.json",
    "_token_stats_qwen35_presplit.json",
]

TOTAL_SHARDS = 23
TRAIN_FILES = [
    f"train-{i:05d}-of-{TOTAL_SHARDS:05d}.parquet" for i in range(TOTAL_SHARDS)
]


def get_http_session(pool_maxsize: int = 16) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=pool_maxsize,
        pool_maxsize=pool_maxsize,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def download_single_file(
    session: requests.Session,
    url: str,
    dest_path: Path,
    position: int = 0,
    chunk_size: int = 4 * 1024 * 1024,
) -> str:
    if dest_path.exists():
        return f"[Skipped] {dest_path.name} already exists."

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    with session.get(url, stream=True, timeout=30) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))

        with (
            open(temp_path, "wb") as f,
            tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=dest_path.name[:25],
                position=position,
                leave=False,
            ) as pbar,
        ):
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

    temp_path.replace(dest_path)
    return f"[Done] {dest_path.name}"


def download_dataset(
    raw_dir: Path,
    max_train_files: int,
    download_metadata: bool = True,
    max_workers: int = 8,
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = get_http_session(pool_maxsize=max_workers * 2)

    if download_metadata:
        print("[1/2] Fetching metadata files...")
        with ThreadPoolExecutor(max_workers=min(len(METADATA_FILES), 4)) as pool:
            futures = {
                pool.submit(
                    download_single_file,
                    session,
                    f"{BASE_URL}/{meta}",
                    raw_dir / meta,
                    idx,
                ): meta
                for idx, meta in enumerate(METADATA_FILES)
            }
            for fut in as_completed(futures):
                print(fut.result())

    shards_to_download = TRAIN_FILES[:max_train_files]
    print(
        f"\n[2/2] Downloading {len(shards_to_download)} shards with {max_workers} threads..."
    )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                download_single_file,
                session,
                f"{BASE_URL}/{filename}",
                raw_dir / filename,
                (idx % max_workers) + 1,
            ): filename
            for idx, filename in enumerate(shards_to_download)
        }

        with tqdm(
            total=len(futures), desc="Total Shards Completed", position=0
        ) as overall_bar:
            for fut in as_completed(futures):
                fut.result()
                overall_bar.update(1)


def make_splits(
    raw_dir: Path,
    train_out_dir: Path,
    val_out_file: Path,
    val_ratio: float = 0.05,
    seed: int = 42,
) -> None:
    shard_paths = sorted(raw_dir.glob("train-*.parquet"))
    if not shard_paths:
        raise FileNotFoundError(f"No parquet shards found in {raw_dir}")

    train_out_dir.mkdir(parents=True, exist_ok=True)
    val_out_file.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"\nPartitioning {len(shard_paths)} shards ({val_ratio * 100:.1f}% validation)..."
    )
    val_tables: list[pa.Table] = []

    for idx, shard_path in enumerate(tqdm(shard_paths, desc="Splitting shards")):
        table = pq.read_table(shard_path)
        if table.num_rows == 0:
            continue

        rng = np.random.default_rng(seed + idx)
        is_val = rng.random(size=table.num_rows) < val_ratio

        val_sub = table.filter(pa.array(is_val))
        train_sub = table.filter(pa.array(~is_val))

        if val_sub.num_rows > 0:
            val_tables.append(val_sub)

        # Preserve standard shard naming for downstream indexing
        out_train_path = train_out_dir / f"train-{idx:05d}.parquet"
        pq.write_table(train_sub, out_train_path, compression="snappy")

    if val_tables:
        print("Writing consolidated val.parquet...")
        full_val_table = pa.concat_tables(val_tables)
        pq.write_table(full_val_table, val_out_file, compression="snappy")
        val_count = full_val_table.num_rows
    else:
        val_count = 0

    print("\nSplit Complete:")
    print(f"  Validation rows : {val_count:,} -> {val_out_file}")
    print(f"  Training shards : {len(shard_paths)} files -> {train_out_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and split dataset shards.")
    parser.add_argument(
        "--base_dir", type=Path, default=Path("data/financial-english-source-corpus")
    )
    parser.add_argument("--max_train_files", type=int, default=23)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--val_ratio", type=float, default=0.05)
    parser.add_argument("--skip_metadata", action="store_true")
    parser.add_argument("--skip_download", action="store_true")
    args = parser.parse_args()

    raw_dir = args.base_dir / "raw"
    partitioned_train = args.base_dir / "partitioned" / "train"
    partitioned_val = args.base_dir / "partitioned" / "val" / "val.parquet"

    if not args.skip_download:
        download_dataset(
            raw_dir=raw_dir,
            max_train_files=args.max_train_files,
            download_metadata=not args.skip_metadata,
            max_workers=args.workers,
        )

    make_splits(
        raw_dir=raw_dir,
        train_out_dir=partitioned_train,
        val_out_file=partitioned_val,
        val_ratio=args.val_ratio,
    )


if __name__ == "__main__":
    main()
