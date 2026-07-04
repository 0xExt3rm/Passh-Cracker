#!/usr/bin/env python3
<<<<<<< HEAD
=======
"""
cracker.py - dictionary-based hash cracker with salt support (Project 1, step ∞)
>>>>>>> f00e4c17e929b8afef136ac6e5621dd4e27a11c8

# -------------------------------------------------------------------------------------------------
# cracker.py - dictionary-based cracker: hashes and ZIP archives (Project 1, step final)          |
#                                                                                                 |
# Usage:                                                                                          |
#    python3 cracker.py hash <hash_file> <wordlist> [-a ALGO] [--salt-position {prepend,append}]  |
#    python3 cracker.py zip <archive.zip> <wordlist>                                              |
# -------------------------------------------------------------------------------------------------

import argparse
import hashlib
import sys
import time
import zipfile
import zlib
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
      SIMPLE HASH CRACKER  v0.4
========================================{Color.RESET}"""

KNOWN_LENGTHS = {
    32: "md5",
    40: "sha1",
    56: "sha224",
    64: "sha256",
    96: "sha384",
    128: "sha512",
}

AES_COMPRESS_TYPE = 99  # WinZip's marker meaning "this entry uses AES, see extra field"


# ---------------------------------------------------------------------
# Hash mode (unchanged from step 4, just moved into its own function) |
# ---------------------------------------------------------------------

def hash_string(plaintext: str, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    hasher.update(plaintext.encode("utf-8"))
    return hasher.hexdigest()


def detect_algorithm(hash_value: str) -> Optional[str]:
    return KNOWN_LENGTHS.get(len(hash_value))


def apply_salt(password: str, salt: str, position: str) -> str:
    if position == "append":
        return password + salt
    return salt + password


def load_targets(path: str, forced_algo: Optional[str]) -> dict:
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
                salt = ":".join(parts[2:])
            hash_value = hash_value.lower()
            algo = forced_algo or detect_algorithm(hash_value)
            if not algo:
                print(f"{Color.YELLOW}[!] Skipping '{label}': can't identify "
                      f"algorithm for a {len(hash_value)}-char value "
                      f"(use -a to force one){Color.RESET}", file=sys.stderr)
                continue
            by_group.setdefault((algo, salt), {})[hash_value] = label
    return by_group


def crack_hashes(by_group: dict, wordlist_path: str, salt_position: str):
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
                              f"{candidate}{Color.RESET}  [{attempts} tries, {elapsed:.1f}s]")
                        if not bucket:
                            del remaining[key]
                if attempts % 200000 == 0:
                    print(f"{Color.YELLOW}[i] {attempts} tried...{Color.RESET}", file=sys.stderr)
    except KeyboardInterrupt:
        interrupted = True
        print(f"\n{Color.YELLOW}[i] Interrupted - showing progress so far.{Color.RESET}", file=sys.stderr)
    return found, remaining, attempts, time.time() - start, interrupted


