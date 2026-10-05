import argparse
from pathlib import Path

from _common import configuration
from lab.database import list_users
from lab.models import VERSIONS


def export_lines(path, version, hashes_only=False):
    return [row['password_hash'] if hashes_only else f"{row['username']}:{row['password_hash']}"
            for row in list_users(path, version)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Exporta únicamente hashes del laboratorio; nunca capturas.')
    parser.add_argument('--version', required=True, choices=VERSIONS)
    parser.add_argument('--hash-only', action='store_true')
    parser.add_argument('--output', type=Path, help='Archivo UTF-8 (evita UTF-16 de PowerShell antiguo).')
    args = parser.parse_args()
    config = configuration()
    if not Path(config['DATABASE']).exists():
        parser.error('Inicializa SQLite primero: python scripts/init_db.py')
    output = '\n'.join(export_lines(config['DATABASE'], args.version, args.hash_only))
    if output:
        output += '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')
