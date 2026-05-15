"""
End-to-end integration tests for the unmasking-moments pipeline.

Companion to :mod:`world.tests.test_pierce_integration`.  Where the
pierce tests cover the *passive* recognition path (observer encounters a
disguised target on `look`), this module covers the *active* path:
observer is in the room when the target's identity signature mutates,
and :class:`world.identity.apply_signature_change` fires
:func:`world.identity._broadcast_unmasking` across the room's conscious
observers.

The existing unit tests in :mod:`world.tests.test_unmasking` cover the
4-cell broadcast matrix exhaustively with fake observer/target/room
objects.  This module's job is the integration tripwire: drive the
production call chain
(``apply_signature_change`` → ``_broadcast_unmasking`` →
recognition-memory mutation + per-cell narrative prose) on real
:class:`typeclasses.characters.Character` instances and assert the
visible end-to-end outcomes hold.

Run via::

    evennia test world.tests.test_unmasking_integration
"""

from __future__ import annotations

from unittest.mock import MagicMock

from evennia.utils.test_resources import EvenniaTest

from typeclasses.characters import Character
from world.identity import (
    apply_signature_change,
    get_apparent_uid,
    get_linked_aliases,
)


class TestUnmaskingIntegrationEndToEnd(EvenniaTest):
    """Drive the unmasking pipeline through real Character typeclasses.

    EvenniaTest creates ``self.char1`` and ``self.char2`` in
    ``self.room1`` automatically; we use char1 as the observer and
    char2 as the unmasking target.
    """

    character_typeclass = Character

    def setUp(self) -> None:
        super().setUp()
        self.observer = self.char1
        self.target = self.char2
        # Stable sleeve UIDs for deterministic signature derivation.
        self.observer.sleeve_uid = "sleeve-observer-001"
        self.target.sleeve_uid = "sleeve-target-002"
        # Known-empty recognition memory baselines.
        self.observer.recognition_memory = {}
        # Real sdesc components so get_sdesc() renders prose-worthy text
        # (otherwise it falls back to self.key and cell-B/D messages
        # short-circuit on the empty-sdesc defensive guard).
        self.target.height = "tall"
        self.target.build = "lean"
        self.target.sdesc_keyword = "man"
        # Capture observer-directed messages without going through the
        # account/session plumbing.  ``.msg()`` is a regular method on
        # DefaultObject so direct replacement is safe.
        self.observer.msg = MagicMock()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _seed_entry(
        self,
        uid: str,
        *,
        assigned_name: str = "",
        linked_to: str | None = None,
        sdesc: str = "a tall lean man",
    ) -> None:
        """Insert a minimal recognition-memory entry on the observer."""
        memory = dict(self.observer.recognition_memory or {})
        memory[uid] = {
            "assigned_name": assigned_name,
            "real_sleeve_uid": self.target.sleeve_uid,
            "times_seen": 1,
            "linked_to": linked_to,
            "sdesc_at_last_encounter": sdesc,
            "location_last_seen": self.room1.key,
            "last_seen": "2024-01-01T00:00:00+00:00",
            "lost_contact": False,
        }
        self.observer.recognition_memory = memory

    # ------------------------------------------------------------------
    # Cell B — knew old, not new
    # ------------------------------------------------------------------

    def test_cell_b_flips_lost_contact_and_auto_creates_new_entry(
        self,
    ) -> None:
        """Cell B: observer knows current presentation as 'Bruce';
        target dons a disguise (height_override flips Apparent UID).
        Old entry must flip to ``lost_contact=True`` and a new entry
        must auto-create with ``linked_to`` pointing at the old UID.
        """
        old_uid = get_apparent_uid(self.target)
        self.assertIsNotNone(old_uid)
        self._seed_entry(
            old_uid, assigned_name="Bruce", sdesc="a tall lean man"
        )

        with apply_signature_change(self.target, source="test:cell-b"):
            self.target.db.height_override = "short"

        memory = self.observer.recognition_memory
        new_uid = get_apparent_uid(self.target)
        self.assertNotEqual(old_uid, new_uid)

        # Old entry flipped.
        self.assertTrue(memory[old_uid]["lost_contact"])
        self.assertEqual(memory[old_uid]["assigned_name"], "Bruce")

        # New entry auto-created with linkage.
        self.assertIn(new_uid, memory)
        self.assertEqual(memory[new_uid]["linked_to"], old_uid)
        self.assertEqual(memory[new_uid]["assigned_name"], "")
        self.assertEqual(
            memory[new_uid]["real_sleeve_uid"], self.target.sleeve_uid
        )

        # Cell-B narrative prose fired.
        self.assertTrue(self.observer.msg.called)
        prose = self.observer.msg.call_args[0][0]
        self.assertIn("steps into view where", prose)

    # ------------------------------------------------------------------
    # Cell D — knew both presentations
    # ------------------------------------------------------------------

    def test_cell_d_links_known_presentations_and_emits_realize_prose(
        self,
    ) -> None:
        """Cell D: observer knows both 'Bruce' (current) and 'Wraith'
        (the disguised presentation) independently.  After the swap:
        old entry flips ``lost_contact``, new entry is refreshed,
        ``linked_to`` is set on the new entry, and the link-discovered
        prose fires.
        """
        old_uid = get_apparent_uid(self.target)
        self._seed_entry(
            old_uid, assigned_name="Bruce", sdesc="a tall lean man"
        )

        # Pre-compute the post-mutation UID by temporarily flipping
        # state, capturing the UID, then restoring.  This lets us seed
        # the 'knew new' entry before the broadcast fires.
        self.target.db.height_override = "short"
        new_uid = get_apparent_uid(self.target)
        self.target.db.height_override = None
        self.assertNotEqual(old_uid, new_uid)

        self._seed_entry(
            new_uid, assigned_name="Wraith", sdesc="a short lean man"
        )

        with apply_signature_change(self.target, source="test:cell-d"):
            self.target.db.height_override = "short"

        memory = self.observer.recognition_memory

        # Old entry flagged, name preserved.
        self.assertTrue(memory[old_uid]["lost_contact"])
        self.assertEqual(memory[old_uid]["assigned_name"], "Bruce")

        # New entry refreshed, name preserved, linked to old.
        self.assertFalse(memory[new_uid]["lost_contact"])
        self.assertEqual(memory[new_uid]["assigned_name"], "Wraith")
        self.assertEqual(memory[new_uid]["linked_to"], old_uid)

        # Cell-D narrative prose fired with both names.
        self.assertTrue(self.observer.msg.called)
        prose = self.observer.msg.call_args[0][0]
        self.assertIn("You realize that", prose)
        self.assertIn("Bruce", prose)
        self.assertIn("Wraith", prose)
        self.assertIn("same person", prose)

    def test_cell_d_does_not_overwrite_existing_linked_to(self) -> None:
        """Cell D's link write is **only-if-None** — a pre-existing
        ``linked_to`` (e.g. from a prior unmasking chain) is sacrosanct
        and must not be rewritten when the same swap re-occurs.
        """
        old_uid = get_apparent_uid(self.target)
        self._seed_entry(old_uid, assigned_name="Bruce")

        self.target.db.height_override = "short"
        new_uid = get_apparent_uid(self.target)
        self.target.db.height_override = None

        # Pre-seed the 'new' entry with a linked_to pointing at some
        # unrelated UID (simulates a prior chain).
        self._seed_entry(
            new_uid,
            assigned_name="Wraith",
            linked_to="uid-some-earlier-presentation",
            sdesc="a short lean man",
        )

        with apply_signature_change(self.target, source="test:cell-d-link"):
            self.target.db.height_override = "short"

        memory = self.observer.recognition_memory
        self.assertEqual(
            memory[new_uid]["linked_to"],
            "uid-some-earlier-presentation",
            "Pre-existing linked_to must not be overwritten by cell D.",
        )

    # ------------------------------------------------------------------
    # Chain rendering surfaces — get_linked_aliases on real memory
    # ------------------------------------------------------------------

    def test_get_linked_aliases_surfaces_prior_name_after_cell_b(
        self,
    ) -> None:
        """After cell B fires, the new entry's chain walks back to the
        bare-face entry, and :func:`get_linked_aliases` surfaces 'Bruce'
        — the same chain ``recall`` / ``memory`` render as
        'Also known as: ...'.
        """
        old_uid = get_apparent_uid(self.target)
        self._seed_entry(
            old_uid, assigned_name="Bruce", sdesc="a tall lean man"
        )

        with apply_signature_change(self.target, source="test:chain"):
            self.target.db.keyword_override = "stranger"

        new_uid = get_apparent_uid(self.target)
        memory = self.observer.recognition_memory
        aliases = get_linked_aliases(memory, new_uid)
        self.assertIn("Bruce", aliases)

    # ------------------------------------------------------------------
    # Negative path — no-op mutations do not fire broadcasts
    # ------------------------------------------------------------------

    def test_signature_unchanged_no_broadcast(self) -> None:
        """A ``with apply_signature_change`` block whose body does not
        actually change the Apparent UID must not mutate observer
        memory, must not emit prose, and must not touch ``lost_contact``
        on the seeded entry.
        """
        current_uid = get_apparent_uid(self.target)
        self._seed_entry(
            current_uid, assigned_name="Bruce", sdesc="a tall lean man"
        )

        with apply_signature_change(self.target, source="test:noop"):
            # Mutate a non-signature attribute.  ``db.notes`` is not in
            # the signature inputs, so the UID will not change and the
            # broadcast must short-circuit.
            self.target.db.notes = "scribble"

        memory = self.observer.recognition_memory
        self.assertFalse(memory[current_uid]["lost_contact"])
        self.assertEqual(memory[current_uid]["assigned_name"], "Bruce")
        # Only the originally-seeded entry should be present.
        self.assertEqual(set(memory.keys()), {current_uid})
        self.observer.msg.assert_not_called()
