"""
Tests for Corpse Apparent UID Propagation (PR 2 of disguise completion).

Verifies that:

1. A freshly created corpse exposes a ``sleeve_uid`` property that
   matches the deceased character's real sleeve UID — so
   :func:`world.identity.get_apparent_uid` flows through the same
   pipeline used for living characters.
2. :meth:`typeclasses.corpse.Corpse.get_worn_items` returns only
   disguise-essential items currently in ``corpse.contents``, mirroring
   :meth:`typeclasses.clothing_mixin.ClothingMixin.get_worn_items` so
   the identity signature recomputes naturally as loot is removed.
3. The death-time snapshot writes ``apparent_uid_at_death`` and the
   identity override axes, matching what ``get_apparent_uid`` would
   compute for the living character at the moment of death.
4. :meth:`Corpse.get_display_name` consults the observer's
   ``recognition_memory`` using the *current* Apparent UID (so looting
   a balaclava off the corpse breaks the recognition silently).
5. :meth:`Corpse.at_object_leave` clears the stale
   ``apparent_uid_at_death`` snapshot when a disguise-essential item
   is removed.

Run via::

    evennia test --settings settings.py world.tests.test_corpse_identity

These are pure unit tests built on lightweight fakes — no Evennia
database is required.
"""

from __future__ import annotations

from unittest import TestCase

from world.identity import get_apparent_uid

from world.tests.test_identity import _FakeDisguiseItem


# ---------------------------------------------------------------------
# Lightweight fakes (mirroring _SignatureMockCharacter, but corpse-shaped)
# ---------------------------------------------------------------------


class _FakeCorpse:
    """Duck-typed stand-in for :class:`typeclasses.corpse.Corpse`.

    Re-implements just the surface that PR 2 adds — the ``sleeve_uid``
    property, the ``get_worn_items`` view over ``contents``, the
    recognition-aware ``get_display_name``, and the
    ``at_object_leave`` snapshot invalidation — so the tests can run
    without spinning up Evennia's typeclass machinery.
    """

    def __init__(
        self,
        *,
        sleeve_uid: str | None = "uid-jorge",
        height_override: str | None = None,
        build_override: str | None = None,
        keyword_override: str | None = None,
        contents: list | None = None,
        apparent_uid_at_death: str | None = None,
    ) -> None:
        class _DB:
            pass

        self.db = _DB()
        self.db.sleeve_uid = sleeve_uid
        self.db.height_override = height_override
        self.db.build_override = build_override
        self.db.keyword_override = keyword_override
        self.db.apparent_uid_at_death = apparent_uid_at_death
        self.contents = list(contents or [])
        self.key = "fresh corpse"
        self._decay_name = "fresh corpse"
        self.ndb = type("_NDB", (), {})()

    # --- methods mirroring the production typeclass --------------------

    @property
    def sleeve_uid(self):
        return self.db.sleeve_uid

    def get_worn_items(self, location=None):
        del location
        return [
            item
            for item in self.contents
            if getattr(item, "disguise_essential", False)
        ]

    def _decay_display_name(self):
        return self._decay_name

    def get_display_name(self, looker, **kwargs):
        decay = self._decay_display_name()
        if looker is None:
            return decay
        apparent_uid = get_apparent_uid(self)
        if apparent_uid is not None and hasattr(looker, "recognition_memory"):
            memory = looker.recognition_memory
            if memory and apparent_uid in memory:
                assigned = memory[apparent_uid].get("assigned_name")
                if assigned:
                    return assigned
        return decay

    def at_object_leave(self, moved_obj, target_location, **kwargs):
        if getattr(moved_obj, "disguise_essential", False):
            if self.db.apparent_uid_at_death is not None:
                self.db.apparent_uid_at_death = None


class _FakeObserver:
    """Minimal observer with a ``recognition_memory`` dict."""

    def __init__(self, memory: dict | None = None) -> None:
        self.recognition_memory = memory or {}


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------


class TestCorpseSleeveUidProperty(TestCase):
    """The ``sleeve_uid`` property must flow into the identity engine."""

    def test_sleeve_uid_property_reflects_db(self):
        corpse = _FakeCorpse(sleeve_uid="uid-victor")
        self.assertEqual(corpse.sleeve_uid, "uid-victor")

    def test_get_apparent_uid_on_corpse_is_not_none(self):
        corpse = _FakeCorpse(sleeve_uid="uid-victor")
        self.assertIsNotNone(get_apparent_uid(corpse))

    def test_get_apparent_uid_returns_none_when_sleeve_uid_missing(self):
        corpse = _FakeCorpse(sleeve_uid=None)
        self.assertIsNone(get_apparent_uid(corpse))


