"""ArtSniffer's unconditional safety boundary.

This package represents the domain where content is rejected unconditionally by the safety gate.

Safety evidence and gate decisions are distinct from content ratings, raw moderation labels,
and semantic traits. Profile configuration cannot override a safety rejection. Evidence is
an unverified claim until evaluated with independently supplied authority grants. The
binding-aware evaluator requires every supplied binding to structurally match the requested
artwork and content version, then returns a decision bound to that subject and criteria set.
Binding authenticity remains the caller's responsibility. Only a cleared result exposes a
SafetyClearedSubject for downstream use.
"""
