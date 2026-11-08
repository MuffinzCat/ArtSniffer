# Issue #48 research spike: Tail Tagger / Hydra furry semantics

**Research updated:** 2026-11-08
**Scope:** Technical evaluation only. This document records public-source research and the
completed private CPU benchmark. It is not an adoption decision. No ArtSniffer runtime integration,
adapter, dependency, configuration, or model-download mechanism is implemented.

## Executive summary

**Hydra 3.5 / JTP-3.5 remains a candidate for further semantic-quality evaluation; production
adoption is undecided.**

- Hydra exposes a useful semantic vocabulary and a headless inference path separate from Tail
  Tagger's desktop UI. The benchmark confirms that the pinned checkpoint produces 8,886 unique
  tag scores per image on CPU.
- On the tested Ryzen 7 5700G, 8 PyTorch intra-op threads and 1 inter-op thread are the preferred
  allocation for further evaluation: pooled median forward time was 22.721 seconds per image,
  about 5.9% slower than the historical 16-thread reference, while the benchmark process used
  7.93 CPU cores on a 16-logical-CPU host. Twelve threads used substantially more CPU without
  improving latency and had greater timing variability.
- The original three-image benchmark provided one-contrast feasibility evidence: the expected
  strong match ranked above the weak match. A later eight-image Stage 0 evaluation validated the
  blinded workflow and provided limited exploratory semantic evidence. Neither establishes
  representative accuracy, calibration quality, or suitability for adoption.
- The benchmark makes memory appear practical on this host at approximately 3.0–3.3 GiB
  high-water RSS. CPU capacity and service contention, rather than RAM capacity, are the more
  salient operational concern. A bounded background analysis-once-and-cache workflow may tolerate
  the measured latency, but this has not been validated in an ArtSniffer pipeline.
- Generated concepts and rating predictions are not source-provided metadata or safety evidence.
  Any future semantic result must retain its provenance and remain separate from unconditional
  safety evaluation.
- The code, checkpoint, dependency, and training-data licensing questions remain open. The
  benchmark does not resolve rights to redistribute or deploy the model.

## Candidate and integration boundary

RedRocket's Hydra 3.5 is called JTP-3.5 in Tail Tagger's classifier folder. Its model card
identifies it as the successor to JTP-3 Hydra; Tail Tagger's JTP-3.5-specific instructions
recommend it, despite older general README wording that calls JTP-3 the latest. Hydra provides
Python image/model/calibration interfaces and headless invocation options. Tail Tagger's desktop
application, Qt worker management, tag editing, and staging workflows are not required for
headless inference. Its narrow wrapper uses a locally patched vendored Hydra package and should
not be copied without reviewing those patches.

Hydra's vocabulary includes character count, framing, interactions, species, physical traits,
clothing/accessories, and pose concepts. Vocabulary coverage is not evidence that predictions are
accurate or useful for ArtSniffer.

The architectural direction remains:

- preserve official source-provided metadata as its own layer;
- keep generated concepts, raw scores, model/checkpoint version, calibration and implication
  settings, and canonical-trait mapping provenance together but distinct from source tags;
- map generated concepts to provider-neutral canonical traits only through a documented mapping;
- keep semantic signals distinct from global visual embeddings and their scores; and
- never treat Hydra tags or rating predictions as unconditional safety clearance or as a
  substitute for source moderation metadata.

Hydra's `safe`, `questionable`, and `explicit` predictions are classifier outputs, not safety
evidence. They must not override ArtSniffer's subject-bound unconditional safety evaluation,
source-provided moderation information, or other content-policy gates. These are design boundaries,
not implemented pipeline behaviour.

## Benchmark evidence

The full benchmark and follow-up scaling run used the prepared private environment on an Ubuntu
server with an AMD Ryzen 7 5700G (8 cores / 16 logical CPUs), Python 3.12.3, and PyTorch
2.12.1+cpu. The Hydra source checkout was pinned to
`cfa9b0a1ffcf2b8df8553be7673210fd60fba23b`; the checkpoint SHA-256 was
`5e9337c21019c51f2bb5b33d053ea3e2c0412e5ca972b5ea3c4c21e6987452ca`. CUDA and ROCm were absent;
the integrated GPU was not used. The pinned checkpoint produced 8,886 unique scores per image.
The full benchmark used calibration `f1.0@0.1` with implications disabled. No artwork was copied
into scaling results.

