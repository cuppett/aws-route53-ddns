import ipaddress
import re

_LABEL_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$')

def validate_fqdn(hostname: str) -> bool:
    if not hostname:
        return False
    h = hostname.rstrip('.')
    if len(h) > 253:
        return False
    labels = h.split('.')
    if len(labels) < 2:
        return False
    return all(_LABEL_RE.match(label) for label in labels)


def validate_ipv4(ip: str) -> bool:
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False
