import socket
import ipaddress
from urllib.parse import urlparse


class SSRFError(Exception):
    """Raised when a URL is rejected by SSRF protection."""
    pass


def is_safe_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
        
    if ip.is_loopback:
        return False
    if ip.is_private:
        return False
    if ip.is_link_local:
        return False
    if ip.is_multicast:
        return False
    if ip.is_reserved:
        return False
    if ip.is_unspecified:
        return False
        
    # Additional specific blocklists can be added here if needed,
    # but the above properties cover standard private/internal ranges
    # including 169.254.169.254 (link-local).
        
    return True


def resolve_hostname(hostname: str) -> list[str]:
    try:
        # socket.getaddrinfo returns a list of tuples: 
        # (family, type, proto, canonname, sockaddr)
        # sockaddr is a tuple (ip, port) for IPv4 or (ip, port, flowinfo, scopeid) for IPv6
        addresses = socket.getaddrinfo(hostname, None)
        ips = set()
        for addr in addresses:
            ips.add(addr[4][0])
        return list(ips)
    except socket.gaierror:
        return []


def validate_url_safety(url: str):
    """
    Validates a URL against SSRF threats by parsing the hostname and
    resolving its IP addresses to ensure they are public/safe.
    Raises SSRFError if unsafe.
    """
    parsed = urlparse(url)
    
    if parsed.scheme not in {"http", "https"}:
        raise SSRFError(f"Invalid scheme: {parsed.scheme}")
        
    hostname = parsed.hostname
    if not hostname:
        raise SSRFError("Missing hostname")
        
    # If the hostname is literally an IP address, urlparse leaves it in hostname.
    # We can check it directly, but resolve_hostname also works for raw IPs
    # by just echoing back the IP (since getaddrinfo parses it).
    
    ips = resolve_hostname(hostname)
    if not ips:
        raise SSRFError(f"Could not resolve hostname: {hostname}")
        
    for ip in ips:
        if not is_safe_ip(ip):
            raise SSRFError(f"URL {url} resolves to unsafe IP address: {ip}")
            
    return True
