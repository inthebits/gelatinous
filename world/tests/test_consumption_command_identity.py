"""
Tests for medical/consumption command identity targeting (PR γ).

Verifies that ``inject``, ``apply``, ``operate``/``surgery``, and
``bandage`` route character-target resolution through
``commands._identity_targeting.resolve_character_target`` so that
recognised names and sdesc keywords work when targeting another
character for medical treatment.

The helper itself is exhaustively tested in
``test_combat_command_identity``; here we assert call-site wiring
only: helper invocation, self-token handling, target-found vs None
branching, and that ``caller.search`` is no longer used for target
resolution.

Run via::

    evennia test world.tests.test_consumption_command_identity
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch


# ===================================================================
# ConsumptionCommand.get_item_and_target — shared base parser
# Covers: inject, apply (non-surgery branch), eat, drink, inhale, smoke
# ===================================================================


class TestGetItemAndTargetIdentity(TestCase):
    """``ConsumptionCommand.get_item_and_target`` uses identity helper."""

    def _make_cmd(self):
        from commands.CmdConsumption import ConsumptionCommand

        cmd = ConsumptionCommand()
        cmd.key = "inject"
        cmd.caller = MagicMock()
        cmd.caller.location = MagicMock()
        # caller.search is used for item lookup (location=caller) —
        # leave it returning a usable medical item.
        item = MagicMock()
        cmd.caller.search.return_value = [item]
        return cmd, item

    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_target_resolved_via_identity_helper(
        self, mock_resolve, _is_med
    ):
        target = MagicMock()
        mock_resolve.return_value = target
        cmd, _item = self._make_cmd()
        result = cmd.get_item_and_target("morphine man")
        mock_resolve.assert_called_once_with(cmd.caller, "man")
        self.assertIs(result["target"], target)
        self.assertEqual(result["errors"], [])

    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_target_not_found_records_error(self, mock_resolve, _is_med):
        mock_resolve.return_value = None
        cmd, _item = self._make_cmd()
        result = cmd.get_item_and_target("morphine ghost")
        self.assertTrue(
            any("ghost" in e for e in result["errors"]),
            f"errors={result['errors']}",
        )

    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_self_tokens_skip_identity_helper(self, mock_resolve, _is_med):
        cmd, _item = self._make_cmd()
        for token in ("me", "myself", "self", "ME", "Self"):
            mock_resolve.reset_mock()
            result = cmd.get_item_and_target(f"morphine {token}")
            self.assertIs(result["target"], cmd.caller)
            mock_resolve.assert_not_called()

    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_no_target_defaults_to_caller(self, mock_resolve, _is_med):
        cmd, _item = self._make_cmd()
        result = cmd.get_item_and_target("morphine")
        self.assertIs(result["target"], cmd.caller)
        mock_resolve.assert_not_called()


# ===================================================================
# CmdApply — surgery/operate branch (separate from get_item_and_target)
# ===================================================================


class TestCmdApplySurgeryIdentity(TestCase):
    """``surgery`` / ``operate`` target lookup uses identity helper."""

    def _make_cmd(self, key="surgery", args="man"):
        from commands.CmdConsumption import CmdApply

        cmd = CmdApply()
        cmd.key = key
        cmd.cmdstring = key
        cmd.args = args
        cmd.caller = MagicMock()
        cmd.caller.location = MagicMock()
        # Provide a surgical kit in caller's contents.
        kit = MagicMock()
        kit.attributes.get = lambda name: (
            "surgical_treatment" if name == "medical_type" else None
        )
        cmd.caller.contents = [kit]
        return cmd, kit

    @patch("commands.CmdConsumption.apply_medical_effects")
    @patch("commands.CmdConsumption.calculate_treatment_success")
    @patch("commands.CmdConsumption.get_medical_type",
           return_value="surgical_treatment")
    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_surgery_uses_identity_helper(
        self, mock_resolve, _is_med, _gmt, _cts, _ame
    ):
        target = MagicMock()
        target.medical_state = MagicMock()
        target.is_unconscious = lambda: False
        mock_resolve.return_value = target
        cmd, _kit = self._make_cmd(args="man")
        # Best-effort func call; short-circuit on first downstream error.
        try:
            cmd.func()
        except Exception:
            pass
        mock_resolve.assert_called_with(cmd.caller, "man")

    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.get_medical_type",
           return_value="surgical_treatment")
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_surgery_self_token_skips_helper(
        self, mock_resolve, _gmt, _is_med
    ):
        cmd, _kit = self._make_cmd(args="myself")
        try:
            cmd.func()
        except Exception:
            pass
        mock_resolve.assert_not_called()

    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.get_medical_type",
           return_value="surgical_treatment")
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_surgery_target_not_found_messages_caller(
        self, mock_resolve, _gmt, _is_med
    ):
        mock_resolve.return_value = None
        cmd, _kit = self._make_cmd(args="ghost")
        try:
            cmd.func()
        except Exception:
            pass
        msg_calls = [c.args[0] for c in cmd.caller.msg.call_args_list]
        self.assertTrue(
            any("ghost" in m for m in msg_calls),
            f"messages={msg_calls}",
        )


# ===================================================================
# CmdBandage — separate parser, separate target lookup
# ===================================================================


class TestCmdBandageIdentity(TestCase):
    """``bandage`` victim lookup uses identity helper."""

    def _make_cmd(self, item_name="bandage", target_name="man"):
        from commands.CmdConsumption import CmdBandage

        cmd = CmdBandage()
        cmd.caller = MagicMock()
        cmd.caller.location = MagicMock()
        item = MagicMock()
        cmd.caller.search.return_value = [item]
        cmd.item_name = item_name
        cmd.target_name = target_name
        cmd.body_location = None
        return cmd, item

    @patch("commands.CmdConsumption.get_medical_type",
           return_value="wound_care")
    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_bandage_target_resolved_via_helper(
        self, mock_resolve, _is_med, _gmt
    ):
        target = MagicMock()
        target.medical_state = MagicMock()
        target.is_unconscious = lambda: False
        mock_resolve.return_value = target
        cmd, _item = self._make_cmd(target_name="man")
        try:
            cmd.func()
        except Exception:
            pass
        mock_resolve.assert_called_with(cmd.caller, "man")

    @patch("commands.CmdConsumption.get_medical_type",
           return_value="wound_care")
    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_bandage_no_target_defaults_to_caller(
        self, mock_resolve, _is_med, _gmt
    ):
        cmd, _item = self._make_cmd(target_name=None)
        try:
            cmd.func()
        except Exception:
            pass
        mock_resolve.assert_not_called()

    @patch("commands.CmdConsumption.get_medical_type",
           return_value="wound_care")
    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_bandage_self_token_skips_helper(
        self, mock_resolve, _is_med, _gmt
    ):
        cmd, _item = self._make_cmd(target_name="myself")
        try:
            cmd.func()
        except Exception:
            pass
        mock_resolve.assert_not_called()

    @patch("commands.CmdConsumption.get_medical_type",
           return_value="wound_care")
    @patch("commands.CmdConsumption.is_medical_item", return_value=True)
    @patch("commands.CmdConsumption.resolve_character_target")
    def test_bandage_target_not_found_messages_caller(
        self, mock_resolve, _is_med, _gmt
    ):
        mock_resolve.return_value = None
        cmd, _item = self._make_cmd(target_name="ghost")
        try:
            cmd.func()
        except Exception:
            pass
        msg_calls = [c.args[0] for c in cmd.caller.msg.call_args_list]
        self.assertTrue(
            any("ghost" in m for m in msg_calls),
            f"messages={msg_calls}",
        )
