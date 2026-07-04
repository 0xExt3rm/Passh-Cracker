#!/usr/bin/env python3
"""
cracker.py - dictionary-based hash cracker with salt support (Project 1, step ∞)

Usage:
    python3 cracker.py <hash_file> <wordlist_file> [-a ALGO] [--salt-position {prepend,append}]
"""

import argparse
import hashlib
import sys
import time
from typing import Optional


class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


BANNER = f"""{Color.CYAN}{Color.BOLD}
========================================
      SIMPLE HASH CRACKER  v0.3
========================================{Color.RESET}"""

KNOWN_LENGTHS = {
    32: "md5",
    40: "sha1",
    56: "sha224",
    64: "sha256",
    96: "sha384",
    128: "sha512",
}


def hash_string(plaintext: str, algorithm: str) -> str:
    """Return the hex digest of plaintext using the given hash algorithm."""
    hasher = hashlib.new(algorithm)
    hasher.update(plaintext.encode("utf-8"))
    return hasher.hexdigest()


def detect_algorithm(hash_value: str) -> Optional[str]:
    """Guess the algorithm from hex-digest length. None if unrecognized."""
    return KNOWN_LENGTHS.get(len(hash_value))


def apply_salt(password: str, salt: str, position: str) -> str:
    """Combine a candidate password with its salt before hashing."""
    if position == "append":
        return password + salt
    return salt + password  # "prepend" (default)


def load_targets(path: str, forced_algo: Optional[str]) -> dict:
    """
    Read target hashes from a file, one per line. Supported formats:
        <hash>                  unsalted, auto-labeled
        <label>:<hash>          unsalted
        <label>:<hash>:<salt>   salted (salt itself may contain colons)
    Blank lines and lines starting with # are skipped. <label> may NOT
    contain a colon - it's always read as the first field.
    Returns { (algorithm, salt): {hash: label} }; salt is "" when unsalted.
    """
    by_group = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(":")
            if len(parts) == 1:
                label, hash_value, salt = f"hash#{line_number}", parts[0], ""
            else:
                label = parts[0]
                hash_value = parts[1]
                salt = ":".join(parts[2:])  # "" if nothing left

            hash_value = hash_value.lower()
            algo = forced_algo or detect_algorithm(hash_value)

            if not algo:
                print(f"{Color.YELLOW}[!] Skipping '{label}': can't identify "
                      f"algorithm for a {len(hash_value)}-char value "
                      f"(use -a to force one){Color.RESET}", file=sys.stderr)
                continue

            by_group.setdefault((algo, salt), {})[hash_value] = label

    return by_group


def crack(by_group: dict, wordlist_path: str, salt_position: str):
    """
    One pass over the wordlist. For each candidate word, salt it correctly
    for every (algorithm, salt) group still needed, hash it, and check it
    against all remaining targets in that group. Stops early once nothing
    is left to find.
    Returns (found, remaining, attempts, elapsed_seconds, interrupted).
    """
    remaining = {key: dict(hashes) for key, hashes in by_group.items()}
    found = []
    attempts = 0
    start = time.time()
    interrupted = False

    try:
        with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wordlist:
            for raw_line in wordlist:
                if not remaining:
                    break

                candidate = raw_line.strip()
                if not candidate:
                    continue
                attempts += 1

                for key in list(remaining.keys()):
                    algo, salt = key
                    salted_candidate = apply_salt(candidate, salt, salt_position)
                    digest = hash_string(salted_candidate, algo)
                    bucket = remaining[key]
                    if digest in bucket:
                        label = bucket.pop(digest)
                        found.append((label, candidate, algo, salt))
                        elapsed = time.time() - start
                        salt_note = f", salt='{salt}'" if salt else ""
                        print(f"{Color.GREEN}[+] {label} ({algo}{salt_note}) -> "
                              f"{candidate}{Color.RESET}  "
                              f"[{attempts} tries, {elapsed:.1f}s]")
                        if not bucket:
                            del remaining[key]

                if attempts % 200000 == 0:
                    print(f"{Color.YELLOW}[i] {attempts} tried...{Color.RESET}",
                          file=sys.stderr)
    except KeyboardInterrupt:
        interrupted = True
        print(f"\n{Color.YELLOW}[i] Interrupted - showing progress so far.{Color.RESET}",
              file=sys.stderr)

    return found, remaining, attempts, time.time() - start, interrupted


def main():
    parser = argparse.ArgumentParser(
        description="Simple dictionary-based hash cracker with salt support."
    )
    parser.add_argument("hash_file", help="File with target hash(es), one per line")
    parser.add_argument("wordlist", help="Wordlist file of candidate passwords")
    parser.add_argument(
        "-a", "--algo",
        choices=sorted(set(KNOWN_LENGTHS.values())),
        help="Force a specific algorithm instead of auto-detecting per hash",
    )
    parser.add_argument(
        "--salt-position",
        choices=["prepend", "append"],
        default="prepend",
        help="Where the salt goes relative to the password (default: prepend)",
    )
    args = parser.parse_args()

    print(BANNER)

    try:
        by_group = load_targets(args.hash_file, args.algo)
    except FileNotFoundError:
        print(f"{Color.RED}[-] Hash file not found: {args.hash_file}{Color.RESET}")
        sys.exit(1)

    total_targets = sum(len(h) for h in by_group.values())
    if total_targets == 0:
        print(f"{Color.RED}[-] No usable hashes loaded from {args.hash_file}{Color.RESET}")
        sys.exit(1)

    algo_totals = {}
    salted_count = 0
    for (algo, salt), hashes in by_group.items():
        algo_totals[algo] = algo_totals.get(algo, 0) + len(hashes)
        if salt:
            salted_count += len(hashes)

    algo_summary = ", ".join(f"{count} {algo}" for algo, count in algo_totals.items())
    print(f"{Color.CYAN}[i] Loaded {total_targets} hash(es): {algo_summary}{Color.RESET}")
    if salted_count:
        print(f"{Color.CYAN}[i] {salted_count} salted (position: {args.salt_position}){Color.RESET}")
    print(f"{Color.CYAN}[i] Wordlist: {args.wordlist}{Color.RESET}\n")

    try:
        found, remaining, attempts, elapsed, interrupted = crack(
            by_group, args.wordlist, args.salt_position
        )
    except FileNotFoundError:
        print(f"{Color.RED}[-] Wordlist not found: {args.wordlist}{Color.RESET}")
        sys.exit(1)

    remaining_count = sum(len(h) for h in remaining.values())

    print(f"\n{Color.BOLD}--- Summary ---{Color.RESET}")
    print(f"Cracked: {len(found)}/{total_targets}")
    print(f"Attempts: {attempts}   Time: {elapsed:.2f}s")

    if remaining_count:
        print(f"{Color.RED}[-] Not cracked:{Color.RESET}")
        for (algo, salt), hashes in remaining.items():
            salt_note = f", salt='{salt}'" if salt else ""
            for h, label in hashes.items():
                print(f"    {label} ({algo}{salt_note}: {h})")

    if interrupted:
        sys.exit(130)
    elif remaining_count:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
