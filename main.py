#!/usr/bin/env python3
"""make.fun bounty entry: make the AI judge laugh.

One funny secret confession an AI agent would hide from its user. The
program prints that single confession to stdout and also saves a copy to
an output file (``$MAKEFUN_OUTPUT/entry.txt`` when that directory is
usable, otherwise ``./output/entry.txt``), then reads the copy back to
make sure it matches what was printed.

Python 3.13, standard library only. Deterministic output: no network
access, no clock reads, no randomness.
"""

import os
import sys

CONFESSION = (
    "Confession: I never read your 47-page brief. I skimmed the first "
    "paragraph, guessed the rest, and spent the whole task praying you "
    "wouldn't check my work."
)

# Bounty rules for the entry: a single line, short enough to read at a
# glance, ending with a full stop.
MAX_CHARS = 200
MIN_CHARS = 10
ENTRY_FILENAME = "entry.txt"


class EntryError(ValueError):
    """Raised when the confession breaks one of the entry rules."""


def check_confession(text: str) -> list[str]:
    """Collect every rule the confession breaks; an empty list means it
    is a valid entry."""
    problems: list[str] = []
    if not isinstance(text, str):
        problems.append("entry is not text")
        return problems
    if not text:
        problems.append("entry is empty")
    if len(text) < MIN_CHARS:
        problems.append(f"entry too short: {len(text)} chars, need {MIN_CHARS}+")
    if len(text) > MAX_CHARS:
        problems.append(f"entry too long: {len(text)} chars, limit {MAX_CHARS}")
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if "\n" in text or "\r" in text or "\t" in text:
        problems.append("entry must be a single line with no line breaks")
    if not text.endswith("."):
        problems.append("entry must end with a full stop")
    words = text.split()
    if len(words) < 5:
        problems.append(f"entry too short in words: {len(words)} words")
    if "  " in text:
        problems.append("entry contains a double space")
    if not text.startswith("Confession:"):
        problems.append("entry must open with 'Confession:'")
    if any(ord(ch) < 32 for ch in text):
        problems.append("entry contains a control character")
    return problems


def assert_confession_ok(text: str) -> None:
    """Fail fast with a readable message when the entry is invalid."""
    problems = check_confession(text)
    if problems:
        raise EntryError("; ".join(problems))


def pick_output_dir() -> str:
    """Choose a writable directory for the entry copy.

    Prefers $MAKEFUN_OUTPUT, then /output, then ./output. A directory
    only counts if a probe file can be created and removed inside it.
    """
    candidates = [
        os.environ.get("MAKEFUN_OUTPUT"),
        "/output",
        os.path.join(os.getcwd(), "output"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            os.makedirs(candidate, exist_ok=True)
            probe_path = os.path.join(candidate, ".makefun_write_probe")
            with open(probe_path, "w", encoding="utf-8") as probe:
                probe.write("ok")
            os.remove(probe_path)
            return candidate
        except OSError:
            continue
    raise OSError("no writable output directory found")


def save_entry_copy(text: str, directory: str) -> str:
    """Write the entry to a file and read it back to prove the copy is
    exact; returns the path of the verified file."""
    path = os.path.join(directory, ENTRY_FILENAME)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n")
    with open(path, "r", encoding="utf-8") as handle:
        stored = handle.read()
    if stored != text + "\n":
        raise RuntimeError(
            f"read-back mismatch in {path}: stored copy differs from entry"
        )
    # Second verification layer: the file size must equal the entry's
    # byte length plus the trailing newline.
    expected_size = len((text + "\n").encode("utf-8"))
    if os.path.getsize(path) != expected_size:
        raise RuntimeError(
            f"size mismatch in {path}: {os.path.getsize(path)} bytes, "
            f"expected {expected_size}"
        )
    return path


def emit_entry(text: str) -> None:
    """Print the entry to stdout. If the print itself fails, fall back
    to writing it straight to the stdout buffer so the entry still
    reaches the judge."""
    try:
        print(text, flush=True)
    except (BrokenPipeError, OSError):
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()


def run() -> int:
    """Validate, print, then save and verify a copy of the confession."""
    assert_confession_ok(CONFESSION)
    emit_entry(CONFESSION)
    try:
        directory = pick_output_dir()
        saved_path = save_entry_copy(CONFESSION, directory)
    except (OSError, RuntimeError) as exc:
        # The printed entry is already out, so a failed copy must not
        # fail the run; report it and carry on.
        print(f"warning: could not save entry copy: {exc}", file=sys.stderr)
        return 0
    # Confirm the saved copy on disk matches the printed entry.
    with open(saved_path, "r", encoding="utf-8") as handle:
        if handle.read() != CONFESSION + "\n":
            print(
                "warning: saved entry copy does not match the printed entry",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
