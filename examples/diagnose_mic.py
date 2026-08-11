"""Diagnóstico crudo de captura de audio — sin VAD, sin preprocess_audio.

Graba N segundos de un dispositivo específico y muestra el máximo y el
RMS real de lo capturado, sample por sample, sin ningún filtro de por
medio. Uso:

    python examples/diagnose_mic.py [device_index] [seconds]

Ejemplo:
    python examples/diagnose_mic.py 2 5
"""

import sys
import time
from typing import cast

import numpy as np
import sounddevice as sd

device = int(sys.argv[1]) if len(sys.argv) > 1 else None
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

# sounddevice no tiene type stubs — ver docs/10-aprendizaje/07-type-checking-pyright.md
info = cast(
    dict,
    sd.query_devices(device, "input") if device is not None else sd.query_devices(kind="input"),
)
print(f"Dispositivo: {info['name']!r} (index={device if device is not None else 'default'})")
print(f"Grabando {seconds}s — HABLÁ FUERTE ahora...")

for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

recording = sd.rec(
    int(seconds * 16000),
    samplerate=16000,
    channels=1,
    dtype="float32",
    device=device,
)
sd.wait()

peak = float(np.max(np.abs(recording)))
rms = float(np.sqrt(np.mean(recording ** 2)))
nonzero = int(np.count_nonzero(recording))

print()
print(f"Peak (máximo absoluto): {peak:.6f}")
print(f"RMS (energía promedio): {rms:.6f}")
print(f"Samples distintos de cero: {nonzero} / {len(recording)}")

if nonzero == 0:
    print("\n>>> El buffer está TOTALMENTE en cero. El micrófono no está")
    print(">>> entregando datos — problema de dispositivo/permisos/hardware,")
    print(">>> no de PipeVoice.")
elif peak < 0.001:
    print("\n>>> Hay señal pero es casi nada — el mic está muteado, el gain")
    print(">>> muy bajo, o es el dispositivo equivocado.")
else:
    print("\n>>> Hay señal real. Si PipeVoice igual la ignora, el problema")
    print(">>> está en preprocess_audio() o en el cálculo de VAD, no en la captura.")
