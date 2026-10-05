import argparse
from _common import ROOT
from lab.hashing import generate_password

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Genera una contraseña aleatoria nueva para el laboratorio; no la guarda.')
    parser.add_argument('--length', type=int, default=20)
    args = parser.parse_args()
    try:
        print(generate_password(args.length))
    except ValueError as exc:
        parser.error(str(exc))
