"""
Tests for Identity Phase 1c commands: ``@shortdesc`` and the memory
verb cluster (``remember``, ``forget``, ``recall``, ``memory``).

Tests the command logic and helper functions using mocks.
Run via::

    evennia test world.tests.test_identity_commands

All test cases match the specification in
``specs/IDENTITY_RECOGNITION_SPEC.md``.
"""

from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, patch, call


# ===================================================================
# Helpers — lightweight character stand-in
# ===================================================================


def _make_character(
    *,
    key="Jorge Jackson",
    sex="male",
    sdesc_keyword=None,
    height="tall",
    build="lean",
    sleeve_uid="uid-abc-123",
    hair_color=None,
    hair_style=None,
    recognition_memory=None,
    location=None,
):
    """Build a mock character with identity attributes."""
    from typeclasses.characters import Character

    char = MagicMock(spec=Character)
    char.key = key
    char.sex = sex
    char.sdesc_keyword = sdesc_keyword
    char.height = height
    char.build = build
    char.sleeve_uid = sleeve_uid
    char.hair_color = hair_color
    char.hair_style = hair_style
    char.recognition_memory = recognition_memory if recognition_memory is not None else {}

    # Hands / clothing
    char.hands = {"left": None, "right": None}
    char.worn_items = {}

    def _coverage_map():
        coverage = {}
        if char.worn_items:
            for loc, items in char.worn_items.items():
                if items:
                    coverage[loc] = items[0]
        return coverage

    char._build_clothing_coverage_map = _coverage_map

    # Bind real methods
    char.get_distinguishing_feature = (
        lambda: Character.get_distinguishing_feature(char)
    )
    char.get_sdesc = lambda: Character.get_sdesc(char)
    char.get_display_name = (
        lambda looker=None, **kw: Character.get_display_name(char, looker, **kw)
    )

    # gender property
    sex_val = (sex or "ambiguous").lower().strip()
    if sex_val in ("male", "man", "masculine", "m"):
        type(char).gender = PropertyMock(return_value="male")
    elif sex_val in ("female", "woman", "feminine", "f"):
        type(char).gender = PropertyMock(return_value="female")
    else:
        type(char).gender = PropertyMock(return_value="neutral")

    # Location
    if location is None:
        location = MagicMock()
        location.key = "Test Room"
    char.location = location

    return char


# ===================================================================
# @shortdesc — instant set mode
# ===================================================================


class TestShortdescInstantSet(TestCase):
    """Test the _set_keyword logic from CmdShortdesc."""

    def test_valid_keyword_sets_attribute(self):
        """Valid keyword is stored on the character."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(sex="male", sdesc_keyword=None)
        cmd = CmdShortdesc()
        cmd.caller = char
        cmd._set_keyword(char, "dude")
        self.assertEqual(char.sdesc_keyword, "dude")

    def test_invalid_keyword_rejected(self):
        """Non-alpha keyword produces error and does not change attribute."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(sex="male", sdesc_keyword="man")
        cmd = CmdShortdesc()
        cmd.caller = char
        cmd._set_keyword(char, "cyber2punk")
        # Should still be "man"
        self.assertEqual(char.sdesc_keyword, "man")
        char.msg.assert_called()
        msg_text = char.msg.call_args[0][0]
        self.assertIn("not a valid keyword", msg_text)

    def test_gender_gated_keyword(self):
        """Male character cannot use a feminine-only keyword."""
        from commands.CmdCharacter import CmdShortdesc
        from world.identity import (
            _DEFAULT_FEMININE_KEYWORDS,
            _DEFAULT_NEUTRAL_KEYWORDS,
        )

        # Pick a keyword that's feminine-only (not in neutral)
        feminine_only = _DEFAULT_FEMININE_KEYWORDS - _DEFAULT_NEUTRAL_KEYWORDS
        kw = sorted(feminine_only)[0]

        char = _make_character(sex="male", sdesc_keyword="man")
        cmd = CmdShortdesc()
        cmd.caller = char
        cmd._set_keyword(char, kw)
        # Should still be "man"
        self.assertEqual(char.sdesc_keyword, "man")
        char.msg.assert_called()
        msg_text = char.msg.call_args[0][0]
        self.assertIn("not available", msg_text)

    def test_neutral_keyword_available_to_all(self):
        """Neutral keywords are available to any gender."""
        from commands.CmdCharacter import CmdShortdesc

        for sex in ("male", "female", "ambiguous"):
            char = _make_character(sex=sex, sdesc_keyword=None)
            cmd = CmdShortdesc()
            cmd.caller = char
            cmd._set_keyword(char, "person")
            self.assertEqual(char.sdesc_keyword, "person")

    def test_sdesc_updates_after_keyword_change(self):
        """After changing keyword, get_sdesc reflects it."""
        char = _make_character(
            sex="male",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )
        self.assertEqual(char.get_sdesc(), "gaunt man")

        # Change keyword
        char.sdesc_keyword = "punk"
        self.assertEqual(char.get_sdesc(), "gaunt punk")


