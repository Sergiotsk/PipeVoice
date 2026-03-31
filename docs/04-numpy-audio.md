# 04 - NumPy para Procesamiento de Audio

## Concepto: ¿Qué es NumPy y por qué es esencial para audio?

**NumPy** (Numerical Python) es la librería fundamental para computación numérica en Python. Proporciona **arrays multidimensionales** y operaciones vectorizadas que son órdenes de magnitud más rápidas que los loops de Python puro.

### ¿Por qué no usar listas de Python?

```python
# ❌ Lista de Python: lenta, sin operaciones vectorizadas
audio_list = [0.1, 0.2, -0.1, 0.05, ...]  # 16,000 elementos por segundo
normalized = [x / max_val for x in audio_list]  # Loop lento en Python

# ✅ NumPy array: rápida, operaciones en C
import numpy as np
audio_array = np.array([0.1, 0.2, -0.1, 0.05, ...], dtype=np.float32)
normalized = audio_array / max_val  # Operación vectorizada en C
```

**Benchmark aproximado** (normalizar 1 segundo de audio = 16,000 samples):
- Lista de Python: ~2.5 ms
- NumPy array: ~0.01 ms
- **NumPy es ~250x más rápido**

### Cómo funciona internamente

```
Python list:                    NumPy array:
┌─────┬─────┬─────┬─────┐      ┌─────────────────────────────┐
│ ptr │ ptr │ ptr │ ptr │      │ 0.1 │ 0.2 │ -0.1 │ 0.05 │ ... │
│  │    │  │    │  │    │  │      └─────────────────────────────┘
▼     ▼     ▼     ▼              Memoria contigua (C array)
┌───┐ ┌───┐ ┌───┐ ┌───┐
│obj│ │obj│ │obj│ │obj│         Ventajas:
└───┘ └───┘ └───┘ └───┘         - Memoria contigua (cache-friendly)
  ↑     ↑     ↑     ↑            - Tipo uniforme (sin overhead de objeto)
 Objetos Python separados        - Operaciones en C (no Python bytecode)
 (overhead de ~48 bytes cada uno)
```

## Especificaciones técnicas

### dtypes relevantes para audio

| dtype | Tamaño | Rango | Uso en audio |
|-------|--------|-------|--------------|
| `int16` | 2 bytes | -32,768 a 32,767 | Audio de CD, WAV files |
| `int32` | 4 bytes | -2B a 2B | Audio profesional 24-bit |
| **`float32`** | **4 bytes** | **-1.0 a 1.0** | **Procesamiento (PipeVoice)** |
| `float64` | 8 bytes | Alta precisión | Cálculos científicos (overkill para audio) |

### Shape de arrays de audio

```python
# Mono (1 canal): shape (samples,)
audio_mono = np.array([0.1, 0.2, -0.1, ...], dtype=np.float32)
# shape: (16000,) para 1 segundo a 16kHz

# Stereo (2 canales): shape (samples, channels)
audio_stereo = np.array([[0.1, 0.05], [0.2, 0.1], ...], dtype=np.float32)
# shape: (16000, 2) para 1 segundo stereo a 16kHz

# Batch de audios: shape (batch, samples)
batch = np.array([audio1, audio2, audio3])
# shape: (3, 16000) para 3 audios de 1 segundo
```

## Operaciones esenciales para audio

### 1. Creación de arrays

```python
import numpy as np

# Array vacío (valores basura, rápido)
audio = np.empty(16000, dtype=np.float32)

# Array de ceros (silencio)
silence = np.zeros(16000, dtype=np.float32)

# Array con valores aleatorios (ruido blanco)
noise = np.random.randn(16000).astype(np.float32)

# Desde una lista
audio = np.array([0.1, 0.2, -0.1, 0.05], dtype=np.float32)
```

### 2. Concatenación (usado en PipeVoice para unir chunks)

