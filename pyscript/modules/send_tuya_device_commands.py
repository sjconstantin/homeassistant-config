import requests
import json
import yaml
import os
import time
import hmac
import hashlib
import json
from urllib.parse import urlencode, parse_qs

MAX_REFRESH_ATTEMPTS = 3
SECRETS_FILE_PATH = 'secrets.yaml'  # Update with the actual path
BASE_URL = 'https://openapi.tuyaus.com'

def load_secrets():
    fd = task.executor(os.open, SECRETS_FILE_PATH, os.O_RDONLY )
    stream = task.executor(os.read, fd, 2048)
    secrets = task.executor(yaml.safe_load, stream)
    return secrets

def save_secrets(config):
    fd = task.executor(os.open, SECRETS_FILE_PATH, os.O_WRONLY)
    stream = task.executor(os.fdopen, fd, 'w')
    result = task.executor(yaml.safe_dump, config, stream)

def encrypt_string(data, secret):
    return hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest().upper()

def get_token(secrets, refresh=False):
    method = 'GET'
    timestamp = str(int(time.time() * 1000))
    if refresh:
        signUrl = '/v1.0/token/' + secrets['tuya_refresh_token']
    else:
        signUrl = '/v1.0/token?grant_type=1'

    contentHash = hashlib.sha256(b'').hexdigest()
    stringToSign = '\n'.join([method, contentHash, '', signUrl])
    signStr = secrets['tuya_client_id'] + timestamp + stringToSign

    headers = {
        't': timestamp,
        'sign_method': 'HMAC-SHA256',
        'client_id': secrets['tuya_client_id'],
        'sign': encrypt_string(signStr, secrets['tuya_secret']),
    }

    response = task.executor(requests.get, BASE_URL + signUrl, headers=headers)
    login = response.json()
    if not login or not login['success']:
        raise Exception(f"fetch failed: {login['msg']}")
    secrets['tuya_access_token'] = login['result']['access_token']
    secrets['tuya_refresh_token'] = login['result']['refresh_token']
    return secrets

def get_signed_request(secrets, path, method, headers={}, query={}, body={}):
    t = str(int(time.time() * 1000))

    if '?' in path:
      uri, pathQuery = path.split('?')
    else:
      uri = path
      pathQuery = ''

    queryMerged = {**query, **dict(parse_qs(pathQuery))}
    sortedQuery = dict(sorted(queryMerged.items()))

    querystring = urlencode(sortedQuery)
    url = f'{uri}?{querystring}' if querystring else uri
    contentHash = hashlib.sha256(json.dumps(body).encode('utf-8')).hexdigest()
    stringToSign = '\n'.join([method, contentHash, '', url])
    signStr = secrets['tuya_client_id'] + secrets['tuya_access_token'] + t + stringToSign

    return {
        't': t,
        'path': url,
        'client_id': secrets['tuya_client_id'],
        'sign': encrypt_string(signStr, secrets['tuya_secret']),
        'sign_method': 'HMAC-SHA256',
        'access_token': secrets['tuya_access_token'],
    }

def post_commands(secrets, deviceId, commands):
    query = {}
    body = commands
    method = 'POST'
    url = f'/v1.0/devices/{deviceId}/commands'
    reqHeaders = get_signed_request(secrets, url, method, {}, query, body)

    response = task.executor(requests.post, BASE_URL + reqHeaders['path'], json=body, headers=reqHeaders)
    data = response.json()
    log.info(f'Response: {data}')
    return data

def send_commands(deviceId, commands):
    secrets = load_secrets()

    if not secrets:
        log.info('No secrets found. Exiting.')
        return

    if 'tuya_access_token' not in secrets or 'tuya_refresh_token' not in secrets:
        secrets = get_token(secrets)
        save_secrets(secrets)
      
    response = post_commands(secrets, deviceId, commands)
    if 'success' in response and response['success']:
        log.info('Request successful.')
    elif response['code'] == 1010:
        log.warning('Request failed with 1010. Refreshing tokens...')
        secrets = get_token(secrets, True)
        save_secrets(secrets)
        response = post_commands(secrets, deviceId, commands)
        if 'success' in response and response['success']:
            log.info('Request successful.')
        else:
            log.info('Request failed with an unexpected error.')
    else:
        log.info('Request failed with an unexpected error.')
