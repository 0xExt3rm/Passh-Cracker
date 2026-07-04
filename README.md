# Passh-Cracker
just training :]

dictionary-based hash cracker (with salt support) (Project 1, step ∞ )

Usage:
    python3 cracker.py <hash_file> <wordlist_file> [-a ALGO] [--salt position {prepend,append}]

if you have salted hash looks like this

 a8500520a449db840d89b79e69e6566c:salt 

you can usage like this

 python3 cracker.py salted_hash.txt wordlist.txt