# ===================================================================
# @shortdesc — EvMenu helpers
# ===================================================================


class TestShortdescMenuHelpers(TestCase):
    """Test the EvMenu goto-callable for keyword selection."""

    def test_numeric_selection(self):
        """Entering a number selects the keyword at that index."""
        from commands.CmdCharacter import _process_keyword_choice

        char = _make_character(sex="male", sdesc_keyword=None)
        keywords = ["bro", "dude", "guy", "man", "person"]
        char.ndb._shortdesc_keywords = keywords

        # Select "2" → "dude" (index 1)
        result = _process_keyword_choice(char, "2")
        self.assertEqual(char.sdesc_keyword, "dude")

    def test_name_selection(self):
        """Entering a keyword name selects it."""
        from commands.CmdCharacter import _process_keyword_choice

        char = _make_character(sex="male", sdesc_keyword=None)
        keywords = ["bro", "dude", "guy", "man", "person"]
        char.ndb._shortdesc_keywords = keywords

        result = _process_keyword_choice(char, "guy")
        self.assertEqual(char.sdesc_keyword, "guy")

    def test_invalid_number_rejected(self):
        """Out-of-range number shows error and returns None (re-display)."""
        from commands.CmdCharacter import _process_keyword_choice

        char = _make_character(sex="male", sdesc_keyword="man")
        keywords = ["bro", "dude", "guy", "man", "person"]
        char.ndb._shortdesc_keywords = keywords

        result = _process_keyword_choice(char, "99")
        self.assertIsNone(result)
        char.msg.assert_called()
        msg_text = char.msg.call_args[0][0]
        self.assertIn("Invalid number", msg_text)

    def test_invalid_text_rejected(self):
        """Unknown text shows error and returns None (re-display)."""
        from commands.CmdCharacter import _process_keyword_choice

        char = _make_character(sex="male", sdesc_keyword="man")
        keywords = ["bro", "dude", "guy", "man", "person"]
        char.ndb._shortdesc_keywords = keywords

        result = _process_keyword_choice(char, "xyzinvalid")
        self.assertIsNone(result)
        char.msg.assert_called()
        msg_text = char.msg.call_args[0][0]
        self.assertIn("not a valid keyword", msg_text)

    def test_empty_input_redisplays(self):
        """Empty input returns None (re-display)."""
        from commands.CmdCharacter import _process_keyword_choice

        char = _make_character(sex="male", sdesc_keyword="man")
        char.ndb._shortdesc_keywords = ["man"]

        result = _process_keyword_choice(char, "   ")
        self.assertIsNone(result)


# ===================================================================
# remember command
# ===================================================================


