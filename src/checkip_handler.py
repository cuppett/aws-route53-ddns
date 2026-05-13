def handler(event, context):
    xff = (event.get('headers') or {}).get('X-Forwarded-For', '')
    if xff:
        client_ip = xff.split(',')[0].strip()
    else:
        client_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')

    body = (
        '<html><head><title>Current IP Check</title></head>'
        f'<body>Current IP Address: {client_ip}</body></html>'
    )
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': body,
    }
