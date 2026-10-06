# Phase 2 Acquire and Organize FineWeb Edu

## Purpose

Create the deterministic datasets specified in `DATA_CARD.md` and the Data section of `BREAKDOWN.md`.

## Tasks

- Stream the pinned FineWeb-Edu source.
- Validate schema and apply frozen normalization and filters.
- Remove duplicate IDs and exact duplicate text.
- Split and order documents with SHA-256.
- Build online-input manifests, offline token arrays, and packed sequences.
- Write the manifest and SHA-256 checksum file.
- Implement every required data validation test.

## Exit Criteria

- Train and validation IDs are disjoint.
- Training subsets are nested byte-for-byte.
- Exact sequence and token counts match `DATA_CARD.md`.
- A locked-environment rebuild produces the same content checksums.

## Outputs

Selected-document archive, ID lists, token arrays, packed datasets, manifest, checksums, and tests.