The private server-side result directories are:

- Full benchmark: `$HOME/Hydra-3.5-Benchmark-issue48/results/20261107T211512411174Z`
- Thread-scaling summary:
  `$HOME/Hydra-3.5-Benchmark-issue48/results/thread-scaling-20261107T223330Z/summary.json`
  (also visible from Windows at
  `X:\Hydra-3.5-Benchmark-issue48\results\thread-scaling-20261107T223330Z\summary.json`)

### Semantic signal observed

The three authorised images included one existing contrast annotation for `valentijns2`. On raw
non-rating tag-score vectors, excluding `safe`, `questionable`, and `explicit`, the expected
strong match `valentijns1` had cosine similarity **0.990198** and **41** shared calibrated
non-rating tags. The expected weak match, the Beesus headshot, had similarity **0.842686** and
**13** shared calibrated non-rating tags. Thus the expected strong match ranked above the weak
match in this one contrast.

This is descriptive evidence only. The annotation predates the benchmark; it is not new or
independent human ground truth. Three images and one contrast are insufficient to estimate
precision, recall, false-positive/negative rates, calibration quality, robustness across art
styles, or production suitability. The shared-tag counts and cosine values do not establish that
the predictions are correct.

### Stage 0: workflow validation and exploratory semantic findings

Stage 0 completed the privacy-preserving evaluation workflow on eight blindly annotated and locked
images: selection, annotation, locking, frozen provenance, opaque staging, Linux validation, CPU
inference, approved-label filtering and comparison against locked annotations. Hydra 3.5 / JTP-3.5
used eight intra-op threads, one inter-op thread, unchanged `f1.0@0.1` calibration and implications
disabled. All eight images completed successfully in the successful fresh run without retries.
Only the 23 approved Hydra labels mapped from 21 evaluation concepts were persisted: 184 raw
values and 46 calibrated approved-label selections. Rating outputs were neither persisted nor
evaluated; generated semantics provide no safety clearance. The locked annotations remained
unchanged.

Across 160 eligible mapped-label decisions, exploratory totals were **TP 43, FP 2, FN 16 and
TN 99**, giving micro precision **95.6%**, recall **72.9%** and F1 **82.7%**. Seventeen uncertain
and seven not-observable annotations were excluded, not treated as negatives. These results
describe eight non-representative images and must not be generalised to deployment quality.

Character count was exactly correct on all eight images, with exactly one count label selected
each time. Feline and glasses detection showed no observed misses, but feline had no eligible
negatives; collar likewise lacked eligible negatives. Misses were concentrated in framing, poses
and tails. Neither framing label nor wings was emitted despite positive support. Eligible false
positives occurred for hand holding and fox. Hand holding, wolf, dragon, antlers, scales and walking
had zero human-positive support: their positive detection remains **untested**, not demonstrated
to fail.

The first Stage 0 attempt stopped before image processing because the dedicated runner did not
make the pinned Hydra checkout importable under isolated Python execution. That failed run was
preserved. Runner v2 corrected the import-path issue and added privacy-safe diagnostic evidence.
A separate startup-only diagnostic successfully verified import, checkpoint/model initialisation,
CPU placement and calibration without opening artwork or performing inference. The fresh Stage 0
run then completed all eight inputs. This infrastructure failure is not model-quality evidence.

Stage 0 validates the workflow only. It justifies improved coverage in a new blindly annotated,
locked 24-image Stage 1 pilot with the unchanged baseline calibration, not threshold/calibration
tuning from Stage 0, a Stage 0 rerun, adoption or ArtSniffer integration.

### CPU thread-scaling measurements

