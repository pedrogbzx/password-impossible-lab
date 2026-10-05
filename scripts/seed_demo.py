import argparse
import json
from pathlib import Path

from _common import ROOT, configuration
from lab.database import connect, init_db
from lab.hashing import generate_password, hash_password
from lab.models import VERSIONS


def seed(path, config, demo):
    # Compute first and insert in a single transaction. Existing accounts are never overwritten.
    passwords = {v: demo[v] for v in ('v1', 'v2', 'v3', 'v4')}
    passwords['v5'] = generate_password(demo.get('v5_length', 20))
    records = [(f'demo_{v}', hash_password(v, passwords[v], config), v) for v in VERSIONS]
    with connect(path) as db:
        if db.execute("SELECT 1 FROM users WHERE username IN ('demo_v1','demo_v2','demo_v3','demo_v4','demo_v5')").fetchone():
            raise ValueError('Ya existen cuentas demo. Resetea antes de volver a cargarlas.')
        db.executemany('INSERT INTO users(username,password_hash,version) VALUES(?,?,?)', records)
    return passwords


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Carga 5 cuentas ficticias. V5 se genera de nuevo en cada carga.')
    parser.add_argument('--config', type=Path, default=ROOT / 'demo_config.json')
    args = parser.parse_args()
    config = configuration()
    init_db(config['DATABASE'])
    try:
        passwords = seed(config['DATABASE'], config, json.loads(args.config.read_text(encoding='utf-8')))
    except (ValueError, KeyError) as exc:
        parser.error(str(exc))
    print('SOLO LAB: estos valores ficticios se muestran una vez; V5 no se guarda en archivo.')
    for version, password in passwords.items():
        print(f'demo_{version}\t{password}')
