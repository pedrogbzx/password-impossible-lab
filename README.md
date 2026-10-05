# ¿Existe una contraseña IMPOSIBLE de Hackear?

**FaceLook · ANORMALIX SECURITY LAB** es una red social inventada para una demostración local. No está afiliada a ninguna red social real. Sus perfiles, publicaciones y credenciales son ficticios. No utiliza CDN, fuentes remotas, APIs externas, telemetría ni envíos externos. Una vez instaladas las dependencias, funciona sin Internet.

## 1. Inicio rápido para grabar

En este equipo el proyecto está en `D:\LAB_ANX\password-impossible-lab` y el entorno virtual ya está instalado.

```powershell
cd D:\LAB_ANX\password-impossible-lab
.\.venv\Scripts\python.exe app.py
```

Abre **http://127.0.0.1:5000/lab**. Si el servidor ya está ejecutándose, simplemente abre la URL. `Ctrl+C` detiene un servidor iniciado en tu terminal.

La instancia inicial se inició en segundo plano para dejarla abierta. Para detener exclusivamente el proceso registrado de este proyecto antes de cambiar parámetros, ejecuta en PowerShell:

```powershell
$labProcessId = [int](Get-Content .\instance\server.pid)
$labProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$labProcessId"
$labPython = Join-Path (Get-Location).Path '.venv\Scripts\python.exe'
if ($labProcess.CommandLine -like "*$labPython*app.py*") {
    Stop-Process -Id $labProcessId
}
```

Después puedes iniciarlo en primer plano con el comando anterior. `server.pid` corresponde solo a la instancia inicial; los inicios manuales posteriores se detienen desde su terminal.

En otra terminal, para precargar cinco cuentas (opcional):

```powershell
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

Muestra `demo_v1`–`demo_v5` y sus valores ficticios. V5 se genera aleatoriamente cada vez y se muestra una sola vez, sin escribir su contraseña en archivos. Copia ese valor para la toma. No redirijas la salida a un archivo si quieres evitar guardar el secreto ficticio. Las cuentas demo existentes no se sobrescriben: primero haz reset. También puedes registrar manualmente cualquier alias nuevo desde cada versión.

```powershell
.\.venv\Scripts\python.exe scripts\export_hashes.py --version v1
.\.venv\Scripts\python.exe scripts\show_database.py
.\.venv\Scripts\python.exe scripts\reset_lab.py
```

El reset solicita escribir `RESET`. El sitio ofrece la misma confirmación en `/reset`.

## 2. Arquitectura

```text
Navegador local o VM en LAN privada autorizada
    -> Waitress -> Flask -> lab/hashing.py -> SQLite (instance/lab.db)
                              SHA-256 / argon2-cffi