class TestRememberCommand(TestCase):
    """Test the remember command's internal logic."""

    def test_remember_target_creates_memory(self):
        """Remembering someone creates a recognition memory entry."""
        from commands.CmdCharacter import CmdRemember

        caller = _make_character(key="Observer", sleeve_uid="uid-observer")
        target = _make_character(
            key="Jorge",
            sleeve_uid="uid-target",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )

        cmd = CmdRemember()
        cmd.caller = caller
        cmd._remember_target(caller, target, "uid-target", "Big J")

        memory = caller.recognition_memory
        self.assertIn("uid-target", memory)
        self.assertEqual(memory["uid-target"]["assigned_name"], "Big J")
        self.assertEqual(memory["uid-target"]["times_seen"], 1)

    def test_display_name_changes_after_remember(self):
        """After remembering, get_display_name returns the chosen name."""
        caller = _make_character(key="Observer", sleeve_uid="uid-observer")
        target = _make_character(
            key="Jorge",
            sleeve_uid="uid-target",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )

        # Before — stranger
        self.assertEqual(target.get_display_name(caller), "a gaunt man")

        # Manually set recognition memory (simulating what remember does)
        caller.recognition_memory = {
            "uid-target": {"assigned_name": "Big J"},
        }
        self.assertEqual(target.get_display_name(caller), "Big J")

    def test_re_remember_updates_name(self):
        """Re-remembering updates the name and increments times_seen."""
        from commands.CmdCharacter import CmdRemember

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory={
                "uid-target": {
                    "assigned_name": "Big J",
                    "first_seen": "2026-01-01T00:00:00",
                    "last_seen": "2026-01-01T00:00:00",
                    "times_seen": 3,
                    "location_first_seen": "Bar",
                    "location_last_seen": "Bar",
                    "locations_seen": ["Bar"],
                    "sdesc_at_first_encounter": "gaunt man",
                    "sdesc_at_last_encounter": "gaunt man",
                    "notes": "",
                    "tags": [],
                    "confidence": 1.0,
                    "relationship_valence": "neutral",
                    "recent_interactions": [],
                },
            },
        )
        target = _make_character(
            key="Jorge",
            sleeve_uid="uid-target",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )

        cmd = CmdRemember()
        cmd.caller = caller
        cmd._remember_target(caller, target, "uid-target", "Jorge")

        memory = caller.recognition_memory
        self.assertEqual(memory["uid-target"]["assigned_name"], "Jorge")
        self.assertEqual(memory["uid-target"]["times_seen"], 4)

    def test_remember_preserves_existing_fields(self):
        """Re-remembering preserves notes, tags, etc."""
        from commands.CmdCharacter import CmdRemember

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory={
                "uid-target": {
                    "assigned_name": "Big J",
                    "first_seen": "2026-01-01T00:00:00",
                    "last_seen": "2026-01-01T00:00:00",
                    "times_seen": 1,
                    "location_first_seen": "Bar",
                    "location_last_seen": "Bar",
                    "locations_seen": ["Bar"],
                    "sdesc_at_first_encounter": "gaunt man",
                    "sdesc_at_last_encounter": "gaunt man",
                    "notes": "Seems dangerous",
                    "tags": ["ally"],
                    "confidence": 0.8,
                    "relationship_valence": "friendly",
                    "recent_interactions": [],
                },
            },
        )
        target = _make_character(
            key="Jorge",
            sleeve_uid="uid-target",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )

        cmd = CmdRemember()
        cmd.caller = caller
        cmd._remember_target(caller, target, "uid-target", "J-Dog")

        memory = caller.recognition_memory
        entry = memory["uid-target"]
        self.assertEqual(entry["assigned_name"], "J-Dog")
        self.assertEqual(entry["notes"], "Seems dangerous")
        self.assertEqual(entry["tags"], ["ally"])
        self.assertEqual(entry["confidence"], 0.8)
        self.assertEqual(entry["relationship_valence"], "friendly")
        self.assertEqual(entry["first_seen"], "2026-01-01T00:00:00")


# ===================================================================
# forget command
# ===================================================================


def _seed_memory(uid="uid-target", name="Big J"):
    """Build a populated recognition_memory dict for a single target."""
    return {
        uid: {
            "assigned_name": name,
            "first_seen": "2026-01-01T00:00:00",
            "last_seen": "2026-01-01T00:00:00",
            "times_seen": 2,
            "location_first_seen": "The Grit",
            "location_last_seen": "Back Alley",
            "locations_seen": ["The Grit", "Back Alley"],
            "sdesc_at_first_encounter": "a gaunt man",
            "sdesc_at_last_encounter": "a gaunt man in a hood",
            "notes": "",
            "tags": [],
            "confidence": 1.0,
            "relationship_valence": "neutral",
            "recent_interactions": [],
        },
    }


