#!/usr/bin/env bash
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# Ultimate Bug Scanner - Installation Script
# https://github.com/Dicklesworthstone/ultimate_bug_scanner

VERSION="4.6.0"
SCRIPT_NAME="ubs"
INSTALL_NAME="ubs"
REPO_URL="https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master"

# Global copy of original args (needed in update re-exec; must not be local)
ORIGINAL_ARGS=()

# Validate bash version (requires 4.0+)
if ((BASH_VERSINFO[0] < 4)); then
  # Attempt macOS auto-remediation via Homebrew
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    # Check for easy mode in args (before parsing)
    IS_EASY=0
    for arg in "$@"; do [[ "$arg" == "--easy-mode" ]] && IS_EASY=1; done

    SHOULD_UPGRADE=0
    if [[ "$IS_EASY" -eq 1 ]]; then
      SHOULD_UPGRADE=1
    else
      # Prompt user using /dev/tty to handle piped execution
      if [ -c /dev/tty ]; then
        echo "Error: macOS ships with Bash 3.2, but UBS requires 4.0+."
        echo -ne "Install modern Bash via Homebrew? (y/N): " > /dev/tty
        read -r REPLY < /dev/tty
        if [[ "$REPLY" =~ ^[Yy]$ ]]; then SHOULD_UPGRADE=1; fi
      fi
    fi

    if [[ "$SHOULD_UPGRADE" -eq 1 ]]; then
      echo "Upgrading Bash via Homebrew..."
      brew install bash

      NEW_BASH="$(brew --prefix)/bin/bash"
      if [[ -x "$NEW_BASH" ]]; then
        # Configure zsh alias if using zsh
        if [[ "${SHELL:-}" == *"zsh"* ]]; then
           RC_FILE="${HOME}/.zshrc"
           if [ -f "$RC_FILE" ] && ! grep -q "alias bash=" "$RC_FILE"; then
             echo "" >> "$RC_FILE"
             echo "# Added by Ultimate Bug Scanner Installer" >> "$RC_FILE"
             echo "alias bash='$NEW_BASH'" >> "$RC_FILE"
             echo "Added bash alias to $RC_FILE"
           fi
        fi

        echo "Re-launching installer with modern Bash..."
        if [[ -f "$0" ]]; then
           exec "$NEW_BASH" "$0" "$@"
        else
          # Piped execution - fetch, run, and clean up
          TEMP_SCRIPT=$(mktemp "${TMPDIR:-/tmp}/ubs-install.XXXXXX")
          curl -fsSL "${REPO_URL}/install.sh" -o "$TEMP_SCRIPT"
          "$NEW_BASH" "$TEMP_SCRIPT" "$@"
          EXIT_CODE=$?
          rm -f "$TEMP_SCRIPT"
          exit $EXIT_CODE
        fi
      else
        echo "Error: Failed to locate Homebrew bash at $NEW_BASH" >&2
      fi
    fi
  fi

  echo "Error: This installer requires Bash 4.0 or later (you have $BASH_VERSION)" >&2
  echo "Please upgrade bash or install manually." >&2
  exit 1
fi

# TTY-aware color initialization
COLOR_ENABLED=1
init_colors() {
  if [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ] || [ "${TERM:-dumb}" = "dumb" ]; then COLOR_ENABLED=0; fi
  if [ "$COLOR_ENABLED" -eq 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
  else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; RESET=''
  fi
}
init_colors

# Symbols
CHECK="${GREEN}✓${RESET}"
CROSS="${RED}✗${RESET}"
ARROW="${BLUE}→${RESET}"
WARN="${YELLOW}⚠${RESET}"