Kali --SSH autenticado--> tu servidor -> scripts locales -> hashes del laboratorio
```

Python 3.10+ (verificado aquí con Python 3.13), Flask, SQLite de la biblioteca estándar, argon2-cffi y Waitress. Waitress sirve la aplicación sin depurador y funciona en Windows/Linux. HTML/CSS/JS son locales; las ilustraciones y avatares son CSS y texto. No hay proceso de compilación frontend.

```text
app.py                   Rutas, sesión, CSRF y límites de red
config.py                Variables de entorno y validación
demo_config.json         Contraseñas públicas FICTICIAS para V1–V4
lab/database.py          SQLite, consultas parametrizadas y reset
lab/hashing.py           Hash, verificación, política y generador
lab/models.py            Contenido de los cinco niveles
templates/               Login, feed, panel y demostración
static/css/style.css     Diseño responsive sin recursos remotos
static/js/lab.js          Mostrar contraseña y generador Web Crypto
scripts/                 Operaciones locales de laboratorio
demo/                    Diccionarios diminutos y una regla de ejemplo
tests/                   Pruebas de comportamiento y límites
instance/lab.db          Datos creados automáticamente; fuera de Git
```

Una cuenta pertenece a una versión. El mismo alias puede tener una contraseña distinta en cada nivel. El feed es ilustrativo: sus acciones sociales no publican contenido. Las sesiones de navegador están firmadas y contienen identificadores, no contraseñas. La clave de sesión cambia al reiniciar; esto cierra las sesiones previas.

## 3. Instalación desde cero

### Windows / PowerShell

```powershell
cd D:\LAB_ANX\password-impossible-lab
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe app.py
```

No necesitas activar el entorno ni modificar ExecutionPolicy. Si prefieres activarlo, utiliza `.\.venv\Scripts\Activate.ps1` cuando tu política lo permita, y después `python`.

### Linux

Con Python 3 y el módulo venv ya disponibles:

```bash
cd password-impossible-lab
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/init_db.py
.venv/bin/python app.py
```

En Debian/Kali, si falta venv, prepara previamente `python3-venv` mediante el repositorio o medio de instalación autorizado de tu sistema. `requirements.txt` contiene solo dependencias de ejecución; `requirements-dev.txt` añade pytest. Las versiones directas están fijadas; `requirements-lock.txt` registra todas las versiones instaladas durante la verificación.

### Instalación totalmente offline

La instalación inicial con pip normalmente descarga paquetes. Para una máquina aislada, prepara previamente un directorio de wheels **para el mismo sistema operativo, arquitectura y versión de Python del destino**:

```bash
python -m pip download --only-binary=:all: -r requirements-lock.txt -d wheelhouse
```

Copia proyecto y `wheelhouse` por un medio local, crea un venv en el destino y ejecuta:

```bash
python -m pip install --no-index --find-links wheelhouse -r requirements-lock.txt
```

Usa el Python del venv. Los wheels binarios de Windows no sirven para Linux; prepara el lote Linux en un entorno equivalente. No copies `.venv` entre sistemas. El laboratorio no necesita conectividad externa durante su ejecución.

## 4. SQLite y URLs

El inicio del servidor y `scripts/init_db.py` crean el esquema si no existe. La ruta es absoluta respecto al proyecto, por lo que ejecutar un script desde otra carpeta no crea otra base por accidente.

| Ruta | Uso | Acceso |
|---|---|---|
| `/lab` | Recorrido de los cinco niveles | Local; LAN si está habilitada |
| `/v1`–`/v5` | Registro, login y feed ficticio | Local; LAN si está habilitada |
| `/database-viewer` | Herramienta administrativa SQLite | Solo loopback |
| `/reset` | Confirmación y borrado de datos | Solo loopback |
| `/plot-twist` | Captura ficticia explícita y opt-in | Solo loopback |

`users`: `id`, `username`, `password_hash`, `version`, `created_at` (UTC). No existe columna de contraseña en claro.

`captures`: tabla separada con `username`, `fictional_password`, fecha e identificador. Es la única excepción deliberada para el plot twist; permanece vacía mientras no se habilite y utilice explícitamente. Exportar hashes nunca incluye esta tabla.

## 5. Qué cambia entre V1–V5

| Versión | Almacenamiento | Ejemplo ficticio | Experimento |
|---|---|---|---|
| V1 | SHA-256 directo, sin salt | `123456` | Diccionario pequeño |
| V2 | **Exactamente igual a V1** | `Password1!` | Palabra + regla de mutación |
| V3 | **Exactamente igual a V1** | `Abcde12!` | Política conocida + máscara |
| V4 | Argon2id + salt único de 16 bytes | `123456` | El costo por candidato aumenta |
| V5 | **Igual a V4** | 20 caracteres aleatorios nuevos | Espacio de búsqueda grande |

V1–V3 calculan `hashlib.sha256(password.encode('utf-8')).hexdigest()`. No concatenan alias, pepper ni salt. La comparación de hashes usa `compare_digest`. Las contraseñas no se recortan ni normalizan silenciosamente.

V3 exige exactamente `[A-Z][a-z]{4}[0-9]{2}` seguido de un carácter de `string.punctuation` (32 símbolos ASCII, sin espacio). Esta política existe **para demostrar la información que filtran las estructuras rígidas**, no como recomendación de contraseñas. Edita `demo_config.json` antes de ejecutar `seed_demo.py` para elegir la contraseña concreta. El JSON contiene exclusivamente ejemplos ficticios públicos, no hashes ni secretos reales.

V5 exige al menos 20 caracteres en el registro, pero una comprobación de longitud no demuestra aleatoriedad ni unicidad. Usa el botón del navegador (Web Crypto con rechazo para evitar sesgo), `seed_demo.py` o:

```bash
python scripts/generate_password.py --length 20
```

El generador Python usa `secrets.choice` sobre 94 caracteres ASCII imprimibles sin espacios. Genera un nuevo valor para cada cuenta y no lo reutilices. La improbabilidad de colisión no equivale a una garantía matemática absoluta. Un texto manual repetitivo de 20 caracteres no representa el experimento del boss final.

## 6. Argon2id y configuración

El string completo PHC de argon2-cffi se guarda intacto:

```text
$argon2id$v=19$m=65536,t=3,p=4$<salt-base64>$<hash-base64>
```

| Variable | Default | Significado |
|---|---|---|
| `HOST` | `127.0.0.1` | IP explícita donde escuchar |
| `PORT` | `5000` | Puerto TCP |
| `LAB_LAN_MODE` | `false` | Autoriza IP privada y clientes LAN |
| `LAB_CAPTURE_MODE` | `false` | Captura ficticia, solo loopback |
| `ARGON_MEMORY_COST` | `65536` | Memoria total por operación, KiB (64 MiB) |
| `ARGON_TIME_COST` | `3` | Número de pasadas |
| `ARGON_PARALLELISM` | `4` | Paralelismo/lanes del algoritmo |

Salt: 16 bytes; digest: 32 bytes; tipo explícito `Type.ID`. El salt lo genera la librería. Dos registros con la misma contraseña generan hashes diferentes. El salt no es secreto: evita que cuentas iguales compartan el mismo resultado y hace más costoso reutilizar trabajo entre salts distintos.

Se validan límites de experimentación: `p` 1–16, `m` entre `8*p` y 1 048 576 KiB, `t` 1–20. Los valores bajos permitidos para comparar **no son recomendaciones seguras**. Cuatro solicitudes simultáneas pueden usar aproximadamente cuatro veces la memoria por operación, más el resto del proceso. Elige parámetros que soporte tu equipo.

PowerShell:

```powershell
$env:ARGON_MEMORY_COST='65536'
$env:ARGON_TIME_COST='3'
$env:ARGON_PARALLELISM='4'
.\.venv\Scripts\python.exe app.py
```

Bash:

```bash
ARGON_MEMORY_COST=65536 ARGON_TIME_COST=3 ARGON_PARALLELISM=4 .venv/bin/python app.py
```

Los cambios se leen al iniciar cada proceso. Los hashes anteriores conservan sus parámetros y se verifican con los valores incluidos en su string. No se rehashean automáticamente: esto permite comparar tomas. Para crear todos los hashes con nuevos parámetros, haz reset y vuelve a cargar cuentas en una terminal con la misma configuración.

Referencia de parámetros: [API de argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/api.html). Es un enlace de consulta, no una dependencia del laboratorio.

## 7. Reset y repetición de tomas

```bash
python scripts/reset_lab.py
# Escribe RESET
python scripts/seed_demo.py
```

La web ofrece `/reset`, protegido con CSRF y confirmación escrita. Borra usuarios, hashes y capturas y vacía páginas libres mediante `VACUUM`; mantiene el esquema y configuración. Los identificadores no se reutilizan, para que una cookie antigua no herede la cuenta de otra toma. El reset web además invalida las sesiones mediante rotación de clave.

No elimina `demo_config.json`, benchmarks, exportaciones, historial de terminal, respaldos ni potfiles de John/Hashcat. No promete borrado forense en SSD o snapshots. Para grabar otro intento de cracking usa un nombre nuevo de potfile/sesión, o retira conscientemente los resultados de tu toma anterior. Si una contraseña aparece recuperada instantáneamente, comprueba que no sea una recuperación del potfile.

## 8. Exportación e inspección

```bash
python scripts/export_hashes.py --version v1
python scripts/export_hashes.py --version v2 --hash-only
python scripts/export_hashes.py --version v3 --hash-only --output instance/v3.hash
python scripts/export_hashes.py --version v4 --hash-only --output instance/v4.hash
python scripts/export_hashes.py --version v5 --hash-only --output instance/v5.hash
python scripts/show_database.py
```

Default: una línea `username:hash` por usuario de esa versión. `--hash-only`: únicamente hash, sin encabezados, ANSI ni comentarios. `--output` escribe UTF-8 sin BOM; es preferible a `>` en Windows PowerShell 5, que puede generar UTF-16. No se muestran contraseñas originales ni capturas en exportaciones.

`show_database.py` muestra esquema, cuentas y número de capturas en JSON. Para demostrar explícitamente los datos ficticios en claro se necesitan ambas opciones: `LAB_CAPTURE_MODE=true` y `--include-captures`. El explorador web los muestra únicamente si el modo sigue activo y el cliente es loopback.

Con el CLI sqlite3 instalado puedes consultar:

```bash
sqlite3 instance/lab.db 'SELECT username,password_hash,version,created_at FROM users;'
```

El script Python no requiere instalar sqlite3 como programa separado.

## 9. Acceso desde Kali por SSH

La aplicación **no instala ni explota SSH**. Usa un servidor SSH ya configurado en tu propia máquina, con una cuenta tuya autorizada y conectividad privada. Para este objetivo no necesitas habilitar el sitio en LAN: SSH y HTTP son servicios separados.

Con servidor Linux (sustituye usuario, IP y ruta por los tuyos):

```bash
ssh usuario_lab@192.168.56.10
cd /ruta/password-impossible-lab
.venv/bin/python scripts/export_hashes.py --version v1 --hash-only
.venv/bin/python scripts/show_database.py
exit
```

Para exportar directamente a un archivo de Kali, ejecuta **en Kali**:

```bash
ssh usuario_lab@192.168.56.10 'cd /ruta/password-impossible-lab && .venv/bin/python scripts/export_hashes.py --version v1 --hash-only' > v1.hash
```

Si el servidor es Windows, habilita previamente el componente oficial OpenSSH Server mediante la administración de Windows y configura una cuenta local de laboratorio. No se ha activado automáticamente ningún servicio SSH ni regla de firewall en este proyecto. Inicia sesión con tu cuenta; según el shell de esa sesión:

```powershell
cd D:\LAB_ANX\password-impossible-lab
.\.venv\Scripts\python.exe scripts\export_hashes.py --version v4 --hash-only --output instance\v4.hash
```

Puedes copiar el archivo generado por un medio local o, desde Kali, por SFTP/SCP usando esa misma cuenta. Restringe TCP 22 al segmento privado del laboratorio mediante el firewall. No configures reenvíos de puertos, túneles ni exposición al exterior.

## 10. HTTP desde otra VM de la LAN

Usa preferentemente una red de VMs **host-only** o una LAN aislada. La IP debe estar asignada a una interfaz de tu servidor. Ejemplo: `192.168.56.10`.

PowerShell:

```powershell
$env:HOST='192.168.56.10'
$env:LAB_LAN_MODE='true'
.\.venv\Scripts\python.exe app.py
```

Bash:

```bash
HOST=192.168.56.10 LAB_LAN_MODE=true .venv/bin/python app.py
```

Desde la VM abre `http://192.168.56.10:5000/v1`. El servidor también escucha en `127.0.0.1:5000` para que en el equipo anfitrión puedas usar las herramientas administrativas. Si el firewall bloquea el puerto, autoriza TCP 5000 **solo desde la subred privada concreta**; no se modifican reglas automáticamente.