class TestForgetCommand(TestCase):
    """Test the forget command."""

    def test_forget_visible_target_clears_name(self):
        """forget <visible target> blanks assigned_name, preserves entry."""
        from commands.CmdCharacter import CmdForget

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory=_seed_memory(),
        )
        target = _make_character(
            key="Jorge",
            sleeve_uid="uid-target",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )

        cmd = CmdForget()
        cmd.caller = caller
        cmd._forget_visible(caller, target, "uid-target")

        memory = caller.recognition_memory
        self.assertIn("uid-target", memory)
        self.assertEqual(memory["uid-target"]["assigned_name"], "")
        # History preserved
        self.assertEqual(memory["uid-target"]["times_seen"], 2)
        self.assertEqual(
            memory["uid-target"]["sdesc_at_first_encounter"], "a gaunt man"
        )

    def test_forget_remembered_name_when_target_absent(self):
        """forget <remembered name> works without target object."""
        from commands.CmdCharacter import CmdForget, _find_remembered_uid_by_name

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory=_seed_memory(),
        )

        sleeve_uid, entry = _find_remembered_uid_by_name(caller, "big j")
        self.assertEqual(sleeve_uid, "uid-target")

        cmd = CmdForget()
        cmd.caller = caller
        cmd._forget_remembered(caller, sleeve_uid, entry)

        memory = caller.recognition_memory
        self.assertEqual(memory["uid-target"]["assigned_name"], "")
        # Output message references snapshot data
        msg_text = caller.msg.call_args[0][0]
        self.assertIn("Big J", msg_text)
        self.assertIn("Back Alley", msg_text)

    def test_forget_unknown_name(self):
        """forget <unknown name> with empty memory rejects gracefully."""
        from commands.CmdCharacter import _find_remembered_uid_by_name

        caller = _make_character(key="Observer", sleeve_uid="uid-observer")
        sleeve_uid, entry = _find_remembered_uid_by_name(caller, "ghost")
        self.assertIsNone(sleeve_uid)
        self.assertIsNone(entry)

    def test_forget_visible_with_no_assigned_name(self):
        """forget on someone with a blank assigned_name reports correctly."""
        from commands.CmdCharacter import CmdForget

        memory = _seed_memory()
        memory["uid-target"]["assigned_name"] = ""
        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory=memory,
        )
        target = _make_character(
            key="Jorge",
            sleeve_uid="uid-target",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )

        cmd = CmdForget()
        cmd.caller = caller
        cmd._forget_visible(caller, target, "uid-target")

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("don't have a name", msg_text)


# ===================================================================
# recall command
# ===================================================================


class TestRecallCommand(TestCase):
    """Test the recall command."""

    def test_recall_renders_full_entry(self):
        """recall outputs assigned name, first sdesc, location, when, count."""
        from commands.CmdCharacter import CmdRecall

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory=_seed_memory(),
        )

        cmd = CmdRecall()
        cmd.caller = caller
        cmd._render_entry(caller, caller.recognition_memory["uid-target"])

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("Big J", msg_text)
        self.assertIn("a gaunt man", msg_text)
        self.assertIn("The Grit", msg_text)
        self.assertIn("seen 2 times", msg_text)

    def test_recall_blank_assigned_name_shows_unnamed_message(self):
        """Entry with blank assigned_name renders the 'no name' header."""
        from commands.CmdCharacter import CmdRecall

        memory = _seed_memory()
        memory["uid-target"]["assigned_name"] = ""
        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory=memory,
        )

        cmd = CmdRecall()
        cmd.caller = caller
        cmd._render_entry(caller, memory["uid-target"])

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("don't have a name", msg_text)
        # Snapshot still rendered
        self.assertIn("a gaunt man", msg_text)

    def test_recall_singular_seen_count(self):
        """times_seen of 1 renders 'time' (singular), not 'times'."""
        from commands.CmdCharacter import CmdRecall

        memory = _seed_memory()
        memory["uid-target"]["times_seen"] = 1
        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory=memory,
        )

        cmd = CmdRecall()
        cmd.caller = caller
        cmd._render_entry(caller, memory["uid-target"])

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("seen 1 time", msg_text)
        self.assertNotIn("seen 1 times", msg_text)


# ===================================================================
# memory command
# ===================================================================


