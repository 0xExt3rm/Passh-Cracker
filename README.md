# Passh-Cracker
> **Project 1, Step ∞** — *Just training :]*

`Dictionary-based hash & zip cracker` (with salt support)

## Usage:
    python3 cracker.py hash <hash_file> <wordlist_file> [-a ALGO] [--salt-position {prepend,append}]
    python3 cracker.py zip <archive.zip> <wordlist_file>

# Examples

## 1. Standard Hash Cracking :

    python3 cracker.py hash hashes.txt wordlist.txt

## 2. Salted Hash Cracking :

If your target hash file contains a salted hash formatted like this:

`alice:a8500520a449db840d89b79e69e6566c:salt`

Run the script specifying the salt position:

    python3 cracker.py hash salted_hash.txt wordlist.txt --salt-position append

## 3. Multi Hash Cracking :

If your hash file looks like this (salted and standard hashes together):

 `alice:a8500520a449db840d89b79e69e6566c:salt
 bob:1c8bfe8f801d79745c4631d09fff36c82aa37fc4cce4fc946683d7b336b63032`

Run the script without any extra configuration. It will dynamically parse the labels, auto-detect each algorithm, extract the unique salts, and process everything in a single pass:

    python3 cracker.py hash mixed_hashes.txt wordlist.txt

`Note: If your salted hashes require the salt to be appended instead of prepended, don't forget to pass the --salt-position append flag!`

## 4. Zip Cracking :

To crack a password-protected zip archive:

    python3 cracker.py zip archive.zip wordlist.txt

`Note: only legacy ZipCrypto is supported — AES-encrypted zips are rejected with a message, not a crash. RAR support is planned.`

## Disclaimer

This tool is created strictly for educational purposes and authorized security testing. Do not use it against systems or hashes without explicit permission.
