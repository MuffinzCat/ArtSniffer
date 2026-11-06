"""ArtSniffer's unconditional safety boundary.

This package represents the domain where content is rejected unconditionally by the safety gate.

Safety evidence and gate decisions are distinct from content ratings, raw moderation labels,
and semantic traits. Profile configuration cannot override a safety rejection. Evidence is
an unverified claim, not a decision or a verified artwork binding. Pure evidence evaluation
uses independently supplied authority grants and fails closed without authorised clearance.
Subject and content-version binding remain deferred.
"""
