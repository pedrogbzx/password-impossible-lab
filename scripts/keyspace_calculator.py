import argparse
from decimal import Decimal, InvalidOperation, localcontext


def calculate(alphabet, length, rate):
    if not 1 <= alphabet <= 1000000 or not 1 <= length <= 1000:
        raise ValueError('Alfabeto: 1–1000000; longitud: 1–1000.')
    rate = Decimal(str(rate))
    if not rate.is_finite() or rate <= 0:
        raise ValueError('Los intentos por segundo deben ser positivos y finitos.')
    combinations = alphabet ** length
    with localcontext() as ctx:
        ctx.prec = 40
        maximum = Decimal(combinations) / rate
        return combinations, maximum, maximum / 2


def readable_seconds(seconds):
    if seconds < 60:
        return f'{seconds:,.4g} segundos'
    if seconds < 3600:
        return f'{seconds / 60:,.4g} minutos'
    if seconds < 86400:
        return f'{seconds / 3600:,.4g} horas'
    if seconds < 31557600:
        return f'{seconds / 86400:,.4g} días'
    return f'{seconds / Decimal(31557600):,.6g} años (365.25 días/año)'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Espacio uniforme N^L y búsqueda exhaustiva a tasa constante.')
    parser.add_argument('--alphabet', required=True, type=int)
    parser.add_argument('--length', required=True, type=int)
    parser.add_argument('--rate', required=True, help='Intentos/s medidos o hipótesis explícita; admite 1e6.')
    args = parser.parse_args()
    try:
        total, maximum, average = calculate(args.alphabet, args.length, args.rate)
    except (ValueError, InvalidOperation) as exc:
        parser.error(str(exc))
    print(f'Espacio: {args.alphabet}^{args.length}')
    if total.bit_length() < 10000:
        print(f'Combinaciones: {total:,}')
    print(f'Notación científica: {Decimal(total):.6E}')
    print(f'Tasa supuesta: {args.rate} intentos/s')
    print(f'Máximo aproximado: {readable_seconds(maximum)}')
    print(f'Promedio aproximado (mitad del espacio): {readable_seconds(average)}')
    print('Modelo idealizado: generación uniforme, tasa constante y búsqueda sin repetir candidatos.')
    print('Depende del algoritmo, hardware, estrategia y generación; NO es un tiempo universal de cracking.')
