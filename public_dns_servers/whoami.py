import sys
import json
import dns.resolver
import pyasn
import ipaddress

def query_dns(nameserver, domain):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.timeout = 1
    resolver.lifetime = 1
    resolver.nameservers = [nameserver]
    try:
        answers = resolver.resolve(domain, 'A')
        return str(answers[0])
    except Exception as e:
        return f"Error querying {nameserver}: {str(e)}"

def main():
    # List of DNS nameservers to query
    nameservers = open('nameservers.txt').read().splitlines()

    # Domain to query
    domain = 'whoami.akamai.net'

    asndb = pyasn.pyasn('asn.db')

    asns = {}

    try:
        for nameserver in nameservers:
            ip = query_dns(nameserver, domain)
            if not ip.startswith('Error'):
                try:
                    asn, subnet = asndb.lookup(ip)
                except Exception as e:
                    print(f"Error getting subnet for {ip}: {str(e)}")
                    continue
                print(f"Nameserver {nameserver} uses IP {ip} (subnet: {subnet}, ASN: {asn})")
                try:
                    asns[asn].add(nameserver)
                except KeyError:
                    asns[asn] = {nameserver}
            else:
                print(ip)
            print(file=sys.stderr)
    finally:
        asns = {k:sorted(v) for k,v in asns.items()}
        print(json.dumps(asns, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
