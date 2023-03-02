# `public-dns-servers`

The purpose of this repository is to keep an up-to-date list of the latest **KNOWN-GOOD** public DNS servers. 
`nameservers.txt` is updated weekly via a CI/CD script that does the following:

- Pulls raw list of public nameservers from https://public-dns.info/
- Interrogates each DNS server to see if it is "worthy". Each DNS server MUST:
    - Respond within 1 second
    - Respond accurately to both A and AAAA queries
    - NOT respond to a NONEXISTENT query (helps to weed out bogus nameservers)
- Compiles the worthy nameservers into `nameservers.txt`

The result is a list that's suitable to be used for any automated task, OSINT or otherwise. Enjoy!

Used by [BBOT](https://github.com/blacklanternsecurity/bbot)'s [massdns module](https://github.com/blacklanternsecurity/bbot/blob/stable/bbot/modules/massdns.py).
