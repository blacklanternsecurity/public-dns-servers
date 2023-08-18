import sys
import dns.resolver
import dns.exception
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

max_workers = 5
dns_timeout = 1
nameservers_txt_file = (Path(__file__).parent.parent / "nameservers.txt").resolve()
no_soa_valid_txt_file = (
    Path(__file__).parent.parent / "nameservers-no_soa_friendly.txt"
).resolve()
test_domain = "hackplanet.earth"


def errprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def do_validate_no_soa_tolerance(nameserver):
    resolver = dns.resolver.Resolver()
    resolver.timeout = dns_timeout
    resolver.lifetime = dns_timeout
    resolver.nameservers = [nameserver]

    try:
        resolver.resolve(test_domain, "NS")
        valid = True

    except (
        dns.resolver.NoNameservers,
        dns.resolver.LifetimeTimeout,
        dns.resolver.NoAnswer,
        dns.resolver.NXDOMAIN,
    ) as e:
        errprint(f"Resolver {nameserver} failed check")
        valid = False

    return nameserver, valid


def validate_no_soa_tolerance(nameservers):
    errprint(
        f"Checking {len(nameservers):,} public nameservers for tolerance of missing SOA record"
    )

    futures = []
    valid_nameservers = set()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for nameserver in nameservers:
            futures.append(executor.submit(do_validate_no_soa_tolerance, nameserver))

        for future in as_completed(futures):
            nameserver, valid = future.result()
            if valid:
                errprint(f"Resolver {nameserver} passed check")
                valid_nameservers.add(nameserver)
            else:
                errprint(f"Resolver {nameserver} failed check")

    errprint(
        f"Found {len(valid_nameservers):,}/{len(nameservers):,} nameservers that tolerate missing SOA record"
    )
    return valid_nameservers


def main():
    with open(nameservers_txt_file) as file:
        nameservers = [line.rstrip() for line in file]
    valid_resolvers = validate_no_soa_tolerance(nameservers)
    with open(no_soa_valid_txt_file, "w") as f:
        for v in valid_resolvers:
            f.write(f"{v}\n")


if __name__ == "__main__":
    main()
