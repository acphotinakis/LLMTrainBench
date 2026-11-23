# Corpus epoch verification

The change implements the user request to train on the complete corpus using
distributed sharding and an epoch budget. No existing test suite was present, so
checks were run with temporary fixtures rather than introducing a test framework.

- RED: `PYTHONPATH=. .venv/bin/python /tmp/check_corpus_epochs.py` initially failed
  because `CorpusEpochLoader` did not exist.
- GREEN: the same check passed after implementation. Synthetic sequential token
  streams of lengths 2, 7, 17 and 81 covered every valid next-token target across
  three ranks over two epochs, including tails and corpora shorter than a context.
  It checked equal batch counts and deterministic cursor seeking. A divisible
  49-token fixture proved the rank shards were disjoint without padding.
- Integration: two CPU processes trained the modern model on an 81-token fixture,
  with context 4, batch 2 and accumulation 2. One epoch resolved to three optimizer
  updates, completed all 20 windows, evaluated and saved a checkpoint at step 2.
  Resuming with a total budget of two epochs continued at step 3 and completed
  epoch 2 at step 5. Both commands exited successfully.
- Accounting: the actual 302,329,795-token training file resolves to 590,488 windows,
  29,525 updates and 12 repeated padding windows at context 512, ten ranks,
  batch 2 and accumulation 1.
- `git diff --check` and Python compilation of the three changed Python modules
  passed. A full new 10-GPU training run was not launched. No coverage percentage
  was measured, and dropout/optimizer RNG replay is not guaranteed on resume;
  the data order and coverage cursor are deterministic.

The first token is context, not a prediction target. Tail overlap and final-update
padding deliberately repeat a small number of tokens/windows to avoid dropping
data or desynchronizing ranks. Existing unsharded checkpoints are rejected for
resume because their historical data coverage cannot be reconstructed.
