from src.checkip_handler import handler


def _event(source_ip='1.2.3.4', xff=None):
    headers = {}
    if xff:
        headers['X-Forwarded-For'] = xff
    return {
        'headers': headers,
        'requestContext': {'identity': {'sourceIp': source_ip}},
    }


def test_returns_source_ip():
    resp = handler(_event(source_ip='203.0.113.42'), None)
    assert resp['statusCode'] == 200
    assert 'Current IP Address: 203.0.113.42' in resp['body']
    assert resp['headers']['Content-Type'] == 'text/html'


def test_xff_takes_precedence():
    resp = handler(_event(source_ip='10.0.0.1', xff='203.0.113.99, 10.0.0.1'), None)
    assert 'Current IP Address: 203.0.113.99' in resp['body']


def test_xff_single_ip():
    resp = handler(_event(xff='5.6.7.8'), None)
    assert 'Current IP Address: 5.6.7.8' in resp['body']


def test_no_headers():
    event = {'requestContext': {'identity': {'sourceIp': '9.10.11.12'}}}
    resp = handler(event, None)
    assert 'Current IP Address: 9.10.11.12' in resp['body']
