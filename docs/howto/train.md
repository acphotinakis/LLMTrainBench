# Train (UI & CLI)

You can run every stage two ways: from the **command line** (full control, best for long jobs) or from
the **Streamlit control panel** (forms, one-click launch, live logs, charts; see [The UI](ui.md)).

## Install

```bash
pip install -e ".[train]"     # editable install, no more PYTHONPATH=.
# optional: export HF_HOME=/path/to/big/disk/hf_cache  to keep Hugging Face downloads elsewhere
```

## The pipeline, end to end (CLI)

Each command reads its stage JSON from `configs/` (override anything with `--field`, or point at another
file with `--config`). Use `python` for one GPU and `torchrun` for many.

=== "1. Data"

    ```bash
    python scripts/prepare_pretrain_data.py --split val   --out data/pile_dev.h5
    python scripts/prepare_pretrain_data.py --split train --num_shards 1 --out data/pile_train.h5
    python scripts/prepare_sft_data.py
    python scripts/prepare_preference_data.py --source both
    python scripts/prepare_rl_prompts.py
    ```

=== "2. Pretrain"

    ```bash
    # single GPU
    python scripts/pretrain_base.py --config configs/pretrain.json
    # both GPUs (effective batch = batch_size * grad_accum * num_gpus)
    torchrun --standalone --nproc_per_node=2 scripts/pretrain_base.py --config configs/pretrain.json
    ```

=== "3. Align"

    ```bash
    torchrun --standalone --nproc_per_node=2 scripts/train_sft.py
    torchrun --standalone --nproc_per_node=2 scripts/train_reward.py
    torchrun --standalone --nproc_per_node=2 scripts/train_dpo.py --loss_type dpo
    torchrun --standalone --nproc_per_node=2 scripts/train_ppo.py --reward_source verifier
    torchrun --standalone --nproc_per_node=2 scripts/train_grpo.py
    ```

The whole alignment chain in one shot:

```bash
bash scripts/run_posttraining.sh        # SFT → RM → DPO → PPO → GRPO → eval table
```

## Multi-GPU notes

- Pretraining defaults to `epochs: 1` in `configs/pretrain.json`. `--epochs N` takes
  precedence over `train_steps`: the trainer derives the number of optimizer updates
  needed to cover the complete training corpus N times. Use `--epochs none` for an
  explicit step budget, which does not guarantee full coverage.
- All ranks share a deterministic shuffle seeded by `seed + epoch`, then take distinct
  shards. The final context window overlaps the previous window to cover the corpus
  tail. The final global update repeats only enough windows to fill all ranks and
  accumulation microbatches, so no rank runs out early. A corpus shorter than one
  context is edge-padded. Every valid next-token target is included each epoch; the
  first token serves as context because it has no preceding token to predict it from.
- Startup prints corpus tokens, windows, steps per epoch, total step budget, and
  repeated padding windows. `Completed corpus epoch` confirms a complete pass.
  New checkpoints record the sharding contract and last completed update. Resume
  with `--resume PATH` and the same corpus, seed, context, world size, batch size and
  accumulation. Resume seeks directly to the remaining batches in that epoch.
  Old checkpoints lack a deterministic data cursor and are rejected for resume;
  restart a new epoch-based run to establish guaranteed coverage. Running processes
  must be restarted to use the new loader.
- `torchrun --standalone --nproc_per_node=N` launches N data-parallel ranks (DDP + bf16). Only rank 0
  logs and checkpoints.
- On the dev box (2× H100, no NVLink) the educational attention materializes a `(B, n_head, T, T)` tensor
  per block, so memory scales with sequence length: at context 1024 use `--batch_size 8 --grad_accum 12`
  and recover the effective batch via accumulation. Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

For the 10-P4 host, the modern 77m preset shape (actually about 51M parameters) can
be launched with FP32 and the NCCL peer-access workaround:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9 NCCL_P2P_DISABLE=1 \
.venv/bin/torchrun --standalone --nproc_per_node=10 scripts/pretrain_base.py \
  --config configs/pretrain.json --arch modern --n_embed 512 --n_head 8 \
  --n_blocks 8 --context_length 512 --batch_size 2 --grad_accum 1 \
  --amp_dtype none --epochs 1 --out_ckpt models/77m-modern-10gpu-epoch.pt
```

With 302,329,795 training tokens, this resolves to 590,488 windows and 29,525
updates per epoch, with 12 repeated windows in the final global update.

## Where outputs go

- Checkpoints → `models/<stage>.pt` (each carries its own resolved `cfg`).
- Metrics → `logs/<stage>_<timestamp>.jsonl` (one JSON per logged step). The UI plots these
  live; you can also `--use_wandb true` to mirror to Weights & Biases.

Then [evaluate](../08_evaluation.md) on GSM8K and [chat](../09_inference.md) with any checkpoint.