def run_hash_mode(args):
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
        found, remaining, attempts, elapsed, interrupted = crack_hashes(
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


# ----------------
# Zip mode (new) |
# ----------------

def pick_test_member(zf: zipfile.ZipFile) -> Optional[zipfile.ZipInfo]:
    """Pick the smallest non-empty file in the archive to test passwords against."""
    files = [info for info in zf.infolist() if not info.is_dir()]
    non_empty = [info for info in files if info.file_size > 0]
    candidates = non_empty or files
    return min(candidates, key=lambda info: info.file_size) if candidates else None


def try_zip_password(zf: zipfile.ZipFile, member: zipfile.ZipInfo, password: str) -> bool:
    """Return True if password successfully decrypts and reads the given member."""
    try:
        with zf.open(member, pwd=password.encode("utf-8")) as f:
            f.read()  # forces the full CRC check, not just the quick header byte
        return True
    except RuntimeError:
        return False                  # wrong password - failed zipfile's own header check
    except (zipfile.BadZipFile, zlib.error):
        return False                  # passed the header check by luck (~1 in 256 odds),
                                       # but the "decrypted" bytes are garbage


def crack_zip(archive_path: str, wordlist_path: str):
    with zipfile.ZipFile(archive_path) as zf:
        member = pick_test_member(zf)
        if member is None:
            return None, 0, 0.0, False

        attempts = 0
        start = time.time()
        interrupted = False
        try:
            with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wordlist:
                for raw_line in wordlist:
                    candidate = raw_line.strip()
                    if not candidate:
                        continue
                    attempts += 1
                    if try_zip_password(zf, member, candidate):
                        return candidate, attempts, time.time() - start, False
                    if attempts % 50000 == 0:
                        print(f"{Color.YELLOW}[i] {attempts} tried...{Color.RESET}", file=sys.stderr)
        except KeyboardInterrupt:
            interrupted = True
            print(f"\n{Color.YELLOW}[i] Interrupted.{Color.RESET}", file=sys.stderr)

        return None, attempts, time.time() - start, interrupted


def run_zip_mode(args):
    print(BANNER)
    try:
        with zipfile.ZipFile(args.archive) as zf:
            infos = zf.infolist()
            if not any(info.flag_bits & 0x1 for info in infos):
                print(f"{Color.YELLOW}[!] This archive doesn't appear to be password protected.{Color.RESET}")
                sys.exit(1)
            if any(info.compress_type == AES_COMPRESS_TYPE for info in infos):
                print(f"{Color.RED}[-] This archive uses AES encryption - Python's built-in "
                      f"zipfile can't read it. Look into the 'pyzipper' package for that.{Color.RESET}")
                sys.exit(1)
    except FileNotFoundError:
        print(f"{Color.RED}[-] Archive not found: {args.archive}{Color.RESET}")
        sys.exit(1)
    except zipfile.BadZipFile:
        print(f"{Color.RED}[-] Not a valid zip file: {args.archive}{Color.RESET}")
        sys.exit(1)

    print(f"{Color.CYAN}[i] Archive: {args.archive}{Color.RESET}")
    print(f"{Color.CYAN}[i] Wordlist: {args.wordlist}{Color.RESET}\n")

    try:
        password, attempts, elapsed, interrupted = crack_zip(args.archive, args.wordlist)
    except FileNotFoundError:
        print(f"{Color.RED}[-] Wordlist not found: {args.wordlist}{Color.RESET}")
        sys.exit(1)

    print(f"\n{Color.BOLD}--- Summary ---{Color.RESET}")
    print(f"Attempts: {attempts}   Time: {elapsed:.2f}s")
    if password:
        print(f"{Color.GREEN}[+] Password found: {password}{Color.RESET}")
    else:
        print(f"{Color.RED}[-] Password not found in wordlist.{Color.RESET}")

    if interrupted:
        sys.exit(130)
    elif not password:
        sys.exit(1)
    else:
        sys.exit(0)


# -------------
# Entry point |
# -------------

def main():
    parser = argparse.ArgumentParser(description="Simple dictionary-based cracker: hashes and zip archives.")
    subparsers = parser.add_subparsers(dest="mode", required=True, help="What to crack")

    hash_parser = subparsers.add_parser("hash", help="Crack password hash(es)")
    hash_parser.add_argument("hash_file", help="File with target hash(es), one per line")
    hash_parser.add_argument("wordlist", help="Wordlist file of candidate passwords")
    hash_parser.add_argument("-a", "--algo", choices=sorted(set(KNOWN_LENGTHS.values())),
                              help="Force a specific algorithm instead of auto-detecting")
    hash_parser.add_argument("--salt-position", choices=["prepend", "append"], default="prepend",
                              help="Where the salt goes relative to the password")

    zip_parser = subparsers.add_parser("zip", help="Crack a password-protected ZIP archive")
    zip_parser.add_argument("archive", help="Path to the .zip file")
    zip_parser.add_argument("wordlist", help="Wordlist file of candidate passwords")

    args = parser.parse_args()

    if args.mode == "hash":
        run_hash_mode(args)
    elif args.mode == "zip":
        run_zip_mode(args)


if __name__ == "__main__":
    main()