class TestMemoryCommand(TestCase):
    """Test the memory command."""

    def test_memory_empty(self):
        """memory with no entries reports the empty state."""
        from commands.CmdCharacter import CmdMemory

        caller = _make_character(key="Observer", sleeve_uid="uid-observer")
        cmd = CmdMemory()
        cmd.caller = caller
        cmd.args = ""
        cmd.func()

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("don't remember anyone", msg_text)

    def test_memory_lists_named_entries(self):
        """memory lists each entry with a non-blank assigned_name."""
        from commands.CmdCharacter import CmdMemory

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory={
                "uid-a": {
                    "assigned_name": "Alice",
                    "last_seen": "2026-05-10T00:00:00",
                    "sdesc_at_last_encounter": "a tall woman",
                    "location_last_seen": "Bar",
                },
                "uid-b": {
                    "assigned_name": "Bob",
                    "last_seen": "2026-05-12T00:00:00",
                    "sdesc_at_last_encounter": "a short man",
                    "location_last_seen": "Alley",
                },
            },
        )
        cmd = CmdMemory()
        cmd.caller = caller
        cmd.args = ""
        cmd.func()

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("Alice", msg_text)
        self.assertIn("Bob", msg_text)

    def test_memory_excludes_blank_names(self):
        """Entries with blank assigned_name are excluded from listing."""
        from commands.CmdCharacter import CmdMemory

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory={
                "uid-a": {
                    "assigned_name": "Alice",
                    "last_seen": "2026-05-10T00:00:00",
                    "sdesc_at_last_encounter": "a tall woman",
                    "location_last_seen": "Bar",
                },
                "uid-b": {
                    "assigned_name": "",  # forgotten
                    "last_seen": "2026-05-12T00:00:00",
                    "sdesc_at_last_encounter": "a short man",
                    "location_last_seen": "Alley",
                },
            },
        )
        cmd = CmdMemory()
        cmd.caller = caller
        cmd.args = ""
        cmd.func()

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("Alice", msg_text)
        self.assertNotIn("a short man", msg_text)

    def test_memory_recency_sort(self):
        """Entries sort by last_seen descending."""
        from commands.CmdCharacter import CmdMemory

        caller = _make_character(
            key="Observer",
            sleeve_uid="uid-observer",
            recognition_memory={
                "uid-old": {
                    "assigned_name": "Older",
                    "last_seen": "2026-01-01T00:00:00",
                    "sdesc_at_last_encounter": "x",
                    "location_last_seen": "y",
                },
                "uid-new": {
                    "assigned_name": "Newer",
                    "last_seen": "2026-12-01T00:00:00",
                    "sdesc_at_last_encounter": "x",
                    "location_last_seen": "y",
                },
            },
        )
        cmd = CmdMemory()
        cmd.caller = caller
        cmd.args = ""
        cmd.func()

        msg_text = caller.msg.call_args[0][0]
        # Newer should appear before Older in the rendered table
        self.assertLess(msg_text.index("Newer"), msg_text.index("Older"))

    def test_memory_rejects_arguments(self):
        """memory with args returns a usage hint."""
        from commands.CmdCharacter import CmdMemory

        caller = _make_character(key="Observer", sleeve_uid="uid-observer")
        cmd = CmdMemory()
        cmd.caller = caller
        cmd.args = "something"
        cmd.func()

        msg_text = caller.msg.call_args[0][0]
        self.assertIn("Usage: memory", msg_text)


# ===================================================================
# @shortdesc — custom keyword acceptance
# ===================================================================