The follow-up used 4, 8, and 12 intra-op threads, with one inter-op thread. Each configuration ran
in a fresh process, with two warm-ups and seven measured forward-only passes for each of the same
three images: 21 measured samples per setting and 63 new timing samples total. Image order was
rotated between settings. The 8- and 12-thread preflights passed. The original 4-thread preflight
was reliable but inconclusive: estimated mean background activity was 0.770 cores, with a 95%
interval from -0.219 to 1.758 cores and one 5-second block at 2.624 cores. The run correctly
stopped at that point. The user later explicitly authorised continuing despite ordinary
background CPU contention; the original 4-thread preflight was retained, not retried or
discarded. The subsequent 4-thread inference-phase resource assessment was within the configured
contention limit. The primary metric is forward-only inference on preprocessed tensors.

| Intra-op threads | Pooled median | Pooled mean | CV | Process CPU | System busy CPU | Approx. logical capacity not consumed by benchmark process | High-water RSS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 40.281 s | 40.370 s | 0.66% | 3.99 cores | 4.18 cores | 12.0 cores | 3.00 GiB |
| 8 | 22.721 s | 22.724 s | 0.84% | 7.93 cores | 8.27 cores | 8.1 cores | 3.12 GiB |
| 12 | 23.093 s | 23.532 s | 5.49% | 10.46 cores | 10.83 cores | 5.5 cores | 3.08 GiB |

“Approx. logical capacity not consumed” is 16 logical CPUs minus mean benchmark-process CPU use;
it is not a reservation or guarantee of idle capacity for other services. System busy CPU also
includes the benchmark and other host work. The measured inference phases were within the
configured contention limit. However, the retained 4-thread preflight warning means the
configurations should not be presented as all having started under equivalently quiet conditions;
these measurements also do not prove behaviour under every production load.

The 16-thread figure is a **historical, non-concurrent reference** from the earlier full
benchmark, not a fourth setting in the scaling experiment. It used 15 measured forward passes
per image, rather than seven: pooled median **21.466 s**, pooled mean **21.434 s**, approximately
97.6–98.0% system CPU, and approximately **3.28 GiB** high-water RSS. The earlier completed
manifest incorrectly retained `model_loaded: false` and `artwork_opened: false`, despite the
inference and image processing having occurred. Those state flags are a metadata error, not
evidence that the baseline did not run. The follow-up completed manifests correctly record both
as `true`. Earlier Windows timing was excluded because unrelated gaming load contaminated it.

### Interpretation

- Four threads used less CPU but took about **40.3 seconds** per image.
- Eight threads reduced pooled median latency by about **43.6%** relative to four threads. Its
  median was about **5.9% slower** than the historical 16-thread reference. The scaling run used
  about 7.93 benchmark-process CPU cores (8.27 system-busy cores), compared with effectively full
  system CPU use in the earlier 16-thread run.
- Twelve threads consumed about 2.5 more process CPU cores than eight threads, but its pooled
  median was about **1.6% slower** and its CV was substantially higher, with several high timing
  outliers.
- On this host and under these test conditions, **8 intra-op / 1 inter-op thread is the preferred
  allocation for further Hydra background-worker evaluation**. It is not a production default,
  a resource reservation, or a decision to adopt Hydra.
- At approximately 3.0–3.3 GiB high-water RSS, memory appears practical on this 16 GiB server.
  CPU throughput and competition with other services are the primary operational questions.
  Since ArtSniffer intends to analyse candidates once and cache results, approximately 22.7
  seconds per image may be workable for a bounded background worker; queue volume and service
  impact have not been tested.

The comparison is a small operational thread-allocation experiment, not a general performance
characterisation. The 4/8/12 measurements use seven samples per image, whereas 16 uses 15, and
the historical run occurred at another time. Do not present all four settings as one simultaneous,
perfectly identical experiment.

## Licensing and model-distribution questions remain open

Tail Tagger declares MIT. The Hydra repository/model card declares Apache-2.0, but the reviewed
materials did not separately specify code versus checkpoint terms or establish redistribution
rights for the checkpoint and its underlying training artwork. The SigLIP2 base model also has
its own provenance and notices. Dependency licences and the exact redistribution obligations
must be checked for any proposed package. Benchmarking a checkpoint is not a licensing clearance.

