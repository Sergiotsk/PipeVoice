"""Diagnóstico usando la clase AudioRecorder REAL (la misma que usa main.py),
en vez de sd.rec() directo — para aislar si el bug está en el capturado por
InputStream+callback vs. una grabación simple bloqueante.

Uso:
    python examples/diagnose_recorder.py [device_index] [seconds]
"""

import sys
import time

import numpy as np

from pipevoice.recorder import AudioRecorder
from pipevoice.audio_processor import preprocess_audio

device = int(sys.argv[1]) if len(sys.argv) > 1 else None
seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

recorder = AudioRecorder(device=device)

print(f"Grabando {seconds}s con AudioRecorder (device={device if device is not None else 'default'}) — HABLÁ FUERTE ahora...")
for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

recorder.record()
time.sleep(seconds)
recorder.stop()
audio = recorder.get_audio()

print()
print("--- Audio crudo capturado por AudioRecorder (InputStream + callback) ---")
print(f"Duración reportada: {recorder.get_duration():.2f}s")
print(f"Largo del array: {len(audio)} samples ({len(audio)/16000:.2f}s)")
if len(audio) == 0:
    print(">>> get_audio() devolvió un array VACÍO. Bug de buffer/callback confirmado.")
    sys.exit(0)

peak = float(np.max(np.abs(audio)))
rms = float(np.sqrt(np.mean(audio ** 2)))
nonzero = int(np.count_nonzero(audio))
print(f"Peak: {peak:.6f}")
print(f"RMS: {rms:.6f}")
print(f"Samples distintos de cero: {nonzero} / {len(audio)}")
print(f"Percentil 99: {np.percentile(np.abs(audio), 99):.6f}")

processed = preprocess_audio(audio, trim=True, normalize=True, soft_limit=True)
if len(processed) == 0:
    print("\n>>> preprocess_audio() devolvió VACÍO.")
else:
    k = max(1, len(processed) // 10)
    top_energy = np.partition(processed ** 2, -k)[-k:]
    vad_rms = float(np.sqrt(np.mean(top_energy)))
    print(f"\nRMS que usa el VAD (top 10%): {vad_rms:.6f}  (umbral: 0.01)")
    if vad_rms < 0.01:
        print(">>> Descartado como silencio — reproducido el bug con AudioRecorder real.")
    else:
        print(">>> Pasa el VAD sin problema con AudioRecorder.")
