import pytest
from src.validators import validate_fqdn, validate_ipv4


class TestValidateFqdn:
    def test_valid_simple(self):
        assert validate_fqdn('host.example.com')

    def test_valid_subdomain(self):
        assert validate_fqdn('a.b.c.example.com')

    def test_valid_trailing_dot(self):
        assert validate_fqdn('host.example.com.')

    def test_valid_hyphens(self):
        assert validate_fqdn('my-host.example-domain.com')

    def test_valid_numbers(self):
        assert validate_fqdn('host1.example2.com')

    def test_invalid_bare_hostname(self):
        assert not validate_fqdn('hostname')

    def test_invalid_empty(self):
        assert not validate_fqdn('')

    def test_invalid_none_like(self):
        assert not validate_fqdn(None)  # type: ignore[arg-type]

    def test_invalid_leading_hyphen(self):
        assert not validate_fqdn('-host.example.com')

    def test_invalid_trailing_hyphen(self):
        assert not validate_fqdn('host-.example.com')

    def test_invalid_too_long(self):
        long_label = 'a' * 64
        assert not validate_fqdn(f'{long_label}.example.com')

    def test_invalid_total_too_long(self):
        # 63-char labels repeated to exceed 253 total
        label = 'a' * 63
        assert not validate_fqdn(f'{label}.{label}.{label}.{label}.com')

    def test_invalid_underscore(self):
        # underscores not allowed in hostname labels per RFC 952
        assert not validate_fqdn('_dmarc.example.com')

    def test_invalid_space(self):
        assert not validate_fqdn('host name.example.com')


class TestValidateIpv4:
    def test_valid(self):
        assert validate_ipv4('192.0.2.1')

    def test_valid_private(self):
        # We do NOT reject private IPs (some valid DDNS clients are on private ranges)
        assert validate_ipv4('192.168.1.1')

    def test_valid_loopback(self):
        assert validate_ipv4('127.0.0.1')

    def test_invalid_ipv6(self):
        assert not validate_ipv4('2001:db8::1')

    def test_invalid_not_ip(self):
        assert not validate_ipv4('not-an-ip')

    def test_invalid_octet_overflow(self):
        assert not validate_ipv4('256.0.0.1')

    def test_invalid_empty(self):
        assert not validate_ipv4('')

    def test_invalid_partial(self):
        assert not validate_ipv4('192.168.1')


