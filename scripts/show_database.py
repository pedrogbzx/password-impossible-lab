import argparse
import json
from pathlib import Path

from _common import configuration
from lab.database import connect, list_users

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inspección administrativa local de SQLite.')
    parser.add_argument('--include-captures', action='store_true', help='Muestra datos ficticios en claro; requiere LAB_CAPTURE_MODE=true.')
    args = parser.parse_args()
    config = configuration()
    if not Path(config['DATABASE']).exists():
        parser.error('Inicializa SQLite primero.')
    if args.include_captures and not config['LAB_CAPTURE_MODE']:
        parser.error('--include-captures requiere LAB_CAPTURE_MODE=true')
    with connect(config['DATABASE']) as db:
        result = dict(schema=[dict(row) for row in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")],
                      users=[dict(row) for row in list_users(config['DATABASE'])],
                      capture_count=db.execute('SELECT count(*) FROM captures').fetchone()[0])
        if args.include_captures:
            result['captures'] = [dict(row) for row in db.execute('SELECT * FROM captures')]
    print(json.dumps(result, indent=2, ensure_ascii=True))
