# ArtSniffer licensing and copyright audit

**Audit date:** 7 November 2026. **Repository:** MuffinzCat/ArtSniffer.
**Audited main/starting revision:** `227e5835778ca9f7eace11619946c63451ab438a`.
**Decision:** recommendation only; do not adopt a new licence in this change.

This is a technical/licensing audit, not legal advice or a certification of copyright ownership.
The licence texts, not this report's summaries, govern any eventual adoption. This report itself
does not grant permission to use ArtSniffer.

## Executive recommendation

The clarified rule is **free of charge for everyone**: nobody, including the owner, may charge for
ArtSniffer itself or a version that remains fundamentally ArtSniffer. This is not a noncommercial-
use requirement. The owner affirmatively permits ordinary commercial and internal use, including
use by people or organisations that earn money through other activities.

**No established, professionally drafted software licence reviewed here clearly and accurately
guarantees this exact rule. Do not adopt PolyForm Noncommercial, Commons Clause, or another
near-match as if it did.** Apache-2.0 plus Commons Clause is the closest to restricting paid
provision of software and substantially ArtSniffer-derived services while allowing commercial
internal use. But its official FAQ deliberately permits selling value-added products and derivatives,
leaving a material boundary around heavily modified forks. It also leaves the copyright holder free
to offer separate licences. PolyForm Perimeter and Elastic License 2.0 restrict competition or
hosted access, not all charging for the software. Ordinary open-source copyleft licences preserve
the ability to charge.

No licence file or licensing metadata has been changed. Keep the current all-rights-reserved state,
subject to law, GitHub's terms and any existing permissions; do not imply that this report grants
the desired use rights. Obtain professional licensing advice before adopting any bespoke
free-of-charge/fork condition or owner covenant. This approach honours the instruction not to
invent a custom licence or misstate a near-match.

## Owner's stated goals

The clarified governing principle is:

> **Nobody may charge money for ArtSniffer itself or an ArtSniffer fork/derivative that remains
> fundamentally ArtSniffer. ArtSniffer and its forks should remain free of charge for everyone,
> including MuffinzCat.**

People and organisations should be able to download and use ArtSniffer, run it personally or
internally in a business, self-host it, inspect/modify/fork it, redistribute originals and
modified versions, contribute changes, build integrations and use it in research or otherwise
commercial activities. This includes an artist earning income from art, a business using the
software internally, and customers independently installing it on ordinary paid VPS/cloud
infrastructure.

The restriction is about **charging for ArtSniffer or the fundamentally ArtSniffer-derived
application**, not making money while using it. It is intended to prohibit a purchase/download/
licence fee, subscription or paywall for ArtSniffer, paid hosted access to ArtSniffer itself,
premium ArtSniffer, rebranding/minor changes to evade the rule, and fees for modifications or
features in a fork that still amounts to ArtSniffer. A different name, user interface, packaging,
deployment, or added features is not intended by itself to permit charging.

Conversely, generic infrastructure or hosting resources, paid hardware capable of running it,
unrelated software interoperating with it, commercial internal use, and products/services whose
value does not consist substantially of providing ArtSniffer should generally remain possible.
This statement is the owner's intent, not a licence test or legal conclusion.

The owner does not intend a special right to sell commercial licences or charge for the software
personally. This condition on the owner is a distinct difficulty: ordinary non-exclusive software
licences grant rights to recipients while the copyright holder retains ownership and separate
licensing authority. A licence's restriction on licensees does not, by itself, bind its own
licensor. A public promise that the owner also will never charge/issue an exception may need a
separately enforceable legal mechanism; standard texts reviewed here do not establish that result.

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
| Muffin, non-noreply address | 1 | Python foundation commit (`9c4bc2b`); GitHub commit API associates it with MuffinzCat. No personal address is reproduced here. |
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
right to impose a no-charge condition on it. If changed ownership or permissions are needed to
cover contributor-owned changes under a future free-of-charge policy, obtain professionally
reviewed contributor terms. Do not claim that this repository already has them.

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
negate separately granted platform rights or statutory exceptions. Legal review should distinguish
these platform permissions from a price charged specifically for ArtSniffer or its forks.

## Candidate comparison

