"""ArtSniffer's unconditional safety boundary.

This package represents the domain where content is rejected unconditionally by the safety gate.

Safety gate decisions are distinct from content ratings, raw moderation labels, and semantic
traits. Profile configuration cannot override a safety rejection. Concrete safety evaluation
is intentionally deferred to a future feature that will define the provider-neutral input
model and evaluation contract.
"""
