# ArtSniffer

ArtSniffer is a self-hosted personalised artwork discovery and recommendation service.

The goal is to learn a user's visual preferences from curated reference collections, discover new artwork from supported sources, and recommend relevant posts through services such as Discord and Telegram.

## Status

ArtSniffer is currently in early domain and infrastructure development.

Core safety, content-policy, analysis, caching, and recommendation primitives exist. Reference-library and source integrations, end-to-end application orchestration, delivery services, and production deployment remain planned.

## Current Domain Boundaries

The current domain primitives include subject-bound unconditional safety evaluation, profile
content-policy evaluation, service-level content permissions, analysis records and recommendation
scoring. They do not yet form an application pipeline.

`ServiceContentPermissions()` disables adult content by default. Its pure evaluator uses the
provider-neutral `ContentRating` vocabulary:

| Rating | Adult support disabled (default) | Adult support explicitly enabled |
|---|---|---|
| `UNKNOWN` | Rejected | Rejected |
| `GENERAL` | Permitted by the service | Permitted by the service |
| `MATURE` | Permitted by the service | Permitted by the service |
| `ADULT` | Rejected | Permitted by the service |

Service permissions are separate from profile preferences. A general profile still rejects MATURE
and ADULT, and a profile accepting ADULT does not enable service-wide adult support. Neither rating
policy can override unconditional safety or grant destination eligibility.

The intended processing order is:

```text
source metadata / labels -> unconditional safety -> service-level permissions
-> profile content policy -> expensive analysis -> recommendation scoring
-> recommendation eligibility -> destination eligibility -> delivery
```

Only an affirmative bound safety result exposes a `SafetyClearedSubject`. The composed
pre-analysis boundary requires that clearance, preserves its exact artwork/content-version binding,
evaluates service permissions before profile policy, and short-circuits on service rejection.
Approval permits only progression to expensive analysis; it does not grant recommendation or
destination eligibility.

Exact cached image-analysis reuse is available through a provider-neutral helper keyed by artwork
ID, supplied content hash, and analyser model ID. Candidate and reference callers are not yet
integrated, and broader end-to-end application orchestration remains planned. Full adult
compliance, destination opt-in, and platform-specific eligibility also remain later work.

## Planned Recommendation Signals

Global whole-image embeddings are one complementary signal for visual, style and composition
similarity; they are not enough to capture component-level furry semantics such as characters,
interactions, species, clothing or pose. Furry-specific semantic analysis is another signal.
Authoritative source metadata (especially e621/e926 tags) remains distinct from generated concepts,
which retain model, version and confidence provenance. The intended architecture maps these inputs
to provider-neutral canonical traits and signals for separately explainable visual and semantic
scoring. Semantic analysis does not grant unconditional safety clearance. These semantic and
canonical-trait capabilities are planned, not yet implemented.

## Planned Features

ArtSniffer is planned to support:

- Multiple independent recommendation profiles.
- OneDrive-hosted reference artwork collections.
- Visual and semantic artwork similarity.
- Live discovery from supported artwork and social platforms.
- Discord and Telegram recommendation feeds.
- Profile-specific filtering, thresholds, and content controls.
- Recommendation feedback and preference learning.
- Artist affinity, discovery, novelty, and diversity controls.
- Duplicate and previously-seen artwork detection.
- Explainable recommendation scoring.
- Modular reference, source, recommendation, and delivery components.
- Optional content-rating modes with platform-appropriate safeguards.

The project is being designed as a self-hosted service with efficient CPU operation and minimal permanent storage of externally retrieved artwork.

## Development

ArtSniffer currently targets Python 3.12.

Development uses:

- `uv` for project and dependency management.
- Ruff for linting and formatting.
- Pyright for static type checking.
- pytest for automated testing.

## Local Reference Observation

Scan a local reference library once from the command line (quote paths containing spaces):

```powershell
uv run artsniffer references scan-local "C:\References\My Library" --source-id favourites
uv run artsniffer references scan-local "C:\References\My Library" --source-id favourites --json
uv run artsniffer --help
```

Readable output is the default: source, supplied root, total observed item count and each item ID
in provider order. JSON contains `schema_version: 1`, `source_id`, `root`, `item_count` and an `items` array of
`source_item_id` / `content_hash` objects in the same order. JSON `root` preserves the exact argument
text supplied by the caller, not the provider's canonical path. Expected provider/filesystem errors
are reported on stderr with a non-zero exit status and no partial successful result.

The command only observes: it does not persist, analyse, monitor, configure sources or retrieve
temporary copies. It does not decode, validate or establish the safety of image content. The
separate synthetic recommendation demo remains available with `uv run python -m artsniffer.demo`.

