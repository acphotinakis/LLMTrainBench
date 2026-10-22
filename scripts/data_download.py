import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
import pyarrow as pa
import glob
import pyarrow.compute as pc
import pyarrow.parquet as pq
import numpy as np

REPO_ID = "alwaysgood/financial-english-source-corpus"
BASE_URL = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main"

# Metadata / manifest files present in the repo root
METADATA_FILES = [
    "README.md",
    "_bundle_manifest.json",
    "_token_stats_qwen35_presplit.json",
]

# Total of 23 training parquet shards in this dataset
TOTAL_SHARDS = 23
TRAIN_FILES = [
    f"train-{i:05d}-of-{TOTAL_SHARDS:05d}.parquet" for i in range(TOTAL_SHARDS)
]

VAL_RATIO = 0.05
RANDOM_SEED = 42


DATA_DIR = Path("data")
DATA_SET_DIR = DATA_DIR / "financial-english-source-corpus"

RAW_DIR = DATA_SET_DIR / "raw"
RAW_TRAIN_DIR = RAW_DIR / "train"
RAW_VAL_DIR = RAW_DIR / "val"

VAL_DIR = DATA_SET_DIR / "val"
VAL_FILE = VAL_DIR / "val.parquet"

# Create all relevant directories
dirs_to_create = [RAW_DIR, RAW_TRAIN_DIR, RAW_VAL_DIR, VAL_DIR]

for directory in dirs_to_create:
    directory.mkdir(parents=True, exist_ok=True)


def make_splits():

    shard_paths = sorted(glob.glob(str(RAW_DIR / "train-*.parquet")))
    if not shard_paths:
        raise FileNotFoundError(f"No parquet files found in {RAW_DIR}")

    print(
        f"Reading {len(shard_paths)} shards to partition {VAL_RATIO*100:.1f}% validation split..."
    )

    val_tables = []

    # Process shard by shard to keep memory bounded
    for idx, shard_path in enumerate(tqdm(shard_paths, desc="Splitting shards")):
        table = pq.read_table(shard_path)
        num_rows = table.num_rows

        if num_rows == 0:
            continue

        # Deterministic generator seeded uniquely per shard
        rng = np.random.default_rng(RANDOM_SEED + idx)
        is_val = rng.random(size=num_rows) < VAL_RATIO

        # Directly invert in NumPy (100% type-safe, eliminates Pylance error)
        val_mask = pa.array(is_val)
        train_mask = pa.array(~is_val)

        val_sub = table.filter(val_mask)
        train_sub = table.filter(train_mask)

        if val_sub.num_rows > 0:
            val_tables.append(val_sub)

        # Write clean train shard without validation rows
        out_train_path = RAW_TRAIN_DIR / f"train-{idx:05d}.parquet"
        pq.write_table(train_sub, out_train_path, compression="snappy")

    # Combine all validation samples into a single unified table
    print("Writing consolidated val.parquet...")
    if val_tables:
        full_val_table = pa.concat_tables(val_tables)
        pq.write_table(full_val_table, VAL_FILE, compression="snappy")
        val_count = full_val_table.num_rows
    else:
        val_count = 0

    print("\nSplit Complete:")
    print(f"Validation rows : {val_count:,} -> {VAL_FILE}")
    print(f"Training shards : {len(shard_paths)} files -> {RAW_TRAIN_DIR}/")


def get_http_session(pool_maxsize: int = 16) -> requests.Session:
    """Configures a requests.Session with connection pooling and automatic retries."""
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
    chunk_size: int = 4 * 1024 * 1024,  # 4 MB chunks for high throughput
) -> str:
    """Streams a file directly with resume safety and dedicated progress bar position."""
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
    dest_dir: Path,
    max_train_files: int,
    download_metadata: bool = True,
    max_workers: int = 8,
) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    session = get_http_session(pool_maxsize=max_workers * 2)

    # 1. Download Metadata Files in Parallel
    if download_metadata:
        print("[1/2] Fetching metadata files...")
        with ThreadPoolExecutor(max_workers=min(len(METADATA_FILES), 4)) as pool:
            futures = {
                pool.submit(
                    download_single_file,
                    session,
                    f"{BASE_URL}/{meta_file}",
                    dest_dir / meta_file,
                    idx,
                ): meta_file
                for idx, meta_file in enumerate(METADATA_FILES)
            }
            for fut in as_completed(futures):
                print(fut.result())

    # 2. Download Parquet Shards in Parallel
    shards_to_download = TRAIN_FILES[:max_train_files]
    print(
        f"\n[2/2] Downloading {len(shards_to_download)} shards with {max_workers} worker threads..."
    )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                download_single_file,
                session,
                f"{BASE_URL}/{filename}",
                dest_dir / filename,
                (idx % max_workers) + 1,  # Cycle bar positions
            ): filename
            for idx, filename in enumerate(shards_to_download)
        }

        # Track global progress across all threads
        with tqdm(
            total=len(futures), desc="Total Shards Completed", position=0
        ) as overall_bar:
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as exc:
                    print(f"Download failed for a shard: {exc}")
                overall_bar.update(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fast concurrent downloader for financial-english-source-corpus."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=RAW_DIR,
        help="Target directory to place raw parquet shards.",
    )
    parser.add_argument(
        "--max_train_files",
        type=int,
        default=23,
        help="Number of parquet shards to download (1-23).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of concurrent download threads (recommended: 4-8).",
    )
    parser.add_argument(
        "--skip_metadata",
        action="store_true",
        help="Skip downloading README and JSON manifests.",
    )

    args = parser.parse_args()
    dest_path = Path(args.output_dir)

    download_dataset(
        dest_dir=dest_path,
        max_train_files=args.max_train_files,
        download_metadata=not args.skip_metadata,
        max_workers=args.workers,
    )
    print("\nAll files successfully downloaded and verified.")

    make_splits()


if __name__ == "__main__":
    main()