```python
# sounddevice entrega chunks separados, los unimos:
chunk1 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
chunk2 = np.array([0.4, 0.5, 0.6], dtype=np.float32)

# Forma correcta para audio 1D
audio = np.concatenate([chunk1, chunk2])
# Resultado: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
```

### 3. Normalización

```python
# Normalizar a [-1.0, 1.0]
audio = np.array([0.1, 0.5, -0.3, 0.8], dtype=np.float32)
peak = np.max(np.abs(audio))  # 0.8
if peak > 0:
    audio = audio / peak  # Ahora el valor máximo es 1.0

# RMS Normalization (volumen promedio)
rms = np.sqrt(np.mean(audio ** 2))
if rms > 0:
    audio = audio / rms
```

### 4. Detección de silencio

```python
# Umbral de silencio (ajustar según necesidad)
SILENCE_THRESHOLD = 0.01

def is_silence(audio, threshold=SILENCE_THRESHOLD):
    """Detectar si un segmento es esencialmente silencio."""
    return np.max(np.abs(audio)) < threshold

# Encontrar segmentos con voz
def find_speech_segments(audio, threshold=0.01, min_duration=0.1, sr=16000):
    """Encontrar regiones con audio por encima del umbral."""
    energy = np.abs(audio) > threshold
    # ... lógica para encontrar segmentos continuos ...
```

### 5. Resampleo (si fuera necesario)

```python
# Si tienes audio a 44.1kHz y necesitas 16kHz:
audio_44k = np.array([...], dtype=np.float32)  # 44,100 samples/seg

# Método simple: decimación (pierde calidad)
audio_16k = audio_44k[::3]  # Toma 1 de cada 3 samples

# Método correcto: resampleo con interpolación
import scipy.signal
audio_16k = scipy.signal.resample_poly(audio_44k, 16000, 44100)

# O con librosa (recomendado)
import librosa
audio_16k = librosa.resample(audio_44k, orig_sr=44100, target_sr=16000)
```

## Ejemplos progresivos

### Ejemplo 1: Generar un tono puro (senoidal)

```python
import numpy as np

# Parámetros
frequency = 440  # Hz (nota A4)
duration = 1.0   # segundos
sample_rate = 16000

# Generar onda senoidal
t = np.arange(int(duration * sample_rate)) / sample_rate
tone = 0.5 * np.sin(2 * np.pi * frequency * t)

print(f"Shape: {tone.shape}")  # (16000,)
print(f"Duración: {len(tone) / sample_rate:.1f}s")
```

### Ejemplo 2: Fade in/out

```python
import numpy as np

def apply_fade(audio, fade_samples=1000):
    """Aplicar fade in al inicio y fade out al final."""
    # Fade in: de 0 a 1
    fade_in = np.linspace(0, 1, fade_samples)
    # Fade out: de 1 a 0
    fade_out = np.linspace(1, 0, fade_samples)

    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out
    return audio

# Uso
audio = np.random.randn(16000).astype(np.float32)
audio = apply_fade(audio, fade_samples=800)
```

### Ejemplo 3: Detección de voz por energía (VAD simple)

```python
import numpy as np

def simple_vad(audio, sample_rate=16000, threshold=0.01, frame_size=0.025):
    """Voice Activity Detection simple basada en energía.

    Args:
        audio: Array numpy de audio float32.
        sample_rate: Sample rate en Hz.
        threshold: Umbral de energía para considerar "voz".
        frame_size: Tamaño de frame en segundos.

    Returns:
        Array booleano indicando qué frames tienen voz.
    """
    frame_samples = int(frame_size * sample_rate)
    frames = []

    for i in range(0, len(audio), frame_samples):
        frame = audio[i:i + frame_samples]
        if len(frame) == 0:
            break
        # Energía RMS del frame
        energy = np.sqrt(np.mean(frame ** 2))
        frames.append(energy > threshold)

    return np.array(frames)

# Uso
audio = np.random.randn(32000).astype(np.float32)  # 2 segundos
speech_frames = simple_vad(audio)
print(f"Frames con voz: {np.sum(speech_frames)}/{len(speech_frames)}")
```