`LocalFilesystemReferenceProvider(source_id, root: Path)` in
[`artsniffer.references.local_filesystem`](src/artsniffer/references/local_filesystem.py)
binds a canonical directory and implements the `ReferenceProvider` observation contract.
`observe()` recursively includes hidden entries and returns a tuple sorted by exact root-relative
POSIX path IDs, preserving filename case, whitespace and Unicode. It selects JPEG (`.jpg`/`.jpeg`),
PNG, WebP, GIF, BMP and TIFF (`.tif`/`.tiff`) suffixes case-insensitively, without decoding images
or establishing their validity or safety. Each file is read in bounded chunks and identified by
`sha256:<lowercase hex digest>`; metadata never substitutes for hashing.

The provider makes no intentional writes, temporary copies or caches. Symlinks and Windows junctions
are rejected, and traversal/read failures or detected file changes abort the whole snapshot rather
than return partial success. Use an operator-controlled, reasonably quiescent directory tree:
portable checks do not guarantee atomic snapshots or hostile-race-resistant confinement. Filesystem
reads may update access times or hydrate cloud-backed files.

### Compare against a saved scan

Save a successful JSON scan, then compare the same source against the current directory:

```powershell
uv run artsniffer references scan-local "C:\References\My Library" --source-id favourites --json |
    Set-Content -Encoding utf8 "C:\References\baseline.json"
uv run artsniffer references diff-local "C:\References\My Library" --source-id favourites --against "C:\References\baseline.json"
uv run artsniffer references diff-local "C:\References\My Library" --source-id favourites --against "C:\References\baseline.json" --json
```

Check that the scan succeeded before using its output as a baseline. Saving the baseline is an
explicit shell operation; neither command writes to the reference library or modifies a baseline.
Keep snapshots outside the scanned library where practical.

Readable diff output includes source, supplied root and baseline path, then category counts.
For a directory with 18 unchanged items:

```text
Added: 0
Changed: 0
Unchanged: 18
Removed: 0
```

Added, changed and removed item IDs are listed indented beneath their categories; unchanged IDs
are omitted from readable output. Items match by exact `source_item_id`, without case, whitespace
or Unicode normalisation. Matching hashes mean unchanged; differing hashes mean changed. Identical
hashes on different IDs are valid and do not match those items: a rename is an addition and removal.
Current items, including additions, retain provider order; removals are sorted by exact item ID.

The baseline must be a UTF-8 JSON object (a UTF-8 BOM is accepted). Existing unversioned
`scan-local` snapshots remain supported; new scans include integer `schema_version: 1`.
Unknown versions, duplicate JSON keys, non-standard NaN/Infinity values, invalid encoding, missing
or extra fields and incorrect field types are errors. Required fields are:

- `source_id`: a non-blank string exactly matching `--source-id`.
- `root`: a non-blank historical string; it need not exist or match the current root and is never
  accessed.
- `item_count`: a non-negative integer, not a boolean, equal to the number of items.
- `items`: an array of objects containing only non-blank string `source_item_id` and `content_hash`.
  Each hash must be `sha256:` followed by 64 lowercase hexadecimal digits. Every item ID must be
  unique, even when duplicate entries have the same hash. Item IDs are opaque and are never opened
  as baseline paths.

`--json` produces a stable, two-space-indented object with these fields:

- `schema_version`: `1` for the diff output format.
- `source_id`, `root`, `against`: the exact arguments supplied by the caller.
- `counts`: integer `added`, `changed`, `unchanged` and `removed` counts.
- `changes`: ordered entries for **all** results, including unchanged items, with `kind`,
  `source_item_id`, `previous_content_hash` and `current_content_hash`. The absent hash is `null`
  for additions/removals. Current entries come first, then sorted removals.

Baseline validation completes before the provider is constructed. A valid comparison scans exactly
once and returns exit status **0**, even when differences exist. Expected baseline/provider errors
return **1**, with useful stderr, no traceback and no partial successful stdout; CLI usage errors
return **2**. The baseline is not updated automatically. This is a read-only, one-off comparison,
not persistence, artwork identity allocation, analysis, caching or monitoring; the provider's
non-atomic scan and filesystem-read caveats above still apply.

The provider-neutral `ReferenceSnapshotChange` and `diff_reference_snapshots` in
[`artsniffer.references.snapshot_diff`](src/artsniffer/references/snapshot_diff.py) compare previous
and current observations without creating `ArtworkRecord` identities. The existing
artwork-record comparison remains separate and unchanged.

This is an observation primitive only. Application configuration, polling, temporary retrieval,
analysis integration and OneDrive integration remain planned; it does not complete issue #39.

### Create, inspect, compare, and refresh snapshots