La validación rechaza `0.0.0.0`, `::`, IPs públicas y nombres DNS como HOST. Solo se permiten loopback, rangos IPv4 RFC1918 y IPv6 ULA. Las cabeceras Host están limitadas a localhost y las IPs configuradas. No se confía en X-Forwarded-For. Las herramientas administrativas siguen bloqueadas para clientes LAN, aunque intenten falsificar esa cabecera. No pongas un proxy delante: podría ocultar la dirección real. La validación de la app no controla NAT ni las configuraciones del router; mantén tu red aislada y sin port forwarding.

El sitio usa HTTP local. No lo conviertas en un servicio de producción ni introduzcas credenciales reales. No incluye funciones de despliegue público, túneles, campañas, persistencia del sistema ni envío de credenciales. Para volver al modo local:

```powershell
$env:HOST='127.0.0.1'
$env:LAB_LAN_MODE='false'
# Reinicia el servidor
```

## 11. Benchmarks reales

```bash
python scripts/benchmark_hashes.py --seconds 2 --argon-samples 5 --output instance/benchmark.json
```

Mide hashes SHA-256 repetidos y verificaciones Argon2id con un hash real. Registra plataforma, Python, timestamp UTC, parámetros, número de operaciones, tiempo, operaciones/s y mediana/mínimo/máximo de latencia Argon2. Hace calentamiento Argon2 antes de medir. No crea usuarios ni modifica sus hashes.