Before bundling or distributing weights, clarify the intended scope of the Hydra code/checkpoint
licence with its publisher, review applicable Apache-2.0 notices and modifications, and investigate
training-data provenance and permissions. Do not treat the repository-level licence declaration
as resolving every model, weight, dependency, or training-artwork question.

## Evidence still needed before an adoption decision

Prioritise semantic quality; another CPU benchmark is not the next step unless a concrete
performance question remains.

1. **Build a rights-cleared, representative evaluation set** with sufficiently varied art styles
   and image quality. Include independently annotated examples for character count and framing,
   interactions, species, physical traits, clothing/accessories, pose, and relevant failure or
   ambiguous cases. Establish a sampling and annotation protocol before selecting thresholds.
2. **Measure per-concept quality on held-out examples.** Collect human judgements independent of
   Hydra outputs; report per-tag precision/recall, false-positive and false-negative examples,
   and uncertainty. Avoid treating the three benchmark images or their existing contrast as a
   validation set.
3. **Evaluate calibration and operating points** on held-out labels, including rare concepts.
   Record the checkpoint, calibration identifier and any implication policy. Keep raw scores
   available for evaluation, but do not compare raw scores directly across models.
4. **Test complementarity** against source-provided metadata and the separate global visual
   embedding signal. Distinguish semantic similarity from visual/style/composition similarity and
   evaluate any combination on human-judged examples.
5. **Resolve licensing and data provenance** for Hydra code, checkpoint, base-model notices,
   dependencies, and training artwork before deciding on distribution or operational use.
6. **Only if a concrete service-capacity question remains**, test queue throughput, bounded
   concurrency, cold-load cost, and impact on other server services at the preferred 8/1
   allocation. Do not repeat broad CPU scaling without a decision-relevant question.
7. **After quality and rights evidence**, coordinate a generated-concept result contract with #44:
   preserve raw model labels/scores and provenance, keep source metadata separate, and record
   canonical-trait mapping provenance. Any adapter or runtime integration is out of scope until
   an explicit adoption decision.

## Recommendation

**Continue evaluation; do not adopt or integrate yet.** The pinned Hydra 3.5 checkpoint has
demonstrated feasible CPU inference on the target server and a promising result on one existing
contrast. Stage 0 additionally validated the workflow and provided limited exploratory
false-positive/false-negative evidence. Eight intra-op and one inter-op thread is the best tested
balance for a potential background-worker follow-up. However, the semantic evidence is far too
small for adoption: representative semantic quality and calibration remain unevaluated, and
licensing/model-data questions are unresolved. The next decision-relevant work is the rights-cleared,
blindly annotated and locked Stage 1 semantic-quality pilot with unchanged baseline calibration,
not implementation.

## Sources and related work

- [Issue #48 — Tail Tagger / Joint Tagger Project investigation](https://github.com/MuffinzCat/ArtSniffer/issues/48)
- [Issue #44 — canonical traits and semantic provenance](https://github.com/MuffinzCat/ArtSniffer/issues/44)
- [Issue #62 — visual embedding and furry semantic benchmark](https://github.com/MuffinzCat/ArtSniffer/issues/62)
- [Tail Tagger README](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/README.md)
- [Tail Tagger MIT licence](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/LICENSE)
- [Tail Tagger JTP-3.5 download instructions](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/classifiers/JTP-3.5/DOWNLOAD_INSTRUCTIONS.md)
- [Tail Tagger Hydra inference wrapper](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/classifier/inference/hydra_inference.py)
- [Tail Tagger vendored Hydra patch notes](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/hydra/VENDOR_PATCHES.md)
- [Hydra 3.5 model card at the pinned revision](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/README.md)
- [Hydra 3.5 public tag-list metadata](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/data/jtp-3.5-hydra-tags.csv)
- [SigLIP2 base-model card](https://huggingface.co/google/siglip2-so400m-patch16-naflex)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
