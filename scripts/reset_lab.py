from _common import configuration
from lab.database import init_db, reset_db

if __name__ == '__main__':
    config = configuration()
    print(f"Se borrarán usuarios, hashes y capturas de: {config['DATABASE']}")
    try:
        confirmation = input('Escribe RESET para confirmar: ')
    except EOFError:
        confirmation = ''
    if confirmation != 'RESET':
        print('Cancelado. No se cambió ningún dato.')
        raise SystemExit(1)
    init_db(config['DATABASE'])
    reset_db(config['DATABASE'])
    print('Laboratorio vacío. Las exportaciones y potfiles externos no se eliminan.')
