# `public-dns-servers`

The purpose of this repository is to keep an up-to-date list of the latest **KNOWN-GOOD** public DNS servers. 
`nameservers.json` is updated weekly via a CI/CD script that does the following:

- Pulls raw list of public nameservers from https://public-dns.info/
- Interrogates each DNS server to see if it is "worthy". Each DNS server MUST:
    - Respond within 3 seconds
    - Respond accurately to both A and AAAA queries
    - NOT respond to a NONEXISTENT query (helps to weed out bogus nameservers)
- Compiles the worthy nameservers into `nameservers.json`

The result is a list that's suitable to be used for any automated task, whether it be OSINT or otherwise. Enjoy!
