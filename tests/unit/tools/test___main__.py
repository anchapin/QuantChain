"""Tests for tools CLI main module."""






import sys
from unittest.mock import Mock, patch
import pytest
from quantchain.tools.__main__ import main
from quantchain.tools.__main__ import main

@pytest.mark.unit


class TestMain:
    """Test CLI main functionality."""



def test_main_no_arguments(self, capsys) -> None:
        """Test main with no arguments."""
        with patch.object(sys, "argv", ["script"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Usage:" in captured.out
            assert "Available commands:" in captured.out



def test_main_help_command(self, capsys) -> None:
        """Test main with help command."""
        with patch.object(sys, "argv", ["script", "help"]):
            # Help doesn't exit, it just prints
            main()

            captured = capsys.readouterr()
            assert "Usage:" in captured.out
            assert "Available commands:" in captured.out
            assert "fix-failing-ci-checks" in captured.out
            assert "Prerequisites:" in captured.out

    @patch("quantchain.tools.__main__.CIFixer")


def test_main_fix_failing_ci_success(self, mock_ci_fixer) -> None:
        """Test main with fix-failing-ci-checks command when successful."""
        mock_fixer = Mock()
        mock_fixer.run_fix_process.return_value = True
        mock_ci_fixer.return_value = mock_fixer

        with patch.object(sys, "argv", ["script", "fix-failing-ci-checks"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
            mock_fixer.run_fix_process.assert_called_once()

    @patch("quantchain.tools.__main__.CIFixer")


def test_main_fix_failing_ci_failure(self, mock_ci_fixer) -> None:
        """Test main with fix-failing-ci-checks command when it fails."""
        mock_fixer = Mock()
        mock_fixer.run_fix_process.return_value = False
        mock_ci_fixer.return_value = mock_fixer

        with patch.object(sys, "argv", ["script", "fix-failing-ci-checks"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_fixer.run_fix_process.assert_called_once()

    @patch("quantchain.tools.__main__.CIFixer")


def test_main_fix_failing_ci_exception(self, mock_ci_fixer) -> None:
        """Test main with fix-failing-ci-checks command when exception occurs."""
        mock_ci_fixer.side_effect = Exception("Test error")

        with patch.object(sys, "argv", ["script", "fix-failing-ci-checks"]):
            with pytest.raises(SystemExit) as exc_info, patch(
                "builtins.print"
            ) as mock_print:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_called_with("Error: Test error")

    @patch("quantchain.tools.__main__.CIFixer")


def test_main_fix_failing_ci_keyboard_interrupt(self, mock_ci_fixer) -> None:
        """Test main with fix-failing-ci-checks command when interrupted."""
        mock_fixer = Mock()
        mock_fixer.run_fix_process.side_effect = KeyboardInterrupt()
        mock_ci_fixer.return_value = mock_fixer

        with patch.object(sys, "argv", ["script", "fix-failing-ci-checks"]):
            with pytest.raises(SystemExit) as exc_info, patch(
                "builtins.print"
            ) as mock_print:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_called_with("\nProcess interrupted by user")



def test_main_unknown_command(self, capsys) -> None:
        """Test main with unknown command."""
        with patch.object(sys, "argv", ["script", "unknown-command"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Unknown command: unknown-command" in captured.out
            assert "Use 'help' to see available commands" in captured.out

    @patch.object(sys, "argv", ["__main__"])


def test_main_execution_with_empty_argv(self, capsys) -> None:
        """Test main when called with empty argv to cover main() call."""
        with patch.object(sys, "argv", ["__main__"]):
            with pytest.raises(SystemExit) as exc_info:

                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Usage:" in captured.out
