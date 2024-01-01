import json
import jwt
import jwt.algorithms
import os
import requests


algorithms = ['RS256']


def make_token_verifier(*, issuer=None, client_id=None):
    assert client_id
    if not issuer:
        issuer = get_issuer()
    p = get_provider_info(issuer)
    a = None
    for k in p['jwks']['keys']:
        if k['alg'] in algorithms:
            a = jwt.algorithms.get_default_algorithms()[k['alg']]
            break
    if not a:
        raise RuntimeError('NoApplicableKey')
    key = a.from_jwk(json.dumps(k))

    def verifier(token):
        d = jwt.decode(token, key=key, algorithms=[k['alg']], audience=[client_id])
        claims = {
            'username': d.get('preferred_username'),
            'subject': d.get('sub'),
            'roles': d.get('resource_access', {}).get(client_id, {}).get('roles', []),
        }
        if not claims['roles']:
            pass
        return claims
    return verifier


def verify_headers(h, token_verifier):
    v = h.get('Authorization', '')
    if v.startswith('Bearer '):
        return token_verifier(v[7:])
    raise Unauthenticated()


def get_provider_info(issuer):
    r = requests.get(issuer + '/.well-known/openid-configuration')
    r.raise_for_status()
    p = r.json()
    if p['issuer'] != issuer:
        raise RuntimeError('IssuerMismatch')
    r = requests.get(p['jwks_uri'])
    r.raise_for_status()
    p['jwks'] = r.json()
    return p


def get_issuer():
    issuer = os.getenv('AUTH_ISSUER')
    if issuer:
        return issuer
    config = os.getenv('AUTH_CONFIG', 'http://auth-config.auth.k8s')
    r = requests.get('%s/issuer' % config)
    r.raise_for_status()
    return r.json()['issuer']


class PermissionDenied(Exception):
    pass


class Unauthenticated(Exception):
    pass