**Es un microbenchmark CPU en Python**: SHA-256 usa un bucle secuencial con su overhead; Argon2 verifica secuencialmente usando el paralelismo configurado. No incluye diccionarios, transferencias, múltiples GPUs ni todas las optimizaciones de Hashcat/John. No es una predicción universal de cracking ni una comparación aislada de algoritmos. Repite las mediciones en tu hardware, anota parámetros y carga del equipo, y usa tasas medidas de la herramienta concreta cuando hables de ella. No se inventan benchmarks.

## 12. Calculador de espacio de búsqueda

```bash
python scripts/keyspace_calculator.py --alphabet 94 --length 20 --rate 1000
```

`1000` es una **hipótesis de ejemplo**, no una tasa prometida. Sustitúyela por tu medición. Acepta notación científica (`--rate 1e6`). Calcula exactamente `N^L`, máximo aproximado `N^L / R` y promedio aproximado `N^L / (2R)`, con números agrupados y notación científica.

El modelo supone generación independiente y uniforme, espacio correcto, tasa constante y búsqueda sin repetir candidatos. El valor esperado discreto sería `(N^L+1)/(2R)`; usamos la mitad como aproximación solicitada. Las palabras humanas, patrones y reutilización invalidan las hipótesis de aleatoriedad. Ni el calculador ni una búsqueda que agota un diccionario demuestran que una contraseña sea imposible de recuperar por cualquier vía.

