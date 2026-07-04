#!/usr/bin/env python3
"""
cracker.py - dictionary-based hash cracker (Project 1, step 2)

Usage:
    python3 cracker.py <hash_file> <wordlist_file> [-a ALGO]
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
      SIMPLE HASH CRACKER  v0.2
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


def load_targets(path: str, forced_algo: Optional[str]) -> dict:
    """
    Read target hashes from a file, one per line. Two supported formats:
        <hash>
        <label>:<hash>
    Blank lines and lines starting with # are skipped. Unlabeled hashes
    are auto-numbered (hash#1, hash#2, ...) by line order.
    Returns { algorithm: {hash: label} }.
    """
    by_algo = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                label, hash_value = line.rsplit(":", 1)
            else:
                label, hash_value = f"hash#{line_number}", line

            hash_value = hash_value.lower()
            algo = forced_algo or detect_algorithm(hash_value)

            if not algo:
                print(f"{Color.YELLOW}[!] Skipping '{label}': can't identify "
                      f"algorithm for a {len(hash_value)}-char value "
                      f"(use -a to force one){Color.RESET}", file=sys.stderr)
                continue

            by_algo.setdefault(algo, {})[hash_value] = label

    return by_algo


def crack(by_algo: dict, wordlist_path: str):
    """
    One pass over the wordlist. For each candidate word, hash it once per
    algorithm still needed and check it against all remaining targets of
    that algorithm. Stops early once nothing is left to find.
    Returns (found, remaining, attempts, elapsed_seconds, interrupted).
    """
    remaining = {algo: dict(hashes) for algo, hashes in by_algo.items()}
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

                for algo in list(remaining.keys()):
                    digest = hash_string(candidate, algo)
                    bucket = remaining[algo]
                    if digest in bucket:
                        label = bucket.pop(digest)
                        found.append((label, candidate, algo))
                        elapsed = time.time() - start
                        print(f"{Color.GREEN}[+] {label} ({algo}) -> "
                              f"{candidate}{Color.RESET}  "
                              f"[{attempts} tries, {elapsed:.1f}s]")
                        if not bucket:
                            del remaining[algo]

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
        description="Simple dictionary-based hash cracker."
    )
    parser.add_argument("hash_file", help="File with target hash(es), one per line")
    parser.add_argument("wordlist", help="Wordlist file of candidate passwords")
    parser.add_argument(
        "-a", "--algo",
        choices=sorted(set(KNOWN_LENGTHS.values())),
        help="Force a specific algorithm instead of auto-detecting per hash",
    )
    args = parser.parse_args()

    print(BANNER)

    try:
        by_algo = load_targets(args.hash_file, args.algo)
    except FileNotFoundError:
        print(f"{Color.RED}[-] Hash file not found: {args.hash_file}{Color.RESET}")
        sys.exit(1)

    total_targets = sum(len(h) for h in by_algo.values())
    if total_targets == 0:
        print(f"{Color.RED}[-] No usable hashes loaded from {args.hash_file}{Color.RESET}")
        sys.exit(1)

    algo_summary = ", ".join(f"{len(h)} {a}" for a, h in by_algo.items())
    print(f"{Color.CYAN}[i] Loaded {total_targets} hash(es): {algo_summary}{Color.RESET}")
    print(f"{Color.CYAN}[i] Wordlist: {args.wordlist}{Color.RESET}\n")

    try:
        found, remaining, attempts, elapsed, interrupted = crack(by_algo, args.wordlist)
    except FileNotFoundError:
        print(f"{Color.RED}[-] Wordlist not found: {args.wordlist}{Color.RESET}")
        sys.exit(1)

    remaining_count = sum(len(h) for h in remaining.values())

    print(f"\n{Color.BOLD}--- Summary ---{Color.RESET}")
    print(f"Cracked: {len(found)}/{total_targets}")
    print(f"Attempts: {attempts}   Time: {elapsed:.2f}s")

    if remaining_count:
        print(f"{Color.RED}[-] Not cracked:{Color.RESET}")
        for algo, hashes in remaining.items():
            for h, label in hashes.items():
                print(f"    {label} ({algo}: {h})")

    if interrupted:
        sys.exit(130)
    elif remaining_count:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
