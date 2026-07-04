# Passh-Cracker
> **Project 1, Step ∞** — *Just training :]*

`Dictionary-based hash cracker`  (with salt support) (Project 1, step ∞ )

## Usage:
    python3 cracker.py <hash_file> <wordlist_file> [-a ALGO] [--salt position {prepend,append}]

## Examples:
    1. Standard Hash Cracking
    python3 cracker.py hashes.txt wordlist.txt

    2. Salted Hash Cracking
    If your target hash file contains salted hashes formatted like this:

     a8500520a449db840d89b79e69e6566c:salt

     Run the script specifying the salt position:

     python3 cracker.py salted_hash.txt wordlist.txt --salt append

## Disclamer

This tool is created strictly for educational purposes and authorized security testing. Do not use it against systems or hashes without explicit permission.
