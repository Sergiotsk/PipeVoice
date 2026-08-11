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

from pipevoice.audio_processor import preprocess_audio

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

audio = recording.flatten()

peak = float(np.max(np.abs(audio)))
rms = float(np.sqrt(np.mean(audio ** 2)))
nonzero = int(np.count_nonzero(audio))

print()
print("--- Audio crudo (sin procesar) ---")
print(f"Peak (máximo absoluto): {peak:.6f}")
print(f"RMS (energía promedio): {rms:.6f}")
print(f"Samples distintos de cero: {nonzero} / {len(audio)}")
print(f"Percentil 90: {np.percentile(np.abs(audio), 90):.6f}")
print(f"Percentil 99: {np.percentile(np.abs(audio), 99):.6f}")
print(f"Percentil 99.9: {np.percentile(np.abs(audio), 99.9):.6f}")

if nonzero == 0:
    print("\n>>> El buffer está TOTALMENTE en cero. El micrófono no está")
    print(">>> entregando datos — problema de dispositivo/permisos/hardware,")
    print(">>> no de PipeVoice.")
elif peak < 0.001:
    print("\n>>> Hay señal pero es casi nada — el mic está muteado, el gain")
    print(">>> muy bajo, o es el dispositivo equivocado.")
    sys.exit(0)

# --- Mismo pipeline que usa main.py de verdad, con los mismos números ---
processed = preprocess_audio(audio, trim=True, normalize=True, soft_limit=True)
if len(processed) == 0:
    print("\n--- Pipeline real de PipeVoice ---")
    print(">>> preprocess_audio() devolvió audio VACÍO (todo se recortó como silencio).")
else:
    k = max(1, len(processed) // 10)
    top_energy = np.partition(processed ** 2, -k)[-k:]
    vad_rms = float(np.sqrt(np.mean(top_energy)))
    print("\n--- Pipeline real de PipeVoice (preprocess_audio + VAD) ---")
    print(f"Peak tras preprocess: {np.max(np.abs(processed)):.6f}")
    print(f"Samples tras trim_silence: {len(processed)} / {len(audio)}")
    print(f"RMS que usa el VAD (top 10% más fuerte): {vad_rms:.6f}  (umbral default: 0.01)")
    if vad_rms < 0.01:
        print(">>> Esto es exactamente lo que descarta PipeVoice como 'silencio'.")
