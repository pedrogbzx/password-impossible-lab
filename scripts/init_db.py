from _common import configuration
from lab.database import init_db

if __name__ == '__main__':
    config = configuration()
    init_db(config['DATABASE'])
    print(f"SQLite inicializado: {config['DATABASE']}")