## 13. Cracking exclusivo de los hashes de este laboratorio

Ejecuta estos ejemplos **en Kali**, desde una copia local del proyecto y con archivos exportados de TU instancia. No apuntan a ningún login ni IP; son pruebas offline. Hashcat y John no son dependencias del servidor y deben estar preparados en Kali previamente. Verifica tu build:

```bash
hashcat --version
hashcat --help
john --list=formats
```

SHA-256 crudo usa modo Hashcat `1400`; Argon2 usa `34000` en versiones que lo incluyen. La compatibilidad depende de versión y backend. John debe ser una build Jumbo que incluya `raw-sha256` y `argon2`. Consulta localmente `--help`/`--list=formats`. Referencia: [tabla oficial de Hashcat](https://hashcat.net/wiki/doku.php?id=hashcat). Estos ejemplos no fueron ejecutados contra una GPU/Kali por el instalador; los tests sí verifican el formato exportado.

### V1: diccionario pequeño

Exporta `v1.hash` con `--hash-only`, tras cargar `demo_v1`:

```bash
hashcat -m 1400 -a 0 v1.hash demo/simple.txt --potfile-path toma01-v1.pot
# Alternativa John Jumbo:
john --format=raw-sha256 --wordlist=demo/simple.txt --pot=toma01-v1-john.pot v1.hash
```

### V2: palabra + regla

La palabra `password` está en `demo/words.txt`. `demo/lab.rule` contiene `c$1$!`: capitalizar y añadir `1!`.

```bash
hashcat -m 1400 -a 0 v2.hash demo/words.txt --potfile-path toma01-v2.pot
hashcat -m 1400 -a 0 v2.hash demo/words.txt -r demo/lab.rule --potfile-path toma01-v2.pot
```

Primero se agota ese diccionario pequeño; después la regla genera `Password1!`. Esto demuestra un patrón concreto; otros diccionarios pueden contener ya la contraseña.

### V3: política conocida y máscara

Edita `demo_config.json` y precarga la cuenta. La máscara general acorde a la política es:

```bash
hashcat -m 1400 -a 3 v3.hash '?u?l?l?l?l?d?d?s' --runtime 60 --potfile-path toma01-v3.pot
```

`?s` de Hashcat puede incluir espacio además de puntuación; por eso esta máscara puede explorar un pequeño superconjunto de la política. La política exacta permite `26^5 * 10^2 * 32 = 38,020,403,200` candidatos. Saber la estructura no garantiza terminar en segundos. `--runtime 60` limita la duración, no promete encontrarla.

Para ensayar con el ejemplo configurado `Abcde12!`, una máscara acotada es:

```bash
hashcat -m 1400 -a 3 v3.hash 'Abcde?d?d!' --potfile-path toma01-v3-ensayo.pot
```

Solo prueba 100 candidatos y **presupone conocer además el prefijo y el símbolo**. No presentes ese resultado como si solo conocieras la política: es un ensayo acelerado. Para la toma real usa la máscara y restricciones que hayas declarado explícitamente al público.

Si dispones localmente de RockYou u otro diccionario, puedes mostrar primero una prueba contra él y reglas genéricas. **No garantizamos que fallen**: depende de la contraseña, de ese archivo y de las reglas. Ensaya antes con un potfile nuevo. Una salida `Exhausted` solo significa que no estaba entre los candidatos probados; un corte por tiempo no significa haberlos agotado. No descargamos RockYou ni listas de credenciales filtradas.

### V4: contraseña mala, almacenamiento mejor

```bash
hashcat -m 34000 -a 0 v4.hash demo/simple.txt --potfile-path toma01-v4.pot
# Alternativa si tu John Jumbo incluye Argon2:
john --format=argon2 --wordlist=demo/simple.txt --pot=toma01-v4-john.pot v4.hash
```

Usa los strings PHC completos, sin cortarlos ni quitar `$`. Si tu Hashcat no incluye el modo 34000, usa una build compatible preparada para el laboratorio o John con Argon2. No conviertas el hash a SHA-256 para simularlo. Una contraseña común continúa entre pocos candidatos, aunque cada verificación sea costosa.

### V5: mismo Argon2id, contraseña nueva y aleatoria

```bash
hashcat -m 34000 -a 0 v5.hash demo/simple.txt --potfile-path toma01-v5.pot
hashcat -m 34000 -a 0 v5.hash demo/words.txt -r demo/lab.rule --potfile-path toma01-v5.pot
hashcat -m 34000 -a 3 v5.hash '?d?d?d?d' --runtime 30 --potfile-path toma01-v5-mask.pot
```

Las listas incluidas no generan la contraseña aleatoria de 20 caracteres. La máscara de cuatro dígitos explora un espacio incorrecto: preséntala como ejemplo de candidatos que no cubren el objetivo, **no como una búsqueda exhaustiva del espacio de 20 caracteres**. No hace falta lanzar una búsqueda inmensa: muestra `94^20` en el calculador con la tasa y los supuestos declarados. Los resultados de búsquedas limitadas no constituyen una prueba absoluta de seguridad.

Los comandos asumen exportaciones `--hash-only`. Para archivos `usuario:hash`, añade `--username` en Hashcat. No mezcles diferentes algoritmos en un mismo archivo. Mantén rutas sin espacios en estos ejemplos o añade el quoting adecuado de tu shell; los ejemplos de máscaras están escritos para Bash.

## 14. Plot twist explícito

Desactivado por defecto. Solo se acepta desde loopback, incluso con LAN habilitada. El banner permanente dice **LOCAL SECURITY LAB — TEST CREDENTIALS ONLY** y el formulario exige confirmar que los datos son ficticios.

Detén el servidor y vuelve a iniciarlo:

```powershell
$env:LAB_CAPTURE_MODE='true'
.\.venv\Scripts\python.exe app.py
```

Linux:

```bash
LAB_CAPTURE_MODE=true .venv/bin/python app.py
```

Abre `/plot-twist` **en el servidor local**, introduce exclusivamente datos generados para la toma y después abre `/database-viewer`. La captura se almacena en claro en `captures`; no verifica que coincida con una cuenta y no modifica la tabla `users`. No existe envío externo. La demostración no clona marcas ni intenta ocultar su finalidad.

Para desactivarlo, establece `LAB_CAPTURE_MODE=false` y reinicia. Luego usa `/reset` o `scripts/reset_lab.py` para borrar capturas anteriores; apagar el modo por sí solo no las borra.

## 15. Tests y comprobación de una toma

```bash
python -m pytest -q
```

Las pruebas usan SQLite temporal y Argon2 de bajo costo exclusivamente para hacer rápida la suite; no alteran la configuración ni los datos de grabación. Comprueban esquemas débiles, política, Argon2id y salts, registro/login/logout, exportación, reset, ausencia de captura por defecto, captura opt-in, CSRF, Host, separación administrativa y denegación de clientes externos. El benchmark utiliza los parámetros reales configurados.

Secuencia sugerida:

1. Reset y carga demo; guarda temporalmente el valor ficticio V5 para la toma.
2. Enseña V1/V2 y sus hashes idénticos en esquema.
3. Muestra la política V3 y declara qué conoce la máscara elegida.
4. Compara V4 con una contraseña mala y mide el costo real.
5. Muestra V5 generado al azar y el calculador con sus supuestos.
6. Habilita conscientemente el plot twist, usa únicamente datos ficticios y muestra la tabla separada.
7. Desactiva captura y resetea antes de la siguiente toma.

## 16. Troubleshooting

| Síntoma | Comprobación |
|---|---|
| `ModuleNotFoundError` | Usa el Python de `.venv` e instala requirements en ese mismo intérprete. |
| No se puede activar el venv en PowerShell | Ejecuta `.\.venv\Scripts\python.exe` directamente; no hace falta cambiar ExecutionPolicy. |
| Puerto ocupado / WinError 10048 | Ya hay un servidor. Abre la URL existente, detén su terminal o usa `PORT=5001`. |
| HOST rechazado | Debe ser IP explícita loopback o privada; evita comodines. LAN requiere flag true. |
| No puede asignar la dirección | Esa IP no pertenece a una interfaz de este servidor. Revisa su configuración de red. |
| Otra VM no conecta | Revisa IP, modo LAN, segmento host-only, firewall y que el servidor siga activo. |
| 403 en administración desde Kali | Es intencional: usa los scripts por SSH o el navegador local del servidor. |
| 400 Host inválido | Accede por `127.0.0.1`, `localhost` o la IP configurada, sin DNS/proxy personalizado. |
| 400 CSRF tras reiniciar/reset | Recarga el formulario. La sesión anterior puede haber quedado invalidada. |
| Base vacía | Registra una cuenta por versión o ejecuta seed_demo; confirma la ruta mostrada por init_db. |
| Alias ya existente | Es único dentro de cada versión. Inicia sesión, cambia el alias o resetea. |
| V3 rechaza la contraseña | Usa exactamente el patrón ASCII, sin espacios, saltos de línea ni letras acentuadas. |
| V5 manual no representa aleatoriedad | Usa el generador y no reutilices el valor. |
| Argon2 lento o sin memoria | Baja la concurrencia y mide parámetros adecuados; documenta cualquier reducción para la demo. |
| Captura desactivada pese a cambiar variable | Reinicia el servidor en la terminal donde cambiaste esa variable. |
| Hashcat `Token length exception` | Revisa modo, formato íntegro, UTF-8, salt/parámetros y `--username` si hay alias. |
| Hashcat ya lo muestra recuperado | Potfile de una toma anterior: usa uno nuevo. |
| Hashcat no tiene 34000 / John sin argon2 | La build instalada no soporta ese formato; prepara una compatible, no alteres el hash. |
| SSH no conecta | SSH es independiente: verifica servicio, cuenta, TCP 22 y red privada del servidor. |
| `database is locked` | Cierra editores/transacciones SQLite largas y vuelve a intentar. No copies la base durante escrituras; exporta hashes por el script. |

No se promete una contraseña imposible de atacar. El laboratorio muestra, por separado, predictibilidad, espacio de búsqueda, costo de verificación y el riesgo de entregar voluntariamente un secreto al lugar equivocado.
