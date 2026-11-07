# Issue #48 research spike: Tail Tagger / Hydra furry semantics

**Research date:** 2026-11-07

**Scope:** Research only. No ArtSniffer production code or issue was changed. No model weights
were downloaded, no inference was run, and ArtSniffer's private benchmark-data directory and
artwork were not accessed. The public Hydra tag-list metadata was inspected.

## Executive summary

**Recommendation: conditional go for a bounded empirical benchmark of Hydra 3.5; no production
adoption or adapter decision yet.**

- **Primary candidate:** RedRocket's **Hydra 3.5**, called **JTP-3.5** in Tail Tagger's classifier
  folder. Its model card calls it the successor to JTP-3 Hydra; Tail Tagger's dedicated JTP-3.5
  download instructions call it the newest, most accurate, recommended default. Do not select the
  older JTP-3 solely because Tail Tagger's general README still calls JTP-3 its recommendation.
- **Good integration shape:** the inference itself is separable from Tail Tagger's PySide6 desktop
  application. Hydra exposes Python model/image/calibration functions, a CLI, and a local FastAPI
  service. Tail Tagger also has a narrow Hydra inference wrapper, but its vendored code has local
  patches and should not be copied without reviewing them.
- **Semantically relevant vocabulary exists:** the public JTP-3.5 tag list contains `solo`, `duo`,
  `group`, `hug`, `headshot_portrait`, `portrait`, `icon`, species tags, physical-trait tags,
  clothing/accessory tags and pose tags. This is evidence of vocabulary coverage, not evidence that
  predictions are accurate or useful for ArtSniffer.
- **Separate licensing and deployment checks remain:** Tail Tagger declares MIT. The Hydra model
  repository declares Apache-2.0 for the repository, but does not publish separate code-versus-
  weights licensing terms or a standalone `LICENSE` file in the reviewed file listing. The
  reviewed model licensing materials do not independently establish redistribution rights for the
  underlying training artwork. Treat model/checkpoint licensing and training-data provenance as
  separate review questions.
- **No performance conclusion is justified:** upstream supports CPU execution, but publishes no
  applicable Ryzen 7 5700G timing or RAM requirement. Its only comparative CPU note concerns a
  hosted demo and has no benchmark conditions. Weight size is about 1.06 GB; inference memory is
  unknown.
- **Preserve boundaries:** generated concepts should be stored with per-tag scores and model /
  calibration provenance, mapped into canonical traits without replacing official e621/e926
  metadata, kept distinct from DINO-style global embeddings, and never used as unconditional
  safety clearance.

## Projects and versions examined