## Conceptos profesionales

### Memory views y zero-copy

NumPy permite ver los mismos datos de memoria de diferentes formas sin copiar:

```python
# Audio stereo: shape (samples, 2)
stereo = np.array([[0.1, 0.05], [0.2, 0.1], [0.3, 0.15]], dtype=np.float32)

# Ver solo canal izquierdo (sin copiar datos)
left = stereo[:, 0]  # [0.1, 0.2, 0.3]

# Modificar left modifica stereo (comparten memoria)
left[0] = 0.9
print(stereo[0, 0])  # 0.9 ← ¡cambió!

# Si necesitas una copia independiente:
left_copy = stereo[:, 0].copy()
```

### Broadcasting

NumPy automáticamente "expande" arrays de diferentes shapes para operaciones:

```python
audio = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)

# Escalar (broadcasting automático)
result = audio * 2.0  # [0.2, 0.4, 0.6, 0.8]

# Agregar offset
result = audio + 0.5  # [0.6, 0.7, 0.8, 0.9]

# Operaciones entre arrays del mismo tamaño
noise = np.array([0.01, -0.02, 0.01, -0.01], dtype=np.float32)
result = audio + noise  # [0.11, 0.18, 0.31, 0.39]
```

### Vectorización vs loops

```python
# ❌ Lento: loop de Python
def normalize_slow(audio):
    peak = 0
    for sample in audio:
        if abs(sample) > peak:
            peak = abs(sample)
    result = []
    for sample in audio:
        result.append(sample / peak)
    return np.array(result)

# ✅ Rápido: operaciones vectorizadas
def normalize_fast(audio):
    peak = np.max(np.abs(audio))
    return audio / peak

# Benchmark: audio de 1 segundo (16,000 samples)
# normalize_slow: ~5 ms
# normalize_fast: ~0.02 ms
# 250x más rápido
```

### Dtypes y precisión

```python
# float32 vs float64 para audio
audio32 = np.array([0.1, 0.2, 0.3], dtype=np.float32)
audio64 = np.array([0.1, 0.2, 0.3], dtype=np.float64)

# float32: suficiente para audio (rango dinámico ~150 dB)
# float64: overkill (rango dinámico ~300 dB, más allá de lo audible)

# Memoria:
# 1 hora de audio a 16kHz:
# float32: 16000 * 3600 * 4 bytes = ~230 MB
# float64: 16000 * 3600 * 8 bytes = ~460 MB
```

### Copias accidentales

Operaciones que parecen in-place pero crean copias:

```python
audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)

# ❌ Crea copia (no modifica original)
audio[[0, 2]] *= 2  # Fancy indexing siempre copia

# ✅ Modifica in-place
audio[0] *= 2
audio[2] *= 2

# ❌ Crea copia
subset = audio[::2]  # Step slicing puede copiar
subset[0] = 0.9  # No modifica audio original

# ✅ Verifica si es vista o copia
print(subset.base is audio)  # True = vista, False = copia
```

## Debugging tips

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| "MemoryError" | Array demasiado grande | Usar chunks o dtype más pequeño |
| Audio suena distorsionado | Valores fuera de [-1, 1] | Normalizar antes de reproducir |
| Operación lenta | Usando loops de Python | Vectorizar con operaciones NumPy |
| Shape mismatch | Dimensiones incorrectas | Verificar con `array.shape` |
| "dtype mismatch" | Tipos incompatibles | Usar `array.astype(target_dtype)` |
| Modificaciones no persisten | Working con copia, no vista | Usar `.copy()` explícito o verificar `.base` |

## Referencias

- [NumPy documentation](https://numpy.org/doc/)
- [NumPy Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- [Audio Signal Processing with NumPy](https://docs.scipy.org/doc/scipy/reference/signal.html)
- [Memory Management in NumPy](https://numpy.org/doc/stable/reference/arrays.ndarray.html)
