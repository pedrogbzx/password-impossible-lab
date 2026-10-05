VERSIONS = {
    'v1': dict(title='El punto de partida', label='Contraseña común', algorithm='SHA-256 · sin salt', lesson='Una contraseña común puede aparecer entre los primeros candidatos de un diccionario.', tag='DICCIONARIO'),
    'v2': dict(title='Compleja. ¿O predecible?', label='Patrones humanos', algorithm='SHA-256 · sin salt', lesson='El servidor es idéntico a V1. Mayúsculas, números y símbolos no eliminan los patrones humanos.', tag='REGLAS'),
    'v3': dict(title='La estructura deja pistas', label='Política y máscara', algorithm='SHA-256 · sin salt', lesson='Una política rígida reduce el espacio que necesita explorar una máscara.', tag='MÁSCARA'),
    'v4': dict(title='Cada intento tiene un costo', label='El servidor se defiende', algorithm='Argon2id · salt único', lesson='Un salt único y un hash costoso protegen el almacenamiento. Una contraseña común sigue siendo adivinable.', tag='ARGON2ID'),
    'v5': dict(title='El boss final', label='Aleatoria, larga y única', algorithm='Argon2id · salt único', lesson='La misma defensa de V4, combinada con una contraseña larga generada al azar para este laboratorio.', tag='BOSS FINAL'),
}