The snapshot commands save and manage observation metadata only. Keep snapshot and state files
outside the reference library; commands that write refuse destinations inside the scanned root.
Paths containing spaces can be quoted directly or assigned to PowerShell variables:

```powershell
$root = "C:\References\My Library"
$source = "favourites"
$snapshot = "C:\References\favourites.snapshot.json"
$state = "C:\ArtSniffer\state\favourites.json"
$previous = "C:\References\favourites-previous.json"

# One-off live scan; existing scan-local output remains available.
uv run artsniffer references scan-local $root --source-id $source
uv run artsniffer references scan-local $root --source-id $source --json

# Create a saved snapshot, validate or inspect it, and compare two saved snapshots.
uv run artsniffer references snapshot create $root --source-id $source --output $snapshot
uv run artsniffer references snapshot validate $snapshot --source-id $source
uv run artsniffer references snapshot show $snapshot --items --json
uv run artsniffer references snapshot diff $previous $snapshot --json

# Compare saved observations with a live scan, or preview/update managed state.
uv run artsniffer references diff-local $root --source-id $source --against $snapshot
uv run artsniffer references refresh-local $root --source-id $source --state $state --dry-run --json
uv run artsniffer references refresh-local $root --source-id $source --state $state
```

`snapshot create` refuses an existing destination; pass `--force` to replace it. A successful
create writes a version-1 snapshot, then prints a concise result (or command-result JSON with
`--json`); that result JSON is separate from the snapshot file. `validate`, `show`, and snapshot
`diff` read and strictly validate saved files without scanning a provider or rewriting either file.
`show` lists opaque item IDs only with `--items`; JSON includes hashes when the item list is
requested. Snapshot-to-snapshot comparisons return **0** when valid, including when differences
exist, and retain current-item order followed by sorted removals.

`refresh-local` treats missing state as empty. A successful non-dry-run refresh writes the complete
current version-1 snapshot, including when nothing changed; `--dry-run` reports the same comparison
without writing. Existing state is fully validated and its source ID checked before the live scan.
Legacy unversioned snapshots and UTF-8 files with or without a BOM can be read; merely validating,
showing, or comparing a legacy snapshot never migrates it. A create or successful refresh writes
version 1.

Snapshot/state files contain the source ID, supplied root text, opaque item IDs, and content hashes;
they contain no artwork bytes and are not `ArtworkRecord` identities or analysis-cache records.
These commands do not analyse images, use the SQLite analysis cache, or provide history/monitoring.

Before publication, output is completely serialised and written to a task-owned temporary file in
the destination directory, then flushed and closed. Create-only publication does not overwrite an
existing destination; `--force` and refresh of existing state use same-directory replacement. A
first refresh uses create-only publication. Expected failures before publication preserve existing
file bytes, and only the task-owned temporary file is cleaned up. Atomicity depends on the host
filesystem's support and semantics; this is not a crash-durability guarantee, and the filesystem
scan itself is not atomic. Reads may update access times or hydrate cloud-backed files, as described
above.

Expected filesystem, provider, validation, overwrite, and write errors return **1** with diagnostics
on stderr and no success output. Successful commands return **0**; argparse usage errors return
**2**. The live provider remains read-only, but it does not make reference content valid or safe.
Monitoring, OneDrive, temporary image retrieval, safety/analyser orchestration, and cache
integration remain unfinished work under issue #39 and related issues.

## Local Benchmarks

Provider-neutral benchmark records live in `artsniffer.benchmark.models`, and timing runners live
in `artsniffer.benchmark.runner`. Production image analysers remain in `artsniffer.analysis`.

Keep local benchmark artwork in `benchmark-data/images/` with its original filenames, and keep
generated benchmark results within `benchmark-data/` too. Git ignores `benchmark-data/` directories
at any depth; artwork and results must never be committed. No `dataset.toml` format is defined yet.
Issue #62 tracks the broader multi-model furry-art benchmark.

The DINOv2 analyser uses `facebook/dinov2-small` and requires the optional `benchmark-dinov2`
dependency group. Run its tests with `uv run --group benchmark-dinov2 pytest` (or select that group
for the other development checks). Tests mock model loading and image access; they do not download
weights or read benchmark artwork. Constructing the real analyser may download uncached model files.

## Copyright and Usage

Copyright © 2026 Muffin. All rights reserved.

This repository is **source-available but not open source**.

No licence is granted to use, copy, modify, distribute, sublicense, or create derivative works from the source code in this repository except where permission is required by applicable law or provided by the applicable hosting platform's terms.

Viewing or forking this repository through GitHub does not grant a licence to use, modify, or redistribute the software outside the rights provided by GitHub's applicable terms.

If you would like permission to use any part of ArtSniffer, please contact the repository owner through GitHub.

See [`NOTICE.md`](NOTICE.md) for the full copyright and usage notice.