The central distinction is between a use that is commercial and a charge for the software itself.
The owner's policy permits the former (including business-internal use) and prohibits the latter,
including for fundamentally ArtSniffer-derived forks. "Free of charge" is not synonymous with
"noncommercial", "source-available", or "open source".

| Candidate | Free download, modify and redistribute? | Commercial/internal use? | Sale/access restriction and modified forks | Fit |
|---|---|---|---|---|
| **PolyForm Noncommercial 1.0.0** | Yes for permitted purposes, with notices. | **Generally no** for ordinary commercial purposes. Personal activity must lack anticipated commercial application; listed organisations have a special carve-out regardless of funding. | Purpose-based, not a simple no-price rule. Separate distribution grant does not restate a noncommercial condition. No clear guarantee against selling every copy. | Too restrictive on business use and does not clearly impose the intended price condition. Do not recommend. |
| **Apache-2.0 + Commons Clause v1.0** | Yes, subject to base/condition notices and Apache obligations. | **Yes.** Commercial internal use is generally allowed; the Sell definition concerns provision to third parties for consideration. | Prohibits charging for a product/service whose value derives entirely or substantially from the software's functionality, expressly including qualifying hosting/support. The official FAQ also says value-added derivatives/products may be sold. Whether a heavily modified but still fundamentally ArtSniffer fork always crosses the "substantially" line is not guaranteed. | **Closest on paid commercial provision while allowing internal use**, but not a dependable no-charge condition for every ArtSniffer-derived fork. Does not bind licensor to no-charge policy. Source-available, not OSI open source. |
| **PolyForm Perimeter 1.0.1** | Copying, modification and redistribution are granted with notices, for permitted purposes. | Internal business use is generally permitted. | Forbids providing others any product that competes with the software, whether free or paid and regardless of interface/deployment. This can bar free competitive forks/services, while it is a competition restriction rather than a no-charge rule. No Other Rights permits the licensor to grant others rights. | Wrong axis: over-restricts free competing provision, and does not ensure the owner or every fork stays free. Source-available. |
| **Elastic License 2.0** | Grants use, copying, distribution and derivative works with notices. | **Yes**, including internal business use. | Prohibits substantial hosted/managed access, but does not generally prohibit selling copies or charging for a fork. Its patent grant explicitly contemplates sale subject to limitations. | Hosted-access restriction, not a free-of-charge licence. Source-available. |
| **Redis Source Available License v2 (RSALv2)** | Grants use/copy/distribution/derivatives subject to conditions. | Yes, including internal commercial use. | Restricts making functionality of original or modified version available to third parties as a service or through distribution; not a price-only rule. Patent grant expressly references sale, subject to limitations. It can block free third-party service/distribution and does not forbid all paid copies as such. | Too restrictive on free provision and does not encode the desired no-charge boundary. Source-available. |
| **Business Source License 1.1 (BSL)** | Grants copy/modify/derivatives/redistribution, generally for non-production use; the licensor defines an Additional Use Grant and Change Date/Change License. | Production/business use depends on the grant; noncompliant use requires purchase of a commercial licence or stopping use. | Not a durable no-fee guarantee: it expressly contemplates charging for commercial licences and changes to an open-source Change License (usually after up to four years). | Conflicts with free-for-everyone owner policy and long-term restriction. Source-available during its term. |
| **GPL/AGPL (including strong copyleft)** | Yes; modified covered code must be redistributed under the same freedoms/terms, subject to each licence. | **Yes.** Commercial internal and external uses are allowed. | Copyleft preserves downstream rights/source obligations, not a no-price rule. The GPL expressly permits charging any price for copies; paid SaaS is not generally prohibited by GPL, and AGPL's network source obligation is not a ban on charging. | Preserves forks' licence freedoms but explicitly fails the no-charge requirement. OSI open source. |
| **MIT / Apache-2.0 / MPL-2.0** | Yes. | Yes. | Permit commercial distribution/sale; MPL copyleft requires source for covered files on distribution but does not prohibit a fee. | Fail the price rule. OSI open source. |

No candidate evaluated is recommended as exactly satisfying the clarified owner intent. Standard
source-available terms that restrict competition or hosted access are not equivalent to a
no-charge rule, and open-source copyleft rules expressly preserve commercial sale.

### PolyForm Noncommercial: why not

The operative grant permits use, modification and distribution for "any permitted purpose";
Noncommercial Purposes says "Any noncommercial purpose is a permitted purpose". Personal use is
described as occurring "without any anticipated commercial application". Although the text grants
an additional Distribution License, the use/change grants remain purpose-limited.

The licence also allows use by specified charities, educational/public research/safety/health/
environmental-protection organisations and government institutions "regardless of the source of
funding or obligations resulting from the funding". This is an organisation-based exception, not
the owner's general permission for commercial businesses to use the software internally.

PolyForm Noncommercial therefore confuses the intended line: it can prohibit a business using
ArtSniffer internally without charging for ArtSniffer, while treating certain funded organisations
differently. Its distribution sentence also does not unambiguously say "no person may charge any
price for a copy or derivative". It is unnecessarily restrictive for the clarified intent and
is **not** the recommendation merely because it has "Noncommercial" in its name.

For completeness: personal/hobby use and research without anticipated commercial application are
expressly included. Modifications and redistribution are permitted for licensed purposes, with
terms/URL and any supplied `Required Notice:` lines passed to recipients. A paid hosted service or
commercial consulting that requires using/modifying the software generally falls outside the
noncommercial-purpose permission; the charitable/educational/public-body exception and the separate
distribution grant complicate categorical conclusions about fee-bearing activities. Consulting
that does not exercise licensed rights is not automatically prohibited by this copyright grant.
It is not a copyleft licence and does not require publishing all modifications.

Its express patent licence covers licensable claims; written patent-infringement claims trigger
Patent Defense termination. The first-notified-violation cure period is 32 days. It preserves fair
use and has an as-is/no-liability clause. It is source-available, not OSI open source. No Other
Rights reserves the licensor's ability to grant other licences, which also conflicts with treating
it as a binding no-exceptions promise by the owner.

### Commons Clause: FAQ-based boundary

The operative Commons Clause v1.0 excludes the right to "Sell" where someone provides to third
parties for consideration a product/service whose value derives entirely or substantially from
the software's functionality. The definition specifically includes fees for hosting and related
consulting/support. The FAQ states that users may build on the software, embed it in larger sold
products, sell qualifying SaaS/products, and provide some consulting, provided what they sell is
not substantially the licensed software itself. The FAQ describes merely renaming it, changing
function/API names, or offering the same functionality as SaaS as still restricted; it says
"substantially" means for the most part/essentially.

This fits several examples: an ordinary paid VPS is not by itself a product whose value
substantially derives from ArtSniffer; a company can generally run the software internally; and a
genuinely unrelated commercial product is not barred merely for interoperability. A paid hosted
ArtSniffer service, repackaged copy, or lightly changed fork would likely fall within the intended
Sell restriction where its value remains substantially ArtSniffer functionality.

It does **not** reliably promise the stronger fork rule. The official FAQ explicitly permits
selling derivatives/products when value is added. There is no objective threshold that guarantees
that a substantially modified but "fundamentally ArtSniffer" application remains substantially the
licensed Software as a matter of every fact pattern. The clause's focus is charging third parties,
not making a copy available free of charge; it is not a share-alike condition requiring all
ArtSniffer-derived work to remain under the condition.

For the owner's examples, personal/research use, modification, free redistribution and business
internal use are generally permitted. Paid hosting/access to ArtSniffer itself is within the
restricted category when its value is substantially ArtSniffer functionality; a generic VPS
provider or unrelated product is not barred merely for making infrastructure or interoperating
software available. Fees for related hosting/consulting/support are named, but the substantial-
value test still applies; the official FAQ permits consulting and value-added products in some
cases. Modified copies may be redistributed, but charging for them is prohibited only when they
meet the Sell test, not by an express downstream no-fee/share-alike rule.

Apache-2.0 requires its licence and relevant copyright/attribution notices to be retained and
modified files to note changes; the Commons Clause condition must also accompany the licence
notice. Apache grants contributor patent rights subject to its patent-litigation termination;
Commons Clause supplies no separate patent grant. Apache has no copyleft requirement to publish
modification source, and its redistribution terms permit licensing modifications/derivatives on
different terms, subject to complying with the base and Sell restriction. The combination is
source-available, not OSI open source. The copyright holder retains its rights and can separately
license them, so the standard text does not commit MuffinzCat to the same no-charge rule.

Most importantly, neither Apache nor Commons Clause binds the licensor not to offer separate
commercial terms for rights it owns. The official Commons Clause was designed to let its licensors
negotiate for prohibited sales. It therefore conflicts with the owner's explicit no-special-
licence/no-owner-sale principle unless a separate enforceable commitment addresses it.

Do not adopt Apache + Commons Clause while describing it as guaranteeing that every fundamentally
ArtSniffer-derived fork remains free or that MuffinzCat can never charge for ArtSniffer.

### Other near-matches and OSI boundary

PolyForm Perimeter 1.0.1 is closer than PolyForm Noncommercial in allowing commercial/internal use.
Its Competition clause covers a substitute for the software's function/value regardless of whether
it is free, a service, library, plug-in or port. Thus it can prevent even a **free** competing
fork/hosted service, while not itself requiring every copy to be free of charge. Its No Other Rights
clause expressly says the licence does not prevent the licensor from granting licences to others.
It is a competition restriction, not the owner's distribution-price restriction.

Elastic License 2.0 permits commercial use, modification and redistribution but prevents substantial
hosted/managed service access; its official FAQ permits some managed hosting where customers lack
access to substantial functionality. It does not ban selling copies or charged modified
distributions. RSALv2 permits commercial use but restricts making the original or modified
software's functionality available to third parties, even beyond paid access. BSL explicitly
contemplates commercial licences for production use and later conversion to a Change License.
These are not free-for-everyone sale prohibitions.

The GPL/AGPL preserve source and downstream freedoms for covered derivatives, but the GNU FAQ
explicitly says a distributor may charge any price; recipients can then redistribute for free or
for a fee. Copyleft cannot make forks free of charge. Open Source Definition criterion 1 requires
that the licence not restrict selling/giving away the software and not require a royalty/fee for
sale. A licence prohibiting anyone from charging for ArtSniffer or its derivative copies therefore
cannot be OSI open source. Any accurate model with the intended price restriction would be
**source-available, not OSI open source**.

This audit found no established candidate that simultaneously: (1) permits commercial/internal
use; (2) permits modification and redistribution; (3) forbids all charges for original and
fundamentally ArtSniffer-derived applications, including qualifying forks; and (4) binds the owner
to the same no-charge rule. These conditions do not establish that no such text exists anywhere;
they mean no reviewed professional standard has been verified as a clear match. Do not patch a
standard text or invent a "no charge" addendum to force a fit.

## Dependency and redistribution compatibility

**ArtSniffer's own-source licence is separate from every dependency licence.** Imports of independent
permissively licensed packages do not generally require the importer itself to adopt their
licence. Redistributing those packages, their modified files or a bundled executable/container
does require compliance with their terms. An ArtSniffer-specific free-of-charge condition cannot
replace their notices or make their own copies noncommercial.

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
  Section 3.3 permits separately licensed larger works. Keep tqdm distinct; do not impose an
  ArtSniffer-specific free-of-charge restriction on its covered source. Its presence is not an
  automatic prohibition on licensing independent ArtSniffer code under a compatible condition.
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
- **Future copyleft imports require a fresh check.** A whole-work copyleft obligation can affect
  whether an ArtSniffer-specific price condition may be imposed on a combined derivative. No such
  whole-work licence was identified in the retrieved package declarations, but binary contents
  have not been certified.

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
**not** a legal conclusion about which grant controls every converted weight file. A licence for
ArtSniffer's own source cannot authorise a restricted checkpoint or third-party content.

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

**Do not change the licence.** This is not a finding that application code is affirmatively
ineligible for licensing: no affirmative third-party application-code blocker was found. It is
the finding that no reviewed standard licence matches the clarified restrictions and the available
repository evidence does not establish full title/authority. Unresolved binary dependency/EULA
questions primarily concern distribution of those artefacts, not licensing independent
ArtSniffer-owned source.

The owner/legal reviewer should resolve:

1. Whether to commission professional legal/licensing review of a purpose-built condition and
   owner commitment. The condition must distinguish charging for ArtSniffer/fundamentally
   ArtSniffer-derived applications from commercial use, generic infrastructure, hardware,
   unrelated integrations and separately valuable products. "Fundamentally ArtSniffer" needs a
   legally workable boundary that resists relabelling while not capturing unrelated works.
2. How the owner can be bound by the same no-charge rule. Standard non-exclusive licences normally
   govern recipients' exercise of licensed rights, not the copyright holder's retained rights.
   Consider enforceability, irrevocability, future owners and whether a public covenant or another
   legal structure is needed. A statement of intent alone may not bind a future rights-holder.
3. Whether "charging for ArtSniffer" includes donations, sponsorship, ads, pass-through costs,
   paid installation/maintenance, consulting, service-level commitments or hosting where users
   cannot access the software itself; preserve the owner's examples rather than defaulting to
   "no commercial use."
4. The copyright holder's identity/authority, any employer/client rights, contributor permissions,
   code-reference/snippet provenance and any earlier private/public grants not in Git. Future
   contributor terms must be compatible with the same downstream no-charge/fork policy; a DCO or
   GitHub account identity alone is not a copyright assignment.
5. Exact checkpoint licences/revisions and artefact-level dependency/EULA/notices for anything
   actually bundled. Keep these obligations distinct from licensing independent project source.

If professional review finds a standard licence and a binding owner arrangement that clearly
match, document that exact decision first. If it requires an altered standard text, newly written
condition or ancillary covenant, do not draft it as an informal report amendment: obtain and use
professionally prepared legal terms and review contributor/ownership authority before changing
`LICENSE`, README, NOTICE or package metadata. Preserve all independent third-party terms and explain
the scope/date and earlier-grant implications.

No licence adopted now means the source remains under the observed all-rights-reserved notice,
subject to law, GitHub terms and existing permissions; the intended free-use permissions are not
implemented. If the eventual restriction is imposed by licence, it is **source-available, not OSI
open source** because it forbids charging for copies/derivatives. It should permit commercial and
internal use otherwise, subject only to the clearly scoped charge prohibition. This report does
not imply that anyone (including the owner) is already bound by a future no-charge condition.

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
| PolyForm Perimeter 1.0.1 official text | <https://polyformproject.org/licenses/perimeter/1.0.1> and <https://github.com/polyformproject/polyformproject.org/blob/main/licenses/perimeter/1.0.1.txt> |
| Official PolyForm Strict text used for exclusion | <https://github.com/polyformproject/polyformproject.org/blob/main/licenses/strict/1.0.0.txt> |
| Commons Clause condition and official FAQ | <https://commonsclause.com/> |
| Commons Clause site's official source, pinned revision | <https://github.com/fossas/commons-clause/blob/a83b2c7466e31f6cb3b285b08319e8af357ea244/src/index.html> |
| Apache-2.0 official text | <https://www.apache.org/licenses/LICENSE-2.0> and <https://www.apache.org/licenses/LICENSE-2.0.txt>; complete terms retrieved via <https://github.com/apache/.github/blob/main/LICENSE> |
| MIT text/reference | <https://choosealicense.com/licenses/mit/> and <https://github.com/github/choosealicense.com/blob/gh-pages/_licenses/mit.txt> |
| CC0 legal text | <https://creativecommons.org/publicdomain/zero/1.0/legalcode>; full text read in github/gitignore LICENSE linked above |
| Open Source Definition, especially sections 1 and 6 | <https://opensource.org/osd> (official search evidence) |
| GNU GPL FAQ, charging a fee for copies | <https://www.gnu.org/licenses/gpl-faq.html#DoesTheGPLAllowSelling> (official search evidence) |
| GitHub Terms of Service, D and J | <https://docs.github.com/en/site-policy/github-terms/github-terms-of-service> (directly retrieved; effective date shown: 27 April 2026) |
| Mozilla MPL 2.0 official text | <https://www.mozilla.org/en-US/MPL/2.0/>; relevant sections retrieved via <https://github.com/github/choosealicense.com/blob/gh-pages/_licenses/mpl-2.0.txt> |
| Elastic License 2.0 and FAQ | <https://www.elastic.co/licensing/elastic-license> and <https://www.elastic.co/licensing/elastic-license/faq> (official search evidence) |
| Redis Source Available License v2 | <https://redis.io/legal/rsalv2-agreement/> (full official text retrieved) |
| Business Source License 1.1 | <https://mariadb.com/bsl11/> and <https://mariadb.com/bsl-faq-adopting/> (official search evidence) |
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
