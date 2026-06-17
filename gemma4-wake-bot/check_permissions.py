#!/usr/bin/env python3
# check_permissions.py
# ─── Bujji Permission Checker ────────────────────────────────────────────────
# Run this FIRST to verify all macOS permissions are set correctly.
# Usage:  python check_permissions.py
# ─────────────────────────────────────────────────────────────────────────────

import subprocess
import sys
import os

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}✅ {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠️  {msg}{RESET}")
def fail(msg): print(f"  {RED}❌ {msg}{RESET}")
def head(msg): print(f"\n{BOLD}{msg}{RESET}")


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


# ── 1. Accessibility (required for: lock screen, keystrokes, app control) ────
head("1. Accessibility Access")
rc, out, _ = run("osascript -e 'tell application \"System Events\" to name of first process'")
if rc == 0:
    ok("Accessibility access is GRANTED to Terminal / your IDE.")
else:
    fail("Accessibility access is NOT granted.")
    print(f"""
     → Go to: System Settings → Privacy & Security → Accessibility
     → Add and enable:  Terminal  (or your IDE / Python executable)
     → Without this: lock screen, app control, and keystrokes will FAIL.
""")

# ── 2. Microphone (required for: wake word + voice commands) ─────────────────
head("2. Microphone Access")
rc, out, _ = run("python3 -c \"import speech_recognition as sr; sr.Microphone()\" 2>&1")
if rc == 0:
    ok("speech_recognition imported. Microphone likely accessible.")
    print("     → If Bujji can't hear you, go to:")
    print("        System Settings → Privacy & Security → Microphone")
    print("        and enable Terminal / Python.")
else:
    warn("speech_recognition not installed or mic blocked.")
    print("     → pip install SpeechRecognition")
    print("     → System Settings → Privacy & Security → Microphone → add Terminal")

# ── 3. Screen Recording (required for: screenshots) ──────────────────────────
head("3. Screen Recording (for screenshots)")
rc, _, _ = run("screencapture -x /tmp/bujji_test_cap.png && rm -f /tmp/bujji_test_cap.png")
if rc == 0:
    ok("Screen recording / screencapture works.")
else:
    fail("screencapture failed — screen recording permission missing.")
    print("""
     → Go to: System Settings → Privacy & Security → Screen Recording
     → Add and enable:  Terminal  (or your IDE)
""")

# ── 4. osascript / AppleScript (required for: volume, dark mode, sleep, etc.) ─
head("4. Automation / AppleScript (volume, dark mode, sleep…)")
rc, out, _ = run("osascript -e 'output volume of (get volume settings)'")
if rc == 0:
    ok(f"osascript works — current volume: {out}%")
else:
    fail("osascript failed.")
    print("""
     → Go to: System Settings → Privacy & Security → Automation
     → Make sure Terminal can control System Events and Finder.
""")

# ── 5. brightness CLI ─────────────────────────────────────────────────────────
head("5. brightness CLI (for display brightness control)")
rc, _, _ = run("which brightness")
if rc == 0:
    ok("'brightness' CLI is installed.")
else:
    warn("'brightness' CLI not found — brightness control will be limited.")
    print("     → Install with:  brew install brightness")

# ── 6. blueutil CLI (for Bluetooth control) ──────────────────────────────────
head("6. blueutil CLI (for Bluetooth on/off)")
rc, _, _ = run("which blueutil")
if rc == 0:
    ok("'blueutil' CLI is installed.")
else:
    warn("'blueutil' not found — Bluetooth control will open System Preferences instead.")
    print("     → Install with:  brew install blueutil")

# ── 7. networksetup (Wi-Fi — needs sudo on some Macs) ────────────────────────
head("7. Wi-Fi Control (networksetup)")
rc, out, _ = run("networksetup -getairportpower en0 2>&1")
if rc == 0:
    ok(f"Wi-Fi control works: {out}")
else:
    warn(f"networksetup returned: {out}")
    print("     → Wi-Fi toggle may need sudo or a different interface (en1).")
    print("     → Try: sudo networksetup -setairportpower en0 on")

# ── 8. Ollama ─────────────────────────────────────────────────────────────────
head("8. Ollama (AI brain)")
rc, out, _ = run("curl -s http://localhost:11434/api/tags")
if rc == 0 and "models" in out:
    ok("Ollama is running.")
else:
    fail("Ollama not reachable.")
    print("     → Start it with:  ollama serve")
    print("     → Pull model with: ollama pull gemma4:e2b")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"{BOLD}📋 REQUIRED PERMISSIONS CHECKLIST{RESET}")
print(f"{'='*60}")
print("""
  Go to: System Settings → Privacy & Security

  ┌─────────────────────────────────┬──────────────────────────────┐
  │ Permission                      │ Needed For                   │
  ├─────────────────────────────────┼──────────────────────────────┤
  │ Accessibility → Terminal/Python │ Lock screen, app control,    │
  │                                 │ keystrokes, dark mode toggle │
  ├─────────────────────────────────┼──────────────────────────────┤
  │ Microphone → Terminal/Python    │ Voice input (wake word)      │
  ├─────────────────────────────────┼──────────────────────────────┤
  │ Screen Recording → Terminal     │ Screenshots (screencapture)  │
  ├─────────────────────────────────┼──────────────────────────────┤
  │ Automation → Terminal           │ Volume, dark mode, sleep,    │
  │   (allow System Events+Finder)  │ restart, Finder control      │
  └─────────────────────────────────┴──────────────────────────────┘

  Optional CLI tools (install once with Homebrew):
    brew install brightness   ← for display brightness control
    brew install blueutil     ← for Bluetooth on/off

  After granting permissions, RESTART Terminal and run Bujji again.
""")
