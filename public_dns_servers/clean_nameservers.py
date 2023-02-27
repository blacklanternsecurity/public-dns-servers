import dns
import sys
import json
import random
import string
import requests
import ipaddress
import dns.resolver
import dns.exception
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


nameservers_url = "https://public-dns.info/nameserver/nameservers.json"
nameservers_json_file = (Path(__file__).parent.parent / "nameservers.json").resolve()
rand_pool = string.ascii_lowercase
rand_pool_digits = rand_pool + string.digits


def errprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def rand_string(length=10, digits=True):
    pool = rand_pool
    if digits:
        pool = rand_pool_digits
    return "".join([random.choice(pool) for _ in range(int(length))])


def is_ip(d, version=None):
    if type(d) in (ipaddress.IPv4Address, ipaddress.IPv6Address):
        if version is None or version == d.version:
            return True
    try:
        ip = ipaddress.ip_address(d)
        if version is None or ip.version == version:
            return True
    except Exception:
        pass
    return False


def download(url):
    """
    Downloads file, returns full path of filename
    If download failed, returns None

    Caching supported via "cache_hrs"
    """
    filename = Path.home() / ".cache" / "public-dns-servers" / "public_dns_servers.json"
    filename.parent.mkdir(parents=True, exist_ok=True)
    try:
        with requests.get(url, stream=True) as response:
            status_code = getattr(response, "status_code", 0)
            errprint(f"Download result: HTTP {status_code}")
            if status_code != 0:
                response.raise_for_status()
                with open(filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
        return filename.resolve()
    except Exception as e:
        errprint(f"Failed to download {url}: {e}")


def get_valid_resolvers(nameservers_file, min_reliability=0.99):
    nameservers = set()
    nameservers_json = []
    try:
        nameservers_json = json.loads(open(nameservers_file).read())
    except Exception as e:
        errprint(f"Failed to load nameserver list from {nameservers_file}: {e}")
        nameservers_file.unlink()
    for entry in nameservers_json:
        try:
            ip = str(entry.get("ip", "")).strip()
        except Exception:
            continue
        try:
            reliability = float(entry.get("reliability", 0))
        except ValueError:
            continue
        if reliability >= min_reliability and is_ip(ip, version=4):
            nameservers.add(ip)
    errprint(f"Loaded {len(nameservers):,} nameservers from {nameservers_url}")
    resolver_list = verify_nameservers(nameservers)
    return resolver_list


def verify_nameservers(nameservers):
    errprint(
        f"Verifying {len(nameservers):,} public nameservers. Please be patient, this may take a while."
    )
    futures = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        for nameserver in nameservers:
            futures.append(executor.submit(verify_nameserver, nameserver))

    valid_nameservers = set()
    for future in as_completed(futures):
        nameserver, error = future.result()
        if error is None:
            errprint(f'Nameserver "{nameserver}" is valid')
            valid_nameservers.add(nameserver)
        else:
            errprint(str(error))
    if not valid_nameservers:
        errprint(
            "Unable to reach any nameservers. Please check your internet connection and ensure that DNS is not blocked outbound."
        )
    else:
        errprint(
            f"Successfully verified {len(valid_nameservers):,}/{len(nameservers):,} nameservers"
        )

    return valid_nameservers


def verify_nameserver(nameserver, timeout=3):
    """Validate a nameserver by making a sample query and a garbage query

    Args:
        nameserver (str): nameserver to verify
        timeout (int): timeout for dns query
    """
    errprint(f'Verifying nameserver "{nameserver}"')
    error = None

    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout
    resolver.nameservers = [nameserver]

    # first, make sure it can resolve a valid hostname
    try:
        a_results = [str(r) for r in list(resolver.resolve("dns.google", "A"))]
        aaaa_results = [str(r) for r in list(resolver.resolve("dns.google", "AAAA"))]
        if not ("2001:4860:4860::8888" in aaaa_results and "8.8.8.8" in a_results):
            error = f"Nameserver {nameserver} failed to resolve basic query"
    except Exception:
        error = f"Nameserver {nameserver} failed to resolve basic query within {timeout} seconds"

    # then, make sure it isn't feeding us garbage data
    randhost = (
        f"www-m.{rand_string(9, digits=False)}.{rand_string(10, digits=False)}.com"
    )
    if error is None:
        try:
            a_results = list(resolver.resolve(randhost, "A"))
            error = f"Nameserver {nameserver} returned garbage data"
        except dns.exception.DNSException:
            pass
            # Garbage query to nameserver failed successfully ;)
    if error is None:
        try:
            a_results = list(resolver.resolve(randhost, "AAAA"))
            error = f"Nameserver {nameserver} returned garbage data"
        except dns.exception.DNSException:
            pass
            # Garbage query to nameserver failed successfully ;)

    return nameserver, error


def main():
    public_dns_info_file = download(nameservers_url)
    if public_dns_info_file is not None:
        valid_resolvers = get_valid_resolvers(public_dns_info_file)
        if not valid_resolvers:
            errprint(f"No valid nameservers retrieved")
            return
        with open(nameservers_json_file, "w") as f:
            json.dump(
                {
                    "last_updated": datetime.now().isoformat(),
                    "nameservers": list(valid_resolvers),
                },
                f,
                indent=4,
            )


if __name__ == "__main__":
    main()