| Project / artifact | Reviewed version or evidence | Finding |
|---|---|---|
| [Tail Tagger](https://github.com/renfald/tail-tagger/tree/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2) | `main` commit `e13c0917` (2026-10-23) | PySide6 desktop app; includes `JTP-3.5` support and a dedicated model instruction file. |
| [RedRocket/Hydra](https://huggingface.co/RedRocket/Hydra/tree/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b) | Current reviewed Hub revision `cfa9b0a1`; Hydra 3.5 release commit `00664f` (2026-05-12) | Hydra 3.5 is a SigLIP2 fine-tune and the stated successor to JTP-3 Hydra. |
| [RedRocket/JTP-3](https://huggingface.co/RedRocket/JTP-3) | Historical model card | JTP-3 Hydra is the preceding model; its published vocabulary is smaller than the Hydra 3.5 claim. |
| [RedRocket/JointTaggerProject](https://huggingface.co/RedRocket/JointTaggerProject) | Historical project card | Earlier project history points to PILOT / PILOT2 and then JTP-3; it is context, not the current model recommendation. |
| [Google SigLIP2 So400m Patch16 NAFlex](https://huggingface.co/google/siglip2-so400m-patch16-naflex) | Hydra base-model card | Identified by Hydra as its base image encoder; the base-model card declares Apache-2.0. |

Hydra's current model card and Tail Tagger's JTP-3.5-specific instructions are the strongest
recommendation evidence reviewed. Tail Tagger's general README still describes JTP-3 as “latest”
and “recommended”; that wording conflicts with its newer, explicit JTP-3.5 instructions and should
be treated as stale. The upstream project now uses both “Hydra 3.5” and “JTP-3.5” naming.

## Findings against the issue checklist

### 1–5. Code reuse, licences, redistribution, and headless inference

**Tail Tagger code-reuse boundary.** Tail Tagger is a manual tagging desktop application, not an
inference library. UI panels, image grid/navigation, tag editing, staging files, GUI settings,
Qt worker management and bulk-curation workflows are application concerns and are not needed for
ArtSniffer. The narrower [Hydra inference wrapper](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/classifier/inference/hydra_inference.py)
loads the model, uses Hydra preprocessing, and returns raw per-tag scores; its
[classifier manager](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/classifier/classifier_manager.py)
is coupled to PySide6 and owns application state and postprocessing. The wrapper imports Tail
Tagger's vendored `tail_tagger.hydra` package rather than a separately published Tail Tagger
inference distribution.

Tail Tagger's [vendor patch notes](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/hydra/VENDOR_PATCHES.md)
identify the vendored code as a copy of RedRocket's Hydra package and document Python compatibility
changes plus an activation binding fix. This makes the patch note and upstream Hydra revision
important if code is reused. It also argues against copying the entire Tail Tagger desktop
application.

**Licences must not be conflated.**

| Component | Upstream licensing evidence | Spike interpretation |
|---|---|---|
| Tail Tagger application | Its [LICENSE](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/LICENSE) is MIT, copyright Tail Tagger Contributors. | Reuse of Tail Tagger-originated code requires retaining its copyright and MIT permission notice. |
| Hydra repository code and checkpoint | The [Hydra model card](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/README.md) declares `license: apache-2.0`. The reviewed Hub file listing did not include a separate `LICENSE` file, and the card does not provide distinct code and weight terms. | Apache-2.0 is the upstream repository-level declaration for the hosted project; upstream does not separately spell out code-versus-checkpoint terms in the reviewed materials. Confirm the intended scope with RedRocket before redistribution. |
| Historical JTP-3 / Joint Tagger Project | Their Hugging Face model cards declare Apache-2.0. | Historical project/model declarations; not a reason to select JTP-3 over Hydra 3.5. |
| SigLIP2 base model | The [Google model card](https://huggingface.co/google/siglip2-so400m-patch16-naflex) declares Apache-2.0. | Keep base-model provenance and its notices in any redistributed package. |

Apache-2.0 redistribution requires, among other conditions, supplying a copy of the licence,
preserving applicable copyright/patent/trademark/attribution notices, and marking modified files;
retain any applicable `NOTICE` content. MIT requires including its copyright and permission notice.
No non-commercial-only clause was found in the cited MIT or Apache declarations. However, the Hydra
card says the training images came from e621 and describes extensive dataset curation. The reviewed
model licensing materials do not independently establish redistribution rights for the underlying
training artwork. Treat model/checkpoint licensing and training-data provenance as separate review
questions. Do not bundle weights into ArtSniffer until the model-code, checkpoint, dependency, and
training-data provenance questions have been reviewed.

**Headless invocation is supported by upstream; UI embedding is unnecessary.** RedRocket publishes
`inference.py` for local classification and `service.py` with a `POST /classify` endpoint. The
service defaults to loopback (`127.0.0.1`) and documents image input. The Python `hydra` subpackage
also exposes `load_model()`, `Hydra.load_image()`, `Hydra.forward()` and `Hydra.calibrate()`. Tail
Tagger's wrapper likewise separates load / preprocess / raw forward from its UI postprocessing.
These are viable inference boundaries, though not a maintained, versioned ArtSniffer API. The
upstream requirements file still includes PySide6 even though a minimal direct Python inference
path need not embed or display the desktop UI.

### 6. Smallest relevant upstream modules

The smallest practical boundary is the upstream `hydra` package plus an ArtSniffer-owned adapter
around input/output and provenance, or the upstream local service if process isolation is desired:

| Responsibility | Smallest relevant upstream path(s) | Notes |
|---|---|---|
| Image preprocessing | [`hydra/model.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/model.py), [`hydra/image.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/image.py) | `ImageConfig`, `open_image()` and `load_image()` implement model-driven background, resize, sRGB and patch handling. |
| Model loading | [`hydra/model.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/model.py) | `load_model()` reads model metadata and safetensors parameters; model labels/validation are embedded for Hydra 3.5. |
| Backbone and prediction | [`hydra/siglip2.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/siglip2.py), [`hydra/pool.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/pool.py), [`hydra/head.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/head.py), `Hydra.forward()` in `hydra/model.py` | SigLIP2 NaFlex image features feed learned per-tag attention pooling and output heads. `inference.py` supplies a batch runner. |
| Tag vocabulary and categories | [`hydra/label.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/label.py), embedded model metadata, and [`data/jtp-3.5-hydra-tags.csv`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/data/jtp-3.5-hydra-tags.csv) | Labels carry categories and implication links. Hydra 3.5's model metadata is self-contained; the CSV is useful for inspection, not needed by its loader. |
| Confidence/calibration and implications | [`hydra/classification.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/hydra/classification.py), `Hydra.calibrate()` in `hydra/model.py` | Per-label validation data determines thresholds for the selected metric; the caller can apply implication modes. |
| Headless CLI/service | [`inference.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/inference.py), [`service.py`](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/service.py) | Provides command-line/batch and HTTP options without embedding Tail Tagger's desktop UI. |

### 7–12. Python, operating systems, Docker, CPU/GPU, storage, and memory

- **Python 3.12:** Tail Tagger's README and setup scripts explicitly support Python 3.10–3.12. Hydra's
  Windows [installer](https://huggingface.co/RedRocket/Hydra/blob/main/install.bat) tries Python
  3.13, 3.12 and 3.11 in order, and its Linux instructions require Python 3.11 or newer. This is
  direct installer compatibility evidence for 3.12, but not proof of a Hydra 3.12 CI/test matrix;
  no such matrix was found in the reviewed upstream materials.
- **Windows:** Hydra provides a Windows `.bat` installer and run scripts. Tail Tagger documents Windows setup and optional NVIDIA acceleration. This is positive platform evidence; it does not prove that every dependency wheel or every GPU backend works on every Windows configuration.
- **Linux:** Hydra documents a Python virtual-environment install and CLI invocation; Tail Tagger provides Linux setup scripts and a CPU-only option. Hydra's headless service is also documented. Linux support is directly evidenced.
- **Docker:** Neither reviewed upstream file listing provided a Dockerfile or official image. A container appears technically feasible because inference is a Python process and the model is a local file, but this is an integration hypothesis, not upstream-validated Docker support.
- **Native/system dependencies:** Hydra lists PyTorch, NumPy, `pyvips[binary]`, einops and safetensors, plus FastAPI/Uvicorn and PySide6 in its full requirements. Tail Tagger additionally lists torchvision, timm and Pillow. Image processing uses pyvips/libvips; PyTorch is a native runtime dependency. The optional `--varlen` path requires flash-attention support. A minimal headless image may be smaller than installing the whole desktop application's dependencies, but that needs a clean packaging experiment.
- **CPU:** CPU is supported in Tail Tagger's setup and Hydra's inference code selects CPU when CUDA is unavailable (the service can be explicitly started with `-d cpu`). The Hydra card's “~400x slower” statement refers to its free hosted CPU demo versus running locally; it provides no workload, hardware or timing methodology. It is not a usable production performance estimate.
- **Ryzen 7 5700G:** No upstream Ryzen 7 5700G measurement was found. CPU support makes an empirical test plausible, but its acceptable latency/throughput is unknown. Do not assume it is fast enough.
- **GPU:** PyTorch device selection supports optional acceleration; Tail Tagger offers CUDA setup and Linux ROCm setup. GPU support is an optional performance route, not a requirement for the proposed ArtSniffer evaluation or production design. Hydra's own README documents CUDA selection; the reviewed Hydra install instructions do not establish an equivalent supported ROCm recipe.
- **Weight storage:** The authoritative Hub tree reports `models/hydra-3.5.safetensors` as **1,064,526,448 bytes** (about **1.06 GB / 0.99 GiB**). Tail Tagger's dedicated instruction says this single file is sufficient for Hydra 3.5 and describes the labels/validation data as embedded. The same Hub repository also carries the older JTP-3 checkpoint (1,002,587,976 bytes); it is not required for a Hydra 3.5-only deployment.
- **Runtime memory:** No official RAM/peak-memory requirement or measured CPU memory figure was found. Batch-size guidance discusses higher GPU VRAM use for larger batches, but does not provide a number. The model's file size must not be presented as an inference RAM estimate.

### 13–18. Inference shape, thresholds, tag types, and concept coverage

- **Single and batch inference:** The model can classify one image through the CLI or `POST /classify`; its `inference.py` accepts files/directories and batches work with a batch-size option. The service also exposes a maximum batch size. Tail Tagger's wrapper is single-image oriented, while its desktop app has bulk tagging. ArtSniffer can choose its own batching boundary; batch support does not require adopting the GUI.
- **Scores and thresholds:** The forward head returns a sigmoid score per label in `[0, 1]`. These are raw model scores, not a universal thresholded tag list. `Calibration` derives a separate decision threshold for each tag from the embedded validation data for a selected metric. The CLI default is `f1.0@0.1`; Hydra's UI describes a confidence slider that selects an F-score trade-off (F4 to F0.25), rather than applying one flat probability cutoff. A further lower-bound threshold is available. The calibration metric, threshold configuration and any implication mode therefore affect which concepts are emitted.
- **Implications:** The model is trained with tag implications, but raw predictions are not constrained by them. Hydra supports modes that inherit, constrain, enforce, remove, or disable implications. A tag added or altered by implication processing must not be represented as an independent raw model observation; preserve raw output separately from derived/implied output if that option is used.
- **Number/type of concepts:** Hydra's card says it predicts 8,886 popular e621 tags. Its Usage Notes instead say 8,884 e621 tags plus three rating meta-tags. The public `jtp-3.5-hydra-tags.csv` has 8,888 non-header rows when counted. These upstream counts do not agree; verify the exact embedded labels for a pinned checkpoint before using a number as a contract. The categories include general, character, species, copyright, meta, lore and rating (with additional categories supported by the code).
- **Representative vocabulary:** Direct inspection of the public tag-list metadata found:
  - **Solo / character count:** `solo`, `duo`, and `group` exist. The exact strings `multiple_characters` and `2_characters` were not found in the checked list; this does not prove the concepts cannot be represented by other labels.
  - **Framing:** `headshot_portrait`, `portrait`, `icon`, `bust_portrait`, `half-length_portrait` and `full-length_portrait` exist. These are e621 labels, not a calibrated ArtSniffer framing ontology.
  - **Interaction:** `hug` exists. Exact `hugging` and `embrace` labels were not found. Tag-list presence is not evidence that the classifier reliably detects an embrace.
  - **Species / physical traits:** Species-category examples include `fox`, `wolf`, `canine` and `felid`; general tags cover traits such as `tail`, `horn`, `fur` and their variants.
  - **Clothing/accessories and pose:** General tags include `clothing`, `dress`, `shirt`, `collar`, `accessory`, `pose`, `sitting` and `standing`.

  Hydra's card says its initial tag selection included general tags with at least 1,200 examples,
  species and character tags with at least 500, and selected copyright/meta/lore labels. Therefore
  the model vocabulary is curated and incomplete, not an exhaustive character-trait schema. These
  vocabulary checks establish only that labels are available for output; accuracy and useful
  granularity require the #62-style contrast benchmark.

### 19–23. Limitations, provenance, safety separation, internal representations, and complementarity

- **Known limits and bias:** Hydra says it was trained on e621 images, not photos of people or real
  animals, and does not support those domains. It documents transparent pixels as composited against
  white and a default effective 512×512-equivalent input, with aspect ratio preserved by NAFlex.
  The label-frequency selection and e621-specific tag conventions bias coverage toward that
  source's distribution and vocabulary. The card describes manual correction/masking of tag
  implications and inconsistent annotations, but publishes no per-concept error rates or
  hallucination rate. False positives/negatives on ArtSniffer's intended artwork remain unknown.
- **Confidence and model/version provenance:** The inference path can provide an ordered label list
  and raw per-label scores; Hydra has model labels, validation data and a model identifier/revision.
  A generated concept can therefore retain a raw score and model/version provenance. For reliable
  replay or interpretation, ArtSniffer would additionally need to record the exact checkpoint
  digest, input/preprocessing version, calibration metric/configuration and whether implication
  processing changed the output. Mapping to a canonical trait should preserve the original label,
  score and mapping provenance, rather than flattening everything to a bare string. This is a
  proposed data contract, not existing ArtSniffer behaviour.
- **Official source tags remain distinct:** an e621/e926 API/post tag is source-provided evidence
  with source provenance; Hydra predictions are model-generated evidence. They must not be merged
  into a single indistinguishable `tags` set or allowed to overwrite each other. The source's tags
  and rating/moderation metadata remain authoritative for that source.
- **Safety remains separate:** Hydra can predict `safe`, `questionable` and `explicit` labels, but
  these are classifier outputs from the same model, not unconditional safety evidence. They must
  never create, override or grant a `SafetyClearedSubject` or other unconditional clearance. Safety
  and content-rating decisions must continue to use their independent, authoritative evidence and
  policy path.
- **Global visual embeddings remain separate:** Hydra is a multi-label semantic classifier, not a
  drop-in replacement for the global image representation used for visual similarity. DINO-style
  embeddings can capture whole-image/style/composition resemblance; Hydra labels can expose
  selected component semantics. Their raw scores are not directly comparable or interchangeable.
- **Internal visual representation:** The code exposes the SigLIP2/NaFlex image-feature path before
  Hydra's learned per-tag cross-attention pooling and tag heads. Such activations are technically
  inspectable from the implementation, but the reviewed project documents a classifier output, not
  a stable general-purpose image-embedding API or retrieval objective. No empirical evidence here
  justifies using those internals as an ArtSniffer embedding; treat that as a separate optional
  experiment, not part of this recommendation.
- **Fit with #44 and #62:** #62 explicitly treats furry taggers as a separate signal family,
  requires contrast examples for character count/framing/interactions/species/traits/clothing/pose,
  and says generic embeddings alone cannot select the complete stack. #44 requires provider-neutral
  canonical traits with source/generated provenance and says not to overload
  [`ArtworkAnalysis.tags`](../../src/artsniffer/analysis/artwork.py). The current
  [`ImageAnalyser`](../../src/artsniffer/analysis/image_analyser.py) seam returns one
  [`ArtworkAnalysis`](../../src/artsniffer/analysis/artwork.py); it does not provide per-tag
  confidence or a semantic result contract. An eventual integration should be a separate analysis
  result/adapter (or a deliberately designed extension under #44), not a GUI dependency or a change
  that conflates embedding, source metadata, generated tags and safety.

## Unknowns and empirical tests still required

No quality, latency, throughput, memory, or Ryzen performance number was measured or inferred in
this spike. Before adoption:

1. **Quality:** Use an appropriately rights-cleared evaluation set and contrast pairs to judge solo
   versus multiple characters, headshot/icon versus wider framing, interaction versus no
   interaction, species, physical traits, clothing/accessories and pose. Record per-concept false
   positives/negatives and failures across art styles. Do not use the private benchmark data without
   its designated access/approval.
2. **Complementarity:** Compare human-judged results for Hydra 3.5 semantics, DINO/global visual
   similarity, official source metadata where available, and carefully separated combinations.
   Record whether each result is visually similar, semantically similar, or both; do not compare
   uncalibrated raw scores across models.
3. **Calibration:** Measure per-tag precision/recall and calibration behaviour on held-out examples,
   including rare tags, implication modes and the confidence/F-score trade-off. Verify exact
   checkpoint labels because upstream count sources disagree.
4. **Operations:** On the Ryzen 7 5700G, measure cold model load, warm single-image time, batch
   throughput and peak resident memory for CPU-only inference. Test batch sizes independently;
   GPU remains optional. Record model storage separately from runtime memory.
5. **Deployment and licensing:** Test a minimal Linux/Windows headless environment and Docker image
   without the GUI; document pyvips/libvips and PyTorch platform requirements. Before any
   redistribution, obtain clarity on Hydra code/checkpoint licensing scope and preserve all
   applicable notices.
6. **Data contract:** Prototype only after #44 defines how raw tag scores, per-label thresholds,
   checkpoint/model version, implication-derived labels and canonical-trait mapping provenance are
   persisted without merging official tags or safety evidence.

## Recommendation and next spike step

**Conditional go — benchmark Hydra 3.5 as the primary furry-semantic candidate.** The current
upstream recommendation, headless inference options, broad relevant tag vocabulary, and
per-label calibration make it a credible candidate. This is not a go for production adoption,
weight bundling, or implementing an ArtSniffer adapter. Licensing scope, semantic quality,
per-tag calibration on ArtSniffer-like examples, version/count discrepancy, and CPU resource use
remain unresolved.

**Next step:** extend the #62 evaluation protocol with a Hydra 3.5 arm (and, only if useful as a
historical ablation, JTP-3), then run a rights-cleared contrast set alongside the visual embedding
and source-tag baselines. Measure CPU time and memory on the Ryzen 7 5700G and record the exact
checkpoint digest, raw outputs, calibration settings and human judgements. After those results,
coordinate the generated-concept contract with #44 before deciding whether to implement a
provider-neutral semantic adapter.

## Source links

- [Issue #48 — Tail Tagger / Joint Tagger Project investigation](https://github.com/MuffinzCat/ArtSniffer/issues/48)
- [Issue #44 — canonical traits and semantic provenance](https://github.com/MuffinzCat/ArtSniffer/issues/44)
- [Issue #62 — visual embedding and furry semantic benchmark](https://github.com/MuffinzCat/ArtSniffer/issues/62)
- [Tail Tagger README](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/README.md)
- [Tail Tagger MIT licence](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/LICENSE)
- [Tail Tagger JTP-3.5 download instructions](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/classifiers/JTP-3.5/DOWNLOAD_INSTRUCTIONS.md)
- [Tail Tagger Hydra inference wrapper](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/classifier/inference/hydra_inference.py)
- [Tail Tagger vendored Hydra patch notes](https://github.com/renfald/tail-tagger/blob/e13c0917cf34ae8a725e077aec1bb266a9c7d7e2/tail_tagger/hydra/VENDOR_PATCHES.md)
- [Hydra 3.5 model card](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/README.md)
- [Hydra Windows installer](https://huggingface.co/RedRocket/Hydra/blob/main/install.bat)
- [Hydra model file-size metadata](https://huggingface.co/api/models/RedRocket/Hydra/tree/main/models?recursive=true&expand=true)
- [Hydra 3.5 public tag-list metadata](https://huggingface.co/RedRocket/Hydra/blob/cfa9b0a1ffcf2b8df8553be7673210fd60fba23b/data/jtp-3.5-hydra-tags.csv)
- [JTP-3 model card](https://huggingface.co/RedRocket/JTP-3)
- [Historical Joint Tagger Project card](https://huggingface.co/RedRocket/JointTaggerProject)
- [SigLIP2 base model card](https://huggingface.co/google/siglip2-so400m-patch16-naflex)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