class TestShortdescCustomKeyword(TestCase):
    """Test that @shortdesc accepts arbitrary valid custom keywords."""

    def test_custom_keyword_accepted(self):
        """A novel alpha-only word is accepted as a custom keyword."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(sex="male", sdesc_keyword="man")
        cmd = CmdShortdesc()
        cmd.caller = char
        with patch("world.identity.log_custom_keyword") as mock_log:
            cmd._set_keyword(char, "ronin")
        self.assertEqual(char.sdesc_keyword, "ronin")
        mock_log.assert_called_once_with(
            "ronin", char.key, account=char.account,
        )

    def test_custom_keyword_not_logged_for_approved(self):
        """Approved keywords bypass the catalog entirely."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(sex="male", sdesc_keyword="man")
        cmd = CmdShortdesc()
        cmd.caller = char
        with patch("world.identity.log_custom_keyword") as mock_log:
            cmd._set_keyword(char, "dude")
        self.assertEqual(char.sdesc_keyword, "dude")
        mock_log.assert_not_called()

    def test_custom_keyword_rejected_with_digits(self):
        """Keywords containing digits are rejected."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(sex="male", sdesc_keyword="man")
        cmd = CmdShortdesc()
        cmd.caller = char
        cmd._set_keyword(char, "r0nin")
        self.assertEqual(char.sdesc_keyword, "man")
        msg_text = char.msg.call_args[0][0]
        self.assertIn("letters", msg_text)

    def test_custom_keyword_rejected_too_short(self):
        """Single-character keyword is rejected."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(sex="male", sdesc_keyword="man")
        cmd = CmdShortdesc()
        cmd.caller = char
        cmd._set_keyword(char, "x")
        self.assertEqual(char.sdesc_keyword, "man")

    def test_custom_keyword_shows_sdesc(self):
        """Confirmation message includes updated sdesc."""
        from commands.CmdCharacter import CmdShortdesc

        char = _make_character(
            sex="male",
            height="tall",
            build="lean",
            sdesc_keyword="man",
        )
        cmd = CmdShortdesc()
        cmd.caller = char
        with patch("world.identity.log_custom_keyword"):
            cmd._set_keyword(char, "samurai")
        # sdesc_keyword should be updated
        self.assertEqual(char.sdesc_keyword, "samurai")
        msg_text = char.msg.call_args[0][0]
        self.assertIn("samurai", msg_text)


# ===================================================================
# Custom keyword catalog — log_custom_keyword
# ===================================================================


class TestLogCustomKeyword(TestCase):
    """Test event logging via :func:`log_custom_keyword`."""

    def _mock_keyword_event(self):
        """Return a mock ``world.models`` module with KeywordEvent stub.

        ``world.models`` can't be imported during default-settings tests
        (``world`` isn't in INSTALLED_APPS for the test runner).  We
        inject a fake module into ``sys.modules`` instead.
        """
        mock_module = MagicMock()
        mock_create = mock_module.KeywordEvent.objects.create
        return mock_module, mock_create

    def test_custom_keyword_logged(self):
        """Novel keyword creates a KeywordEvent record."""
        from world.identity import log_custom_keyword

        mock_module, mock_create = self._mock_keyword_event()

        with patch.dict("sys.modules", {"world.models": mock_module}):
            with patch(
                "world.identity.get_all_keywords", return_value=frozenset()
            ):
                log_custom_keyword("ronin", "Alice")

        mock_create.assert_called_once_with(
            event_type="custom_set",
            keyword="ronin",
            character_name="Alice",
            account_name="",
        )

    def test_custom_keyword_logged_with_account(self):
        """Account name is included when account is provided."""
        from world.identity import log_custom_keyword

        mock_module, mock_create = self._mock_keyword_event()

        account = MagicMock()
        account.key = "player1"

        with patch.dict("sys.modules", {"world.models": mock_module}):
            with patch(
                "world.identity.get_all_keywords", return_value=frozenset()
            ):
                log_custom_keyword("ronin", "Alice", account=account)

        mock_create.assert_called_once_with(
            event_type="custom_set",
            keyword="ronin",
            character_name="Alice",
            account_name="player1",
        )

    def test_approved_keyword_not_logged(self):
        """Keywords from the approved lists are silently ignored."""
        from world.identity import log_custom_keyword

        mock_module, mock_create = self._mock_keyword_event()

        with patch.dict("sys.modules", {"world.models": mock_module}):
            with patch(
                "world.identity.get_all_keywords",
                return_value=frozenset({"man"}),
            ):
                log_custom_keyword("man", "Alice")

        mock_create.assert_not_called()

    def test_multiple_keywords_each_logged(self):
        """Multiple distinct keywords each create their own event."""
        from world.identity import log_custom_keyword

        mock_module, mock_create = self._mock_keyword_event()

        with patch.dict("sys.modules", {"world.models": mock_module}):
            with patch(
                "world.identity.get_all_keywords", return_value=frozenset()
            ):
                log_custom_keyword("ronin", "Alice")
                log_custom_keyword("wraith", "Bob")

        self.assertEqual(mock_create.call_count, 2)
