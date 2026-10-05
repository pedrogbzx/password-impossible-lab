"""Explicit local configuration. No dotenv or external services."""
import ipaddress
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIVATE_NETWORKS = tuple(ipaddress.ip_network(n) for n in (
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7'))


def address(value):
    try:
        ip = ipaddress.ip_address(value)
        return ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
    except ValueError:
        return None


def private_address(value):
    ip = address(value)
    return ip is not None and (ip.is_loopback or any(ip in n for n in PRIVATE_NETWORKS))


def flag(name):
    value = os.environ.get(name, 'false').lower()
    if value not in ('true', 'false'):
        raise ValueError(f'{name}: usa true o false')
    return value == 'true'


def load_config():
    return dict(
        HOST=os.environ.get('HOST', '127.0.0.1'),
        PORT=int(os.environ.get('PORT', '5000')),
        LAB_LAN_MODE=flag('LAB_LAN_MODE'),
        LAB_CAPTURE_MODE=flag('LAB_CAPTURE_MODE'),
        DATABASE=str(ROOT / 'instance' / 'lab.db'),
        SECRET_KEY=secrets.token_hex(32),
        ARGON_MEMORY_COST=int(os.environ.get('ARGON_MEMORY_COST', '65536')),
        ARGON_TIME_COST=int(os.environ.get('ARGON_TIME_COST', '3')),
        ARGON_PARALLELISM=int(os.environ.get('ARGON_PARALLELISM', '4')),
        MAX_CONTENT_LENGTH=16384,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_NAME='facelook_lab',
    )


def validate_config(config):
    ip = address(config['HOST'])
    if ip is None or not private_address(config['HOST']):
        raise ValueError('HOST debe ser una IP loopback o privada explícita; no se permite 0.0.0.0/:: ni IP pública.')
    if not ip.is_loopback and not config['LAB_LAN_MODE']:
        raise ValueError('Para enlazar una IP privada debes habilitar LAB_LAN_MODE=true.')
    if not 1 <= config['PORT'] <= 65535:
        raise ValueError('PORT fuera de rango.')
    p, m, t = (config[k] for k in ('ARGON_PARALLELISM', 'ARGON_MEMORY_COST', 'ARGON_TIME_COST'))
    if not (1 <= p <= 16 and 8*p <= m <= 1048576 and 1 <= t <= 20):
        raise ValueError('Argon2: parallelism 1–16, memory_cost 8*p–1048576 KiB, time_cost 1–20.')
