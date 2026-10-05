# Verificación local

Fecha: 21 de septiembre de 2026 (Lima); registro de benchmark en UTC: 22 de septiembre.

- Windows 11, Python 3.13.3, dependencias instaladas en `.venv`.
- 35 pruebas automatizadas: registro/login/logout V1–V5, hashing, salts, exportación, reset, configuración, CSRF y límites de red.
- Navegador real: panel, registro V1–V5, feed, generador Web Crypto V5 y tabla SQLite con los cinco formatos esperados. Inspección visual de interfaz de escritorio y formulario estrecho.
- Exportación CLI V1 sin encabezados y V4 a archivo UTF-8 comprobadas.
- Captura opt-in verificada con cliente Flask y base temporal. El servidor entregado permanece con captura y LAN desactivadas.
- Microbenchmark medido con los parámetros por defecto: aproximadamente 2 010 559 SHA-256/s y 23,10 verificaciones Argon2id/s; mediana Argon2id de 43,69 ms. Datos completos en `instance/benchmark.json`. Son mediciones CPU Python locales, no GPU/Hashcat.
- No se ejecutó una sesión SSH remota, una VM Linux ni Hashcat/John en este equipo. Los ejemplos y pasos están documentados; requieren tu equipo Kali y un servicio SSH previamente configurado.

Los datos de prueba del navegador se eliminaron con el reset para dejar SQLite listo para la primera toma. Los resultados de rendimiento se conservan.
