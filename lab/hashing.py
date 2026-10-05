import hashlib
import hmac
import re
import secrets
import string

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

ALPHABET = string.ascii_letters + string.digits + string.punctuation
POLICY = re.compile(r'[A-Z][a-z]{4}[0-9]{2}[' + re.escape(string.punctuation) + r']', re.ASCII)


def hasher(config):
    return PasswordHasher(time_cost=config['ARGON_TIME_COST'], memory_cost=config['ARGON_MEMORY_COST'],
                          parallelism=config['ARGON_PARALLELISM'], type=Type.ID, salt_len=16, hash_len=32)


def validate_password(version, password):
    if not 1 <= len(password) <= 256:
        raise ValueError('La contraseña debe contener entre 1 y 256 caracteres.')
    if version == 'v3' and not POLICY.fullmatch(password):
        raise ValueError('V3 exige: 1 mayúscula ASCII + 4 minúsculas ASCII + 2 dígitos + 1 símbolo ASCII (sin espacio).')
    if version == 'v5' and len(password) < 20:
        raise ValueError('V5 exige al menos 20 caracteres. Usa el generador local para obtener aleatoriedad.')


def hash_password(version, password, config):
    validate_password(version, password)
    if version in ('v1', 'v2', 'v3'):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    if version in ('v4', 'v5'):
        return hasher(config).hash(password)
    raise ValueError('Versión desconocida')


def verify_password(version, encoded, password, config):
    if version in ('v1', 'v2', 'v3'):
        return hmac.compare_digest(encoded, hashlib.sha256(password.encode('utf-8')).hexdigest())
    try:
        return hasher(config).verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def generate_password(length=20):
    if not 20 <= length <= 256:
        raise ValueError('Longitud aleatoria: entre 20 y 256.')
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))
