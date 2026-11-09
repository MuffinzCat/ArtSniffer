"""Provider-neutral contract for observing reference source contents."""

from typing import Protocol

from artsniffer.references.observation import ReferenceItemObservation


class ReferenceProvider(Protocol):
    """Observe one configured source with a stable source_id for the instance's lifetime.

    Callers own disabled-source policy. Provider configuration, temporary artwork retrieval
    and orchestration are outside this protocol.
    """

    source_id: str

    def observe(self) -> tuple[ReferenceItemObservation, ...]:
        """Return a complete materialised snapshot of the configured source on success.

        Every observation must use this provider's exact source_id and a stable provider
        source_item_id, unique within the snapshot. Preserve identifiers and content hashes
        exactly, without normalisation; distinct item IDs may share a content hash.
        Providers define deterministic ordering for unchanged source state.

        An empty tuple means a genuinely empty successful snapshot. If a complete snapshot
        cannot be produced, fail rather than return partial or empty success. Provider
        exceptions propagate unchanged, without wrapping, retries or suppression.

        Concrete providers own these obligations; this protocol adds no runtime validation.
        """
        ...
