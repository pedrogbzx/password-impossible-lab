import argparse
import hashlib
import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from _common import configuration
from lab.hashing import hasher


def measure(config, seconds, samples):
    password = 'benchmark-ficticio-local'
    encoded_password = password.encode()
    ph = hasher(config)
    encoded = ph.hash(password)
    # Warm-up then timed repeated verification with the stored PHC parameters/salt.
    ph.verify(encoded, password)
    start = time.perf_counter()
    count = 0
    while time.perf_counter() - start < seconds:
        for _ in range(1000):
            hashlib.sha256(encoded_password).hexdigest()
        count += 1000
    elapsed = time.perf_counter() - start
    durations = []
    for _ in range(samples):
        start = time.perf_counter()
        ph.verify(encoded, password)
        durations.append(time.perf_counter() - start)
    return dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), platform=platform.platform(),
                processor=platform.processor(), python=platform.python_version(),
                parameters={k: config[k] for k in ('ARGON_MEMORY_COST', 'ARGON_TIME_COST', 'ARGON_PARALLELISM')},
                sha256=dict(operations=count, seconds=elapsed, attempts_per_second=count/elapsed),
                argon2id=dict(operations=samples, seconds=sum(durations), attempts_per_second=samples/sum(durations),
                              median_ms=statistics.median(durations)*1000, min_ms=min(durations)*1000, max_ms=max(durations)*1000),
                scope='Microbenchmark CPU Python secuencial, no tasa GPU ni predicción universal de cracking.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mide SHA-256 y verificación Argon2id en ESTA máquina.')
    parser.add_argument('--seconds', type=float, default=2)
    parser.add_argument('--argon-samples', type=int, default=5)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not 0 < args.seconds <= 60 or not 1 <= args.argon_samples <= 100:
        parser.error('--seconds debe estar entre 0 y 60; --argon-samples entre 1 y 100.')
    result = measure(configuration(), args.seconds, args.argon_samples)
    output = json.dumps(result, indent=2, ensure_ascii=True)
    if args.output:
        args.output.write_text(output + '\n', encoding='utf-8')
    print(output)
