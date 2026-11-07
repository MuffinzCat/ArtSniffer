# ArtSniffer licensing and copyright audit

**Audit date:** 7 November 2026. **Repository:** MuffinzCat/ArtSniffer.
**Audited main/starting revision:** `227e5835778ca9f7eace11619946c63451ab438a`.
**Decision:** recommendation only; do not adopt a new licence in this change.

This is a technical/licensing audit, not legal advice or a certification of copyright ownership.
The licence texts, not this report's summaries, govern any eventual adoption. This report itself
does not grant permission to use ArtSniffer.

## Executive recommendation

**PolyForm Noncommercial License 1.0.0 is the closest established candidate**, because it grants
noncommercial use, modification and redistribution and expressly reserves the licensor's ability
to grant other licences. Its professionally drafted software-specific terms are a better fit than
an informal restriction added to MIT or Apache-2.0.

**It is not sufficiently clear that it implements the owner's exact, unqualified prohibition on
third-party monetisation.** Its organisational permission and separate distribution grant require
legal review, described below. Apache-2.0 with Commons Clause v1.0 more explicitly addresses paid
hosting and selling substantially the software, but deliberately permits other commercial uses,
including commercial internal use and qualifying value-added products. Neither candidate should
be represented as guaranteeing that nobody can make money from ArtSniffer.

Accordingly, leave `README.md`, `NOTICE.md` and `pyproject.toml` unchanged and do not add `LICENSE`.
The present all-rights-reserved position remains in force, subject to applicable law, existing
permissions and GitHub's terms. This means the desired general noncommercial permissions are
**not yet granted**. Review the questions in this report before a separate adoption change.
If the owner accepts PolyForm's standard boundaries after legal review, adopt the official text
unchanged, rather than drafting additional restrictions.

## Owner's stated goals

The owner wants free downloading and use, self-hosting, source inspection, modification, forks,
redistribution of originals and modified versions, and contributions for personal, hobby and
genuinely noncommercial purposes.

Third parties should not sell ArtSniffer, sell substantially derived forks, charge for hosted
access/SaaS, repackage it as a paid product, or otherwise commercially monetise it in a manner
prohibited by the selected standard licence. The copyright holder should remain able to grant
separate commercial licences.

The broad "genuinely non-commercial" and "make money" statements are treated conservatively:
ordinary business use is not assumed acceptable merely because the business does not resell the
software. Paid support, consulting, sponsorship, advertising, donations and cost recovery also
need their boundaries understood; a licence should not silently add permissions the owner has
not considered. There is no requirement to invent a bespoke licence.

## Scope, method and limitations

The starting tree has **125 tracked files**. The audit inventoried all tracked paths, searched
tracked text for copyright, licence, SPDX, attribution, copied/adapted material and source URLs,
examined project metadata and notices, classified imports in every Python source/test file,
reviewed file-introduction and licensing history, and checked publication/contributor information
through GitHub's API.

The checkout was initially shallow. `git fetch --unshallow origin` and a tag fetch recovered
**109 commits reachable across fetched refs**, including **53 commits on main** at the audited
revision. Counts include feature commits and their squash/merge counterparts, not 109 independent
contributions. Current source, tests, configuration and documentation were included in the
licensing/provenance scan; deleted/moved paths and fetched branch history were considered as
historical evidence, not automatically treated as current shipped files.

All **62 third-party packages in `uv.lock`** had their exact-version PyPI JSON licence declarations
retrieved successfully. The build requirement was checked separately. These declarations are
inventory evidence, not a substitute for each distributed artefact's actual licence files.
No dependencies or model weights were installed/downloaded for execution.

Direct retrieval from several official websites failed because of DNS resolution in this
environment. The complete PolyForm text was instead read from both the project's official
licence-source repository and its website-source repository. Commons Clause's complete condition
and FAQ were read from the site's official source repository. Official-site search results
corroborated these sources. Apache-2.0, MIT, CC0 and MPL text was also examined through the sources
listed below. Source links distinguish directly retrieved text from search-only model evidence.

This is not an exhaustive global code-similarity search, examination of private contracts, or a
binary/container/software-bill-of-materials clearance. Commit identity, an absent notice and
permissive-looking metadata cannot prove originality, ownership or complete redistribution rights.
Deleted remote refs, privately published packages and off-platform permissions are outside the
available evidence.

## Current repository licensing state

| Surface | Observed state at the audited revision |
|---|---|
| `LICENSE` / `LICENCE` / `COPYING` | No such tracked licence file identified in the current tree or examined history. |
| `README.md`, Copyright and Usage | `Copyright © 2026 Muffin. All rights reserved.` Explicitly source-available, not open source; no general use/modification/redistribution grant. |
| `NOTICE.md` | Same copyright holder; express reservation of rights, statutory/platform exceptions and possible separate permission; third-party rights expressly unaffected. |
| `pyproject.toml` | Project `artsniffer`, version `0.1.0`, author `Muffin`; no licence expression, licence-files declaration or licence classifier. Runtime dependencies are empty. |
| SPDX / per-file copyright | No SPDX licence identifiers or additional source/test copyright notices identified. Absence is not a grant. |
| Other tracked material | Python implementation/tests, Markdown agent/instruction/skill files, workflow YAML, `.gitignore`, `.python-version`, generated `uv.lock`. No vendored directory or embedded model/artwork artefacts identified. |
| GitHub repository API | `license: null`, `fork: false`; repository created 5 November 2026. This is metadata, not independent legal clearance. |

