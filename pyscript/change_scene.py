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

SCENES = {
    "read": "010e0d0000000000000003e801f4",
    "night": "000e0d0000000000000000c80000",
    "working": "020e0d0000000000000003e803e8",
    "leisure": "030e0d0000000000000001f401f4",
    "soft": "04464602007803e803e800000000464602007803e8000a00000000",
    "colorful": "05464601000003e803e800000000464601007803e803e80000000046460100f003e803e800000000464601003d03e803e80000000046460100ae03e803e800000000464601011303e803e800000000",
    "dazzling": "06464601000003e803e800000000464601007803e803e80000000046460100f003e803e800000000",
    "gorgeous": "07464602000003e803e800000000464602007803e803e80000000046460200f003e803e800000000464602003d03e803e80000000046460200ae03e803e800000000464602011303e803e800000000"
}
def loadSecrets():
    fd = task.executor(os.open, SECRETS_FILE_PATH, os.O_RDONLY )
    stream = task.executor(os.read, fd, 2048)
    secrets = task.executor(yaml.safe_load, stream)
    return secrets

def saveSecrets(config):
    fd = task.executor(os.open, SECRETS_FILE_PATH, os.O_WRONLY)
    stream = task.executor(os.fdopen, fd, 'w')
    result = task.executor(yaml.safe_dump, config, stream)

def encryptStr(data, secret):
    return hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest().upper()

def getToken(secrets, refresh=False):
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
        'sign': encryptStr(signStr, secrets['tuya_secret']),
    }

    response = task.executor(requests.get, BASE_URL + signUrl, headers=headers)
    login = response.json()
    if not login or not login['success']:
        raise Exception(f"fetch failed: {login['msg']}")
    secrets['tuya_access_token'] = login['result']['access_token']
    secrets['tuya_refresh_token'] = login['result']['refresh_token']
    return secrets

def getRequestSign(secrets, path, method, headers={}, query={}, body={}):
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
        'sign': encryptStr(signStr, secrets['tuya_secret']),
        'sign_method': 'HMAC-SHA256',
        'access_token': secrets['tuya_access_token'],
    }

def changeScene(secrets, deviceId, scene):
    query = {}
    body = {'commands': [{'code': 'scene_data', 'value': SCENES[scene]},{'code': 'work_mode', 'value': 'scene'}]}
    method = 'POST'
    url = f'/v1.0/devices/{deviceId}/commands'
    reqHeaders = getRequestSign(secrets, url, method, {}, query, body)

    response = task.executor(requests.post, BASE_URL + reqHeaders['path'], json=body, headers=reqHeaders)
    data = response.json()
    log.info(f'Response: {data}')
    return data

def main(deviceId, scene):
    secrets = loadSecrets()

    if not secrets:
        log.info('No secrets found. Exiting.')
        return

    if 'tuya_access_token' not in secrets or 'tuya_refresh_token' not in secrets:
        secrets = getToken(secrets)
        saveSecrets(secrets)
      
    response = changeScene(secrets, deviceId, scene)
    if 'success' in response and response['success']:
        log.info('Request successful.')
    elif response['code'] == 1010:
        log.warning('Request failed with 1010. Refreshing tokens...')
        secrets = getToken(secrets, True)
        saveSecrets(secrets)
        response = changeScene(secrets, deviceId, scene)
        if 'success' in response and response['success']:
            log.info('Request successful.')
        else:
            log.info('Request failed with an unexpected error.')
    else:
        log.info('Request failed with an unexpected error.')

@service
def change_scene(deviceId=None, scene=None):
    log.info(f'Changing scene to {scene} for device {deviceId}')
    main(deviceId, scene)