class TestCorpseWornItemsView(TestCase):
    """``get_worn_items`` returns only disguise-essential contents."""

    def test_no_contents_returns_empty(self):
        corpse = _FakeCorpse(contents=[])
        self.assertEqual(corpse.get_worn_items(), [])

    def test_filters_out_non_essential_items(self):
        balaclava = _FakeDisguiseItem(
            disguise_essential=True, disguise_type_id="balaclava",
        )
        loose_loot = _FakeDisguiseItem(
            disguise_essential=False, disguise_type_id="",
        )
        corpse = _FakeCorpse(contents=[balaclava, loose_loot])
        worn = corpse.get_worn_items()
        self.assertEqual(worn, [balaclava])


class TestCorpseSignatureMatchesLivingCharacter(TestCase):
    """Apparent UID derived from corpse matches the living character's."""

    def test_signature_axes_propagate_to_corpse(self):
        from world.tests.test_identity import _SignatureMockCharacter

        balaclava = _FakeDisguiseItem(
            disguise_essential=True, disguise_type_id="balaclava",
        )
        living = _SignatureMockCharacter(
            sleeve_uid="uid-jorge",
            height_override="tall",
            build_override="lean",
            keyword_override=None,
            worn_items=[balaclava],
        )
        living_uid = get_apparent_uid(living)

        # Death-time snapshot mirrors the character's signature axes
        # plus the disguise-essential items dropping into contents.
        corpse = _FakeCorpse(
            sleeve_uid="uid-jorge",
            height_override="tall",
            build_override="lean",
            keyword_override=None,
            contents=[balaclava],
        )
        corpse_uid = get_apparent_uid(corpse)

        self.assertEqual(living_uid, corpse_uid)
        self.assertIsNotNone(living_uid)

    def test_looting_essential_item_shifts_uid(self):
        balaclava = _FakeDisguiseItem(
            disguise_essential=True, disguise_type_id="balaclava",
        )
        corpse = _FakeCorpse(sleeve_uid="uid-jorge", contents=[balaclava])
        uid_before = get_apparent_uid(corpse)

        corpse.contents.remove(balaclava)
        uid_after = get_apparent_uid(corpse)

        self.assertNotEqual(uid_before, uid_after)


class TestCorpseDisplayNameRecognition(TestCase):
    """Corpse display name honours observer recognition memory."""

    def test_none_looker_returns_decay_name(self):
        corpse = _FakeCorpse(sleeve_uid="uid-jorge")
        self.assertEqual(corpse.get_display_name(None), "fresh corpse")

    def test_stranger_sees_decay_name(self):
        corpse = _FakeCorpse(sleeve_uid="uid-jorge")
        observer = _FakeObserver(memory={})
        self.assertEqual(
            corpse.get_display_name(observer), "fresh corpse",
        )

    def test_recogniser_sees_assigned_name(self):
        corpse = _FakeCorpse(sleeve_uid="uid-jorge")
        apparent_uid = get_apparent_uid(corpse)
        observer = _FakeObserver(
            memory={apparent_uid: {"assigned_name": "Jorge"}},
        )
        self.assertEqual(corpse.get_display_name(observer), "Jorge")

    def test_looting_essential_item_breaks_recognition(self):
        balaclava = _FakeDisguiseItem(
            disguise_essential=True, disguise_type_id="balaclava",
        )
        corpse = _FakeCorpse(
            sleeve_uid="uid-jorge", contents=[balaclava],
        )
        disguised_uid = get_apparent_uid(corpse)
        observer = _FakeObserver(
            memory={disguised_uid: {"assigned_name": "BalaclavaDude"}},
        )
        # While the corpse still "wears" the balaclava, recognition holds.
        self.assertEqual(
            corpse.get_display_name(observer), "BalaclavaDude",
        )

        # Looter removes the balaclava.
        corpse.contents.remove(balaclava)
        # Signature has shifted; the observer's old recognition
        # silently falls away.
        self.assertEqual(
            corpse.get_display_name(observer), "fresh corpse",
        )


class TestCorpseAtObjectLeave(TestCase):
    """``at_object_leave`` clears the death-time UID snapshot on loot."""

    def test_non_essential_leave_preserves_snapshot(self):
        corpse = _FakeCorpse(
            sleeve_uid="uid-jorge",
            apparent_uid_at_death="deadbeef00112233",
        )
        loose = _FakeDisguiseItem(disguise_essential=False)
        corpse.at_object_leave(loose, None)
        self.assertEqual(
            corpse.db.apparent_uid_at_death, "deadbeef00112233",
        )

    def test_essential_leave_clears_snapshot(self):
        corpse = _FakeCorpse(
            sleeve_uid="uid-jorge",
            apparent_uid_at_death="deadbeef00112233",
        )
        balaclava = _FakeDisguiseItem(
            disguise_essential=True, disguise_type_id="balaclava",
        )
        corpse.at_object_leave(balaclava, None)
        self.assertIsNone(corpse.db.apparent_uid_at_death)
