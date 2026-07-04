# Passh-Cracker
> **Project 1, Step ∞** — *Just training :]*

`Dictionary-based hash cracker`  (with salt support) (Project 1, step ∞ )

## Usage:
    python3 cracker.py <hash_file> <wordlist_file> [-a ALGO] [--salt position {prepend,append}]

# Examples

## 1. Standard Hash Cracking :

    python3 cracker.py hashes.txt wordlist.txt

## 2. Salted Hash Cracking :

 If your target hash file contains salted hashes formatted like this:

 `a8500520a449db840d89b79e69e6566c:salt`
 
 Run the script specifying the salt position:

    python3 cracker.py salted_hash.txt wordlist.txt --salt append

## 3. Multi Hash Cracking :

 If you have hash.txt looks like this (Salted and standard hashes together

 `alice:a8500520a449db840d89b79e69e6566c:salt
bob:1c8bfe8f801d79745c4631d09fff36c82aa37fc4cce4fc946683d7b336b63032`

Run the script without any extra configurations. The script will dynamically parse the labels, auto-detect the algorithms, extract the unique salts, and process them all in a single pass:

     python3 cracker.py hash.txt wordlist.txt

`Note: If your salted hashes require the salt to be appended instead of prepended, don't forget to pass the --salt-position append flag!`

## Disclamer

This tool is created strictly for educational purposes and authorized security testing. Do not use it against systems or hashes without explicit permission.