The existing `NOTICE.md` is the owner's usage reservation, **not** an Apache-2.0 upstream NOTICE
file. If a licence is later adopted, its contradictory no-permission language must be replaced;
simply adding a `LICENSE` beside it would leave an inconsistent permission statement.

## Copyright and contributor audit

### Observable authorship

Main's Git author summary is:

| Recorded identity | Main commits | Interpretation / limit |
|---|---:|---|
| Muffin, GitHub noreply address for account ID 33560694 | 51 | Account associated with MuffinzCat; appears to be the owner. |
| Muffin, non-noreply address | 1 | Initial commit; GitHub commit API associates it with MuffinzCat. No personal address is reproduced here. |
| Copilot, bot-associated identity | 1 | SQLite cache change, merged as [#59](https://github.com/MuffinzCat/ArtSniffer/pull/59). Includes owner and bot co-author trailers. |

Across fetched refs, additional `MuffinzCat` author-name variants use the same account ID, and
Copilot/coding-agent identities appear on feature commits. Co-author trailers also identify
Copilot and Copilot Autofix. GitHub's main contributor API lists MuffinzCat (52 commits) and
Copilot (1); examined PR submitters are MuffinzCat and Copilot. No distinct non-owner human
copyright claimant was identified in this evidence.

This is evidence of an owner-led, AI-assisted project, **not** a finding that every contribution's
copyright has been assigned to MuffinzCat. Authors, committers, PR submitters, co-author credits and
copyright owners are different concepts. No tracked CLA, copyright assignment, contributor
ownership register or employer/contractor permission was found.

GitHub's current Terms of Service section J.2 says GitHub does not claim ownership of Input or
Output, but warns that Output may contain third-party copyrighted/licensed material. A bot credit
does not itself make GitHub a co-owner; conversely, AI assistance does not prove absence of
third-party material or establish protectable human authorship in every jurisdiction.
The owner should confirm human authorship/control where relevant and review any code-reference
matches, copied examples or external snippets used during development.

Section D.6's inbound=outbound provision is **not** a copyright assignment. In particular, a
contribution made while the project reserved all rights should not be assumed to grant a later
right to relicense it. Future contributions under PolyForm alone would also not necessarily let
the owner commercially relicense contributor-owned changes. Preserve a clear inbound policy and,
if needed, obtain a professionally reviewed contributor agreement granting that authority.
Do not claim that this repository already has one.

### Imports and third-party code

The initial commit
[`7a726bb`](https://github.com/MuffinzCat/ArtSniffer/commit/7a726bb0c24dcccdacdb4edb01f6d578539db855)
contains only README and `.gitignore`. The Python foundation, metadata and rights notice appear
in
[`9c4bc2b`](https://github.com/MuffinzCat/ArtSniffer/commit/9c4bc2baba18244bbef409f8e84d9f1be68c8edc).
Later history introduces domain implementations, tests, analysis/cache/benchmark functionality and
tooling incrementally, with several package reorganisations. No wholesale third-party application
import or asserted upstream copyright in those files was identified.

**One clearly inherited template exists:** `.gitignore` substantially matches
[`github/gitignore`'s Python template](https://github.com/github/gitignore/blob/7705c2cd7cfe56c5b9b5c1000844a17f573cf5f1/Python.gitignore).
The examined current upstream differs by a Conda section and ArtSniffer's benchmark-data rule.
ArtSniffer's initial `.gitignore` and the upstream
[`9630d0` template](https://github.com/github/gitignore/blob/9630d0771522b209b81e0faad310b676531378df/Python.gitignore)
have the identical SHA-256
`114f3cdc2057d610cbc810f69cbc4f195acec0cd15dd54e9b154cf5f6657fc24`.
That upstream revision's licence is also CC0.
The upstream repository's
[`LICENSE`](https://github.com/github/gitignore/blob/7705c2cd7cfe56c5b9b5c1000844a17f573cf5f1/LICENSE)
is **CC0-1.0, not MIT**. CC0 imposes no attribution condition and is not a relicensing blocker on
this evidence. Its original dedication/fallback permissions are not revoked by a project licence,
and it does not convey third-party patent or trademark rights.

No vendored Python/C/C++ source, submodules, symlinks to external source, third-party source archive,
image assets, checkpoint files or generated inference code was identified in the tracked tree.
`uv.lock` is generated dependency-resolution metadata, not a copy of those packages' implementation.
No generator-specific licensing requirement was identified. Workflow `uses:` entries reference
external actions; they do not embed those actions' implementations in ArtSniffer. No missing
required third-party notice was established for the currently tracked application source.

The DINOv2 adapter uses normal external APIs from Pillow, Torch and Transformers. Model-loading
code can resemble public usage examples; no attributed copied block was found, but its precise
development provenance cannot be certified from Git alone. Review any known snippet origin.

**Ownership conclusion:** no affirmative third-party application-code blocker was found, but legal
title/authority has not been established beyond repository evidence. Confirm the identity behind
`Muffin`, any employer/client rights, contributor permissions and external snippet provenance
before representing an adoption as ownership-cleared. Neither an owner credit nor a squash merge
is sufficient to transfer another person's rights.

## Earlier versions and publication implications

The first README makes no licence grant. The foundation introduces the all-rights-reserved notice,
which is unchanged through the audited revision; no prior permissive/open-source ArtSniffer licence
was identified in examined reachable history.

At the audit date GitHub returned **zero tags and zero releases**. A PyPI lookup for
`artsniffer/0.1.0` returned HTTP 404. The tracked workflows have no package-release publishing step.
Version `0.1.0` in metadata alone does not prove a released package. Nevertheless, public Git
commits, forks and GitHub source downloads are already available; no named release is required
for licences or platform permissions to have consequences. These checks cannot rule out private
downloads, other registries, deleted releases or individually granted permissions.

**A new licence cannot simply revoke existing grants.** Apache-2.0's copyright grant is expressly
perpetual and irrevocable, subject to its conditions; CC0 expressly waives/falls back irrevocably.
The Commons Clause official FAQ specifically says a change affects future releases and does not
revoke licences on previous versions. A previously permissively licensed copy, if one exists beyond
the examined evidence, can continue to be used, forked and redistributed under that grant, including
commercially where permitted. Existing private commercial licences also need their own terms
reviewed. A later change does not automatically relicense historical downloads or terminate them.

For ArtSniffer's observed history, older copies continue with their attached all-rights-reserved
state, lawful exceptions, hosting-platform rights and any separately granted permissions.
Adoption could make a newly offered copy of owner-controlled existing code available under new
terms, but should state the applicable revision and date, not assert retrospective revocation.
Even a future PolyForm grant must not be treated as arbitrarily withdrawable from compliant
recipients: its own Violations/cure conditions govern termination.

GitHub's Terms of Service D.5 already grants public-repository viewing/forking rights through the
service. D.4 and D.8 contain additional hosting/lawful-access provisions. A software licence cannot
negate separately granted platform rights or statutory exceptions. Legal review should consider
these terms if "no third-party commercial benefit whatsoever" is intended literally.

## Candidate comparison

The Commons Clause candidate here is **Apache License 2.0 subject to Commons Clause License
Condition v1.0**, not unmodified Apache-2.0 offered as an alternative. Apache is an appropriate
permissive base because it has explicit patent, notice and contribution provisions. Choosing MIT
instead would simplify notices but would provide no express patent grant; it would not repair
Commons Clause's commercial-use mismatch.

In this table, "permitted" always means subject to the candidate's conditions. PolyForm conclusions
about monetisation are deliberately qualified; see the textual ambiguities immediately below.

| Question | PolyForm Noncommercial 1.0.0 | Apache-2.0 + Commons Clause v1.0 |
|---|---|---|
| Free download/source inspection/personal use | Permitted for permitted purposes; listed personal activities must have no anticipated commercial application. | Permitted; ordinary commercial purposes also allowed outside defined Sell. |
| Personal/hobby self-hosting | Permitted on the same purpose basis. | Permitted. |
| Modification and forks | Permitted for permitted purposes under Changes and New Works License. | Permitted, including commercial modification outside defined Sell. |
| Redistribution of original | Express additional distribution grant, with notices; its unqualified wording needs review before claiming all paid distribution is forbidden. | Permitted except defined Sell; base and condition notices must accompany it. |
| Redistribution of modified versions | Expressly covered when changes/new works are permitted; preserve terms/notices. No unrestricted commercial relicensing of ArtSniffer's underlying code. | Permitted except defined Sell, with Apache modification/notice requirements and Commons Clause notice. |
| Contributions | Noncommercial changes can be submitted; not a copyright assignment or automatic commercial relicensing authority. | Submissions allowed; Apache section 5 supplies default inbound terms, not ownership transfer. |
| Ordinary commercial internal use prohibited? | Generally outside permitted purposes; organisational carve-out and genuinely noncommercial activities must be considered. | **No.** Internal business use is generally allowed; Sell requires provision to third parties. |
| Can a company use it internally without reselling? | Not automatically. The use's purpose matters; being free to acquire is not enough. A genuinely noncommercial use may qualify. | **Yes**, normally, including for commercial business operations. |
| Selling the original software | Commercial purpose generally outside the use grant, but separate distribution wording prevents a categorical assurance. | **Prohibited** when the product/service's value derives entirely or substantially from ArtSniffer. |
| Selling modified forks | Commercial development/use generally outside the grants; distribution and organisational issues still need review. | **Prohibited** when value still derives entirely/substantially from its functionality; real value-added products may be sold. |
| Paid hosting / SaaS | Commercial operation generally outside the use grant; organisational permission needs review. | Hosting fees expressly included in Sell for a substantially ArtSniffer-derived service. Not a ban on all larger SaaS using a component. |
| Paid consulting / support | Commercial activity involving licensed use or changes generally outside the purpose grant; advice alone may not exercise copyright rights. | Fees for related consulting/support expressly included, but only with the substantial-value condition. FAQ says consulting may be allowed. |
| Attribution/notices | Give recipients the terms or official URL and any supplied plain-text `Required Notice:` lines. Not a mandatory UI credit or copyleft source-publication rule. | Include Apache text and Commons Clause condition; retain relevant source notices, mark changed files, and preserve relevant upstream NOTICE attribution where supplied. |
| Patent provisions | Express grant of licensable claims infringed by using the software; written patent-infringement claims trigger Patent Defense termination. | Apache contributor patent grant limited to covered contribution claims; patent-litigation termination. Condition limits granted rights; it does not create extra patents. |
| OSI open source? | **No: source-available.** Commercial-purpose restrictions conflict with the Open Source Definition. | **No: source-available.** Adding Commons Clause removes the combined offering's open-source status. |
| Owner can grant separate commercial licences? | **Yes**, for rights it controls; No Other Rights expressly preserves licensing to others. Contributor/dependency rights remain separate. | **Yes**, for rights it controls; a nonexclusive public licence does not transfer ownership. Same contributor/dependency qualification. |
| Core mismatch | Organisational carve-out, undefined noncommercial boundaries and unqualified distribution wording versus an absolute no-monetisation demand. | Intentionally allows commercial internal use and value-added monetisation; not a genuinely-noncommercial-only licence. |

### PolyForm: exact text and uncertainties

Its Copyright License allows otherwise infringing acts "for any permitted purpose", while
Noncommercial Purposes says "Any noncommercial purpose is a permitted purpose".
Personal Uses enumerates research/experimentation, personal study, entertainment, hobbies, amateur
pursuits and religious observance "without any anticipated commercial application".

Two clauses are material to the strict owner intent:

> Use by any charitable organization, educational institution, public research organization,
> public safety or health organization, environmental protection organization, or government
> institution is use for a permitted purpose regardless of the source of funding or obligations
> resulting from the funding.

This is broader than a simple test that every activity must earn no money. Do not say that all
paid, sponsored or revenue-associated activities by these organisations are necessarily prohibited.
The clause's application to particular fee-charging institutions/services needs legal review.

> The licensor grants you an additional copyright license to distribute copies of the software.

The separate Distribution License does not repeat the permitted-purpose limitation. It expressly
covers permitted modifications, but the interaction with commercial distribution of originals
is not resolved by merely reading the licence's name or the project's general description.
This audit does **not** conclude that selling copies is affirmatively allowed; it concludes that
a blanket assurance that all selling is prohibited is unsafe without authoritative interpretation.

The licence also leaves donations, advertising, sponsorship, mixed-purpose use, cost recovery and
consulting boundaries to purpose/legal analysis rather than defining an exhaustive list of sales.
Its patent grant, first-notified-violation 32-day cure provision, fair-use preservation and
as-is/liability terms should be retained exactly.

PolyForm is not a share-alike/source-disclosure licence: recipients must retain the underlying
terms/notices, but the text does not require publication of every modification. It does not permit
recipients to sublicense/transfer their licences; that is different from its expressly permitted
redistribution. It cannot prevent commercial use of independently owned dependencies on their
own, or capture an independently written implementation merely because it has similar ideas.

### Commons Clause: exact boundary

The operative definition restricts providing to third parties, "for a fee or other consideration
(including without limitation fees for hosting or consulting/support services related to the
Software), a product or service whose value derives, entirely or substantially, from the
functionality of the Software".

Thus selling a rebranded ArtSniffer, substantially derived paid fork or substantially ArtSniffer
hosted service is within its intended restriction. But the official FAQ expressly permits
embedding it in a larger sold product, qualifying SaaS and some consulting. "Substantially" is a
value/functionality test, not a line-count threshold or a ban on every commercial derivative.
The FAQ is explanatory and cannot override the condition's actual text.

This would be a defensible alternative **only if the owner changes the goal** to preventing
defined Sell while accepting commercial internal use and qualifying value-added monetisation.
Do not adopt it while claiming it bans all commercial use. Nor should unmodified Apache or MIT be
offered alongside it as a public alternative, which would allow recipients to bypass the condition.

### Other established options

The official PolyForm comparison was reviewed. Strict removes modification and distribution;
Internal Use permits internal business purposes and lacks the required distribution permission;
Small Business permits business use; Shield/Perimeter restrict competition rather than commercial
use generally. None materially improves this fit without losing a required freedom or retaining
commercial uses. Strict's actual exclusion of distributing or making changes was also checked.
No additional candidate is recommended.

Unmodified MIT/Apache and GPL/AGPL are not noncommercial licences. Network copyleft is not a ban
on paid hosting. Creative Commons noncommercial terms are not selected as a software licence;
their use for artwork or other content is a separate question. No custom hybrid or informal
"no commercial use" addendum is proposed.

## Dependency and redistribution compatibility

**ArtSniffer's own-source licence is separate from every dependency licence.** Imports of independent
permissively licensed packages do not generally require the importer itself to adopt their
licence. Redistributing those packages, their modified files or a bundled executable/container
does require compliance with their terms. A noncommercial project licence cannot remove their
commercial permissions or replace their notices.

The default application has no declared runtime dependencies. Optional `benchmark-dinov2` adds
Pillow, Torch and Transformers and their transitive dependencies. The lock also includes development
tools. Build requirement `uv_build>=0.13.7,<0.14.0` is separate and not fixed by this lock;
the checked lower-bound release declares `MIT OR Apache-2.0`.

The inventory below records **publisher metadata at the exact locked version**, not a conclusion
that each wheel contains only that licence. "Classifier only" and "unspecified" require checking
the artefact's actual terms. Each version is linked to its retrieved PyPI metadata.

| Package/version | Declared licence or evidence |
|---|---|
| [annotated-doc 0.0.5](https://pypi.org/pypi/annotated-doc/0.0.5/json) | MIT |
| [anyio 4.16.0](https://pypi.org/pypi/anyio/4.16.0/json) | MIT |
| [click 8.5.1](https://pypi.org/pypi/click/8.5.1/json) | BSD-3-Clause |
| [colorama 0.4.6](https://pypi.org/pypi/colorama/0.4.6/json) | BSD classifier only |
| [cuda-bindings 13.5.0](https://pypi.org/pypi/cuda-bindings/13.5.0/json) | Apache-2.0 |
| [cuda-pathfinder 1.8.6](https://pypi.org/pypi/cuda-pathfinder/1.8.6/json) | Apache-2.0 |
| [cuda-toolkit 13.2.2](https://pypi.org/pypi/cuda-toolkit/13.2.2/json) | Unspecified |
| [filelock 4.2.9](https://pypi.org/pypi/filelock/4.2.9/json) | MIT |
| [fsspec 2026.9.0](https://pypi.org/pypi/fsspec/2026.9.0/json) | BSD-3-Clause |
| [h11 0.16.0](https://pypi.org/pypi/h11/0.16.0/json) | MIT |
| [hf-xet 1.8.0](https://pypi.org/pypi/hf-xet/1.8.0/json) | Apache-2.0 |
| [httpcore2 2.16.0](https://pypi.org/pypi/httpcore2/2.16.0/json) | BSD-3-Clause |
| [httpx2 2.16.0](https://pypi.org/pypi/httpx2/2.16.0/json) | BSD-3-Clause |
| [httpx2-jsfetch 1.0](https://pypi.org/pypi/httpx2-jsfetch/1.0/json) | BSD-3-Clause |
| [huggingface-hub 2.4.0](https://pypi.org/pypi/huggingface-hub/2.4.0/json) | Apache-2.0 |
| [idna 3.20](https://pypi.org/pypi/idna/3.20/json) | BSD-3-Clause |
| [iniconfig 2.3.1](https://pypi.org/pypi/iniconfig/2.3.1/json) | MIT |
| [jinja2 3.1.6](https://pypi.org/pypi/jinja2/3.1.6/json) | BSD classifier only |
| [markdown-it-py 4.2.0](https://pypi.org/pypi/markdown-it-py/4.2.0/json) | MIT classifier only |
| [markupsafe 3.0.4](https://pypi.org/pypi/markupsafe/3.0.4/json) | BSD-3-Clause |
| [mdurl 0.1.2](https://pypi.org/pypi/mdurl/0.1.2/json) | MIT classifier only |
| [mpmath 1.3.0](https://pypi.org/pypi/mpmath/1.3.0/json) | BSD, unspecified variant |
| [networkx 3.7](https://pypi.org/pypi/networkx/3.7/json) | BSD-3-Clause |
| [nodeenv 1.12.0](https://pypi.org/pypi/nodeenv/1.12.0/json) | BSD, unspecified variant; LICENSE/AUTHORS listed |
| [numpy 2.5.4](https://pypi.org/pypi/numpy/2.5.4/json) | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| [nvidia-cublas 13.4.1.3](https://pypi.org/pypi/nvidia-cublas/13.4.1.3/json) | Unspecified |
| [nvidia-cuda-cccl 13.3.5.0.6](https://pypi.org/pypi/nvidia-cuda-cccl/13.3.5.0.6/json) | LicenseRef-NVIDIA-Proprietary |
| [nvidia-cuda-cupti 13.2.86](https://pypi.org/pypi/nvidia-cuda-cupti/13.2.86/json) | Unspecified |
| [nvidia-cuda-nvrtc 13.2.86](https://pypi.org/pypi/nvidia-cuda-nvrtc/13.2.86/json) | Unspecified |
| [nvidia-cuda-runtime 13.2.86](https://pypi.org/pypi/nvidia-cuda-runtime/13.2.86/json) | Unspecified |
| [nvidia-cudnn-cu13 9.26.0.51](https://pypi.org/pypi/nvidia-cudnn-cu13/9.26.0.51/json) | Unspecified |
| [nvidia-cufft 12.2.0.57](https://pypi.org/pypi/nvidia-cufft/12.2.0.57/json) | Unspecified |
| [nvidia-cufile 1.17.1.22](https://pypi.org/pypi/nvidia-cufile/1.17.1.22/json) | Unspecified |
| [nvidia-cusolver 12.2.0.11](https://pypi.org/pypi/nvidia-cusolver/12.2.0.11/json) | Unspecified |
| [nvidia-cusparse 12.7.10.12](https://pypi.org/pypi/nvidia-cusparse/12.7.10.12/json) | Unspecified |
| [nvidia-cusparselt-cu13 0.8.1](https://pypi.org/pypi/nvidia-cusparselt-cu13/0.8.1/json) | NVIDIA Proprietary Software |
| [nvidia-nccl-cu13 2.30.7](https://pypi.org/pypi/nvidia-nccl-cu13/2.30.7/json) | Unspecified |
| [nvidia-nvjitlink 13.5.37](https://pypi.org/pypi/nvidia-nvjitlink/13.5.37/json) | LicenseRef-NVIDIA-Proprietary |
| [nvidia-nvshmem-cu13 3.7.2](https://pypi.org/pypi/nvidia-nvshmem-cu13/3.7.2/json) | Unspecified |
| [nvidia-nvtx 13.2.86](https://pypi.org/pypi/nvidia-nvtx/13.2.86/json) | Unspecified |
| [packaging 26.3](https://pypi.org/pypi/packaging/26.3/json) | Apache-2.0 OR BSD-2-Clause |
| [pillow 13.0.0](https://pypi.org/pypi/pillow/13.0.0/json) | MIT-CMU |
| [pluggy 1.7.0](https://pypi.org/pypi/pluggy/1.7.0/json) | MIT |
| [pygments 2.21.0](https://pypi.org/pypi/pygments/2.21.0/json) | BSD-2-Clause |
| [pyright 1.1.414](https://pypi.org/pypi/pyright/1.1.414/json) | MIT |
| [pytest 9.2.0](https://pypi.org/pypi/pytest/9.2.0/json) | MIT |
| [pyyaml 6.0.3](https://pypi.org/pypi/pyyaml/6.0.3/json) | MIT |
| [regex 2026.11.7](https://pypi.org/pypi/regex/2026.11.7/json) | Apache-2.0 AND CNRI-Python |
| [rich 15.0.0](https://pypi.org/pypi/rich/15.0.0/json) | MIT |
| [ruff 0.17.3](https://pypi.org/pypi/ruff/0.17.3/json) | MIT |
| [safetensors 0.8.0](https://pypi.org/pypi/safetensors/0.8.0/json) | Apache classifier only |
| [setuptools 84.2.1](https://pypi.org/pypi/setuptools/84.2.1/json) | MIT |
| [shellingham 1.5.4](https://pypi.org/pypi/shellingham/1.5.4/json) | ISC License |
| [sympy 1.14.0](https://pypi.org/pypi/sympy/1.14.0/json) | BSD, unspecified variant; LICENSE/AUTHORS listed |
| [tokenizers 0.23.3](https://pypi.org/pypi/tokenizers/0.23.3/json) | Apache classifier only |
| [torch 2.15.0](https://pypi.org/pypi/torch/2.15.0/json) | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND ISC AND MIT AND Zlib |
| [tqdm 4.70.1](https://pypi.org/pypi/tqdm/4.70.1/json) | MPL-2.0 AND MIT |
| [transformers 5.22.2](https://pypi.org/pypi/transformers/5.22.2/json) | Apache 2.0 License |
| [triton 3.9.0](https://pypi.org/pypi/triton/3.9.0/json) | MIT |
| [truststore 0.10.5](https://pypi.org/pypi/truststore/0.10.5/json) | MIT |
| [typer 0.28.0](https://pypi.org/pypi/typer/0.28.0/json) | MIT |
| [typing-extensions 4.16.0](https://pypi.org/pypi/typing-extensions/4.16.0/json) | PSF-2.0 |

Important consequences:

- **tqdm is not simply MIT.** Its upstream `LICENCE` identifies MPL-covered contributions and
  MIT exceptions. MPL 2.0 sections 3.1-3.4 require covered source, including modifications, to remain
  under MPL, preserve notices and make that source available when executables are distributed.
  Section 3.3 permits separately licensed larger works. Keep tqdm distinct; do not put a
  noncommercial restriction on its covered source. Its presence is not an automatic prohibition
  on licensing independent ArtSniffer code under PolyForm.
- **NVIDIA clearance is unresolved for bundled distribution.** Thirteen packages lack a licence
  declaration in the retrieved metadata, and others expressly identify proprietary terms.
  CUDA's official EULA provides conditional redistribution rights for specified components, not
  a blanket permission to relicense the toolkit. Inspect the exact wheel/EULA, component list,
  required notices and any separate cuDNN/cuSPARSELt/NCCL/NVSHMEM terms before distributing a bundle.
  Missing metadata does not mean public domain or prove a prohibition.
- **Torch and NumPy are multi-licence artefacts.** Their metadata lists numerous licence files.
  Preserve included third-party notices and check the actual platform wheel's bundled libraries.
  Do not reduce either to its headline licence or claim full wheel clearance from metadata.
  Pillow wheels can also carry external image-library notices; retain those as applicable.
- **Development/build/runtime are separate.** If tools, Node/Python runtimes or SQLite are bundled,
  their distributions and embedded components need their own review. Python's PSF/historical
  notices and SQLite's dedication are not replaced by ArtSniffer's licence. No such bundle is
  tracked here.
- **Future copyleft imports require a fresh check.** A whole-work GPL/AGPL obligation can conflict
  with adding noncommercial restrictions to a combined derivative. No such whole-work licence was
  identified in the retrieved package declarations, but binary contents have not been certified.

For an own-source-only release, no dependency-driven requirement to license all ArtSniffer source
permissively or under copyleft was established. For an optional-dependency bundle, no complete
redistribution clearance is claimed. Preserve every dependency's original notices/licence files;
the current generic `NOTICE.md` is not a substitute for an artefact-specific notice inventory.

## Models, training data and artwork are separate rights layers

| Layer | Evidence / implication |
|---|---|
| ArtSniffer adapter/domain source | Subject to the project's existing reservation or a future owner-authorised licence. |
| Dependency implementation | Separate licences above; no project relicense changes them. |
| DINOv2 code/checkpoints | Current official upstream README says DINOv2 code and model weights are Apache-2.0; the current `facebook/dinov2-small` model-page search result also labels Apache-2.0. No weights are tracked here. |
| Specific checkpoint/version | The adapter calls `from_pretrained("facebook/dinov2-small")` without a pinned revision. Historical model-card evidence at revision `169e7c34622d7a7c466d7d9aabcec09c35c9a91e` shows `cc-by-nc-4.0`; current labels must not be applied blindly to every cached/historical download. |
| Other models | The DINOv2 repository now also documents specialised models with separate noncommercial terms. Do not assume every model in that repository has the DINOv2 backbone's licence. |
| Training datasets | Neither a model licence nor ArtSniffer's licence establishes rights to redistribute underlying training images, retrain on arbitrary images, or ignore artist/privacy/database rights. |
| User/reference/discovered artwork | Remains the creator/rightsholder's content. Access through OneDrive, an API or a user collection is not a general licence to redistribute or commercially exploit it. |

The Hugging Face model-page/historical-card evidence above was obtained through search; direct
model-card download failed DNS. It is a reason to verify the exact artefact's provenance/licence,
**not** a legal conclusion about which grant controls every converted weight file. Commercial
licensing of ArtSniffer later cannot authorise a restricted checkpoint or third-party content.

Current README plans include source metadata, generated semantic signals, OneDrive collections,
Discord/Telegram delivery and model-neutral analysis. Those integrations have independent API,
service, moderation, asset and licensing requirements. The implementation already includes a
SQLite analysis cache and DINOv2 adapter/benchmark tooling, but no complete delivery/discovery
service is claimed. Local benchmark images/results are ignored and no artwork is tracked.
Ignoring a file is not a licence to use or redistribute it.

For historical planning context,
[#62](https://github.com/MuffinzCat/ArtSniffer/issues/62) considers CLIP/OpenCLIP, SigLIP/SigLIP 2,
DINOv2/DINOv3, DreamSim and furry taggers. These families are **not** automatically covered by one
software or model licence. A fetched, unmerged branch's
[`61046f4` Hydra spike](https://github.com/MuffinzCat/ArtSniffer/blob/61046f41ed23eb0ade9b1a279b6ee37cf4c90d56/docs/research/issue-48-hydra-3-5-spike.md)
also flags separate Tail Tagger code, Hydra checkpoint and training-artwork questions.
It is not part of the audited main tree or proof of any upstream grant; independently review
the exact code/checkpoint before adoption. These plans do not block licensing independent project
source by themselves, but remain gates for model use, bundling and future commercial offerings.

## Adoption decision and manual-review gates

**Phase 5 is not authorised by the evidence obtained:** no standard candidate has been established
to match the strict intent without material qualification, and the repository evidence alone does
not settle all copyright authority. There is no licence adoption commit in this proposal.
Dependency-bundle uncertainty is a separate release/integration concern, not automatically a
copyright blocker for the independent project source.

The owner/legal reviewer should resolve:

1. Whether the exact PolyForm organisational and distribution grants satisfy the intended sales,
   paid-hosting and "genuinely noncommercial" boundaries; seek authoritative interpretation rather
   than silently rewriting those clauses.
2. Whether advertising, sponsorship, donation-funded hosting, cost recovery, fee-charging
   institutions and paid support are acceptable; distinguish uses requiring a copyright licence
   from independent advice, legal exceptions and platform-granted rights.
3. The copyright holder's identity/authority, any employer/client rights, contribution permissions,
   code-reference/snippet provenance and any earlier private/public licence grants not in Git.
4. An inbound contribution arrangement sufficient for later commercial licensing of contributor
   changes; a DCO or GitHub account identity alone is not a copyright assignment.
5. Exact checkpoint licences/revisions and artefact-level dependency/EULA/notices for anything
   actually bundled. Keep this separate from the own-source licensing decision.

If these are resolved in favour of PolyForm's **unmodified** standard terms, a later, separate PR
can add the official `LICENSE`, supply a truthful `Required Notice:` copyright line as prescribed,
replace the contradictory reservation in README/NOTICE with an accurate source-available licensing
summary, and use `PolyForm-Noncommercial-1.0.0` in supported package licence metadata. Ensure source
and wheel distributions actually include the licence/notices; do not merely update the README.
Preserve independent third-party terms and explain the adoption revision/date and earlier grants.

That eventual offering would allow free genuinely noncommercial personal/hobby use, self-hosting,
inspection, noncommercial changes, forks and redistribution/contributions under the standard
conditions. Commercial operation/development outside permitted purposes would require separate
permission; sales/fee scenarios must follow the reviewed interpretation, not an invented blanket
rule. It would be **source-available, not OSI open source**, with commercial use intentionally
restricted. The owner could license rights it controls commercially in parallel.

If the standard boundaries remain unacceptable or uncertain, retain the current reservation
pending a new owner decision. Do not manufacture a PolyForm variant, add an informal no-commercial
sentence, remove independent notices or claim the owner's goals have already been implemented.

## Official and authoritative sources

All sources were consulted for this audit on 7 November 2026. Exact-version PyPI links are in the
inventory; they evidence metadata rather than replacing licence texts.

| Source | Link / retrieval context |
|---|---|
| PolyForm Noncommercial 1.0.0 official page | <https://polyformproject.org/licenses/noncommercial/1.0.0> |
| Official downloadable text | <https://polyformproject.org/licenses/noncommercial/1.0.0.txt> |
| Official licence-source text, pinned revision | <https://github.com/polyformproject/polyform-licenses/blob/9c032bcb6b44a68f90efddd1060cf71d4e6fd7ce/PolyForm-Noncommercial-1.0.0.md> |
| Official deployed website-source text, pinned revision | <https://github.com/polyformproject/polyformproject.org/blob/caa273a0f67aba05e8cc06f7e869469918f53617/licenses/noncommercial/1.0.0.txt> |
| PolyForm drafting/status explanation | <https://polyformproject.org/about> and <https://github.com/polyformproject/polyformproject.org/blob/main/pages/about.md> |
| Official PolyForm suite comparison | <https://polyformproject.org/licenses> and <https://github.com/polyformproject/polyformproject.org/blob/main/pages/licenses.md> |
| Official PolyForm Strict text used for exclusion | <https://github.com/polyformproject/polyformproject.org/blob/main/licenses/strict/1.0.0.txt> |
| Commons Clause condition and official FAQ | <https://commonsclause.com/> |
| Commons Clause site's official source, pinned revision | <https://github.com/fossas/commons-clause/blob/a83b2c7466e31f6cb3b285b08319e8af357ea244/src/index.html> |
| Apache-2.0 official text | <https://www.apache.org/licenses/LICENSE-2.0> and <https://www.apache.org/licenses/LICENSE-2.0.txt>; complete terms retrieved via <https://github.com/apache/.github/blob/main/LICENSE> |
| MIT text/reference | <https://choosealicense.com/licenses/mit/> and <https://github.com/github/choosealicense.com/blob/gh-pages/_licenses/mit.txt> |
| CC0 legal text | <https://creativecommons.org/publicdomain/zero/1.0/legalcode>; full text read in github/gitignore LICENSE linked above |
| Open Source Definition, especially sections 1 and 6 | <https://opensource.org/osd> (official search evidence) |
| GitHub Terms of Service, D and J | <https://docs.github.com/en/site-policy/github-terms/github-terms-of-service> (directly retrieved; effective date shown: 27 April 2026) |
| Mozilla MPL 2.0 official text | <https://www.mozilla.org/en-US/MPL/2.0/>; relevant sections retrieved via <https://github.com/github/choosealicense.com/blob/gh-pages/_licenses/mpl-2.0.txt> |
| tqdm attribution/MPL/MIT text | <https://github.com/tqdm/tqdm/blob/master/LICENCE> |
| CUDA EULA and redistribution component lists | <https://docs.nvidia.com/cuda/eula/> (official search evidence; exact installed component terms still required) |
| DINOv2 upstream licence and model statement | <https://github.com/facebookresearch/dinov2/blob/main/LICENSE> and <https://github.com/facebookresearch/dinov2/blob/main/README.md> (directly retrieved) |
| Current converted checkpoint model page | <https://huggingface.co/facebook/dinov2-small> (search evidence) |
| Historical converted model-card licence declaration | <https://huggingface.co/facebook/dinov2-small/blame/169e7c34622d7a7c466d7d9aabcec09c35c9a91e/README.md> (search evidence) |
| Build requirement lower-bound metadata | <https://pypi.org/pypi/uv_build/0.13.7/json> |
| Python runtime notices | <https://github.com/python/cpython/blob/main/LICENSE> |
| SQLite dedication | <https://www.sqlite.org/copyright.html> (reference for a future bundled-runtime review; not clearance of an unexamined bundle) |

## Change scope and validation

This proposal adds only this report. It does not change application code, dependency constraints,
licence/notice text, package metadata, platform settings or historical releases. It is intended for
a **draft PR with `manual-review`, without auto-merge**, not immediate adoption.

Validation is documentation-scoped: check the diff for whitespace errors, reconcile the dependency
inventory with `uv.lock` and the retrieved metadata, inspect changed paths and confirm the draft/
manual-review/no-auto-merge state. Application tests, Ruff and Pyright are not evidence needed for
this report-only change and are not claimed to have run.
