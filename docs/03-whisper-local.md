# 03 - Whisper Local: Speech-to-Text sin API keys ni costos

## Concepto: ¿Qué es Whisper?

**Whisper** es un modelo de speech-to-text (voz a texto) de código abierto creado por OpenAI. A diferencia de la API de OpenAI (que es paga), el modelo Whisper es **100% gratuito, open-source (MIT license), y corre localmente** en tu máquina.

### Diferencia clave: Modelo vs API

| | Whisper Local (open-source) | OpenAI Whisper API |
|---|---|---|
| **Costo** | Gratis, sin límites | $0.006/minuto |
| **Privacidad** | Todo local, nada sale de tu PC | Audio enviado a servidores de OpenAI |
| **Internet** | No requiere (después de descargar modelo) | Requiere conexión constante |
| **API Key** | No necesita | Necesita y se factura |
| **Modelos** | tiny, base, small, medium, large | Solo `whisper-1` (equivalente a large) |
| **Velocidad** | Depende de tu hardware | Depende de los servidores de OpenAI |
| **Licencia** | MIT | Servicio comercial |

**PipeVoice usa el modelo local** → 100% gratis para siempre, sin límites de uso.

### ¿Cómo funciona Whisper?

Whisper es un modelo de **Deep Learning** basado en la arquitectura **Transformer** (la misma que GPT, pero para audio→texto en vez de texto→texto).

```
Audio (16kHz waveform)
      ↓
[Feature Extractor] → Log-Mel Spectrogram (80 bands)
      ↓
[Transformer Encoder] → Entiende patrones de audio
      ↓
[Transformer Decoder] → Genera texto token por token
      ↓
Texto transcrito
```

### Log-Mel Spectrogram

El audio no se feeding directo al modelo. Primero se convierte en un **espectrograma log-mel**, que es una representación visual del audio:

```
Frecuencia (Hz)
   ↑
8000|  ██    ████    ██
4000| ████  ██████  ████
2000| ██████████████████
 100|████████████████████
    +────────────────────→ Tiempo
```

- **Eje X**: Tiempo
- **Eje Y**: Frecuencia (80 bandas mel-scale)
- **Color/intensidad**: Volumen en esa frecuencia

**¿Por qué mel-scale?** El oído humano no percibe frecuencias linealmente. Somos más sensibles a diferencias en bajas frecuencias que en altas. La escala mel aproxima esta percepción biológica.

## Especificaciones técnicas: Modelos disponibles

| Modelo | Parámetros | Tamaño archivo | Velocidad (CPU) | Precisión | Uso recomendado |
|--------|-----------|---------------|-----------------|-----------|-----------------|
| **tiny** | 39M | ~75 MB | ~3x real-time | Baja | Prototipos, hardware muy limitado |
| **base** | 74M | ~142 MB | ~5x real-time | Decente | Voz clara, buena velocidad |
| **small** | 244M | ~466 MB | ~10x real-time | Buena | **Default de PipeVoice** |
| **medium** | 769M | ~1.5 GB | ~30x real-time | Alta | Alta precisión, CPU potente |
| **large** | 1550M | ~3 GB | ~60x real-time | Máxima | Máxima calidad, GPU recomendada |

**"x real-time"** significa: un audio de 10 segundos tarda ~1 segundo en transcribirse (10x real-time).

### ¿Por qué PipeVoice usa `small` por defecto?

| Factor | tiny | base | **small** | medium | large |
|--------|------|------|-----------|--------|-------|
| RAM necesaria | ~1 GB | ~1 GB | ~2 GB | ~4 GB | ~8 GB |
| Latencia primera frase | ~1s | ~2s | ~3s | ~8s | ~15s |
| Precisión español | 60% | 75% | **88%** | 94% | 96% |
| Precisión inglés | 70% | 82% | **92%** | 97% | 98% |
| Acentos/ruido | Mal | Regular | **Bueno** | Muy bueno | Excelente |

`small` es el **sweet spot**: buena precisión con latencia aceptable en CPU.

## Arquitectura interna de Whisper

### Encoder-Decoder Transformer

```
                    Audio Input
                        ↓
              ┌─────────────────┐
              │  Conv1D Layers  │  ← Extrae features del waveform
              │  (stride=2)     │     Reduce resolución temporal 2x
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │    Positional   │  ← Añade información de posición
              │    Embedding    │     (el transformer no tiene noción
              └────────┬────────┘     de orden sin esto)
                       ↓
              ╔═══════════════════╗
              ║  Transformer      ║
              ║    Encoder        ║  ← 6-32 layers (según modelo)
              ║    (N layers)     ║     Self-attention sobre audio
              ╚═══════════════════╝
                       ↓
              ┌─────────────────┐
              │  Cross-Attention│  ← Conecta encoder con decoder
              └────────┬────────┘
                       ↓
              ╔═══════════════════╗
              ║  Transformer      ║
              ║    Decoder        ║  ← Genera texto token por token
              ║    (N layers)     │     Autoregressive (cada token
              ╚═══════════════════╝     depende de los anteriores)
                       ↓
                  Text Output
```

### Tokenización

Whisper usa **Byte-Pair Encoding (BPE)** con un vocabulario de ~50,000 tokens. Esto significa que palabras comunes son un solo token, mientras que palabras raras se dividen:

```
"hola" → 1 token
"transcripción" → 2-3 tokens (trans + cripción)
"speech-to-text" → 3-4 tokens (speech + to + text)
```

### Detección de idioma

Whisper puede detectar automáticamente el idioma del audio analizando los primeros segundos. También puedes forzar un idioma:

```python
# Auto-detect (default)
result = model.transcribe(audio)

# Forzar idioma
result = model.transcribe(audio, language="es")
```

**Forzar idioma es más rápido** porque el modelo no necesita ejecutar la detección.

## Ejemplos progresivos

### Ejemplo 1: Transcribir un archivo de audio

```python
import whisper

# Cargar modelo (descarga automática la primera vez)
model = whisper.load_model("small")

# Transcribir archivo
result = model.transcribe("mi_audio.mp3")

print(result["text"])           # Texto transcrito
print(result["language"])       # Idioma detectado
print(result["segments"])       # Segmentos con timestamps
```

### Ejemplo 2: Transcribir desde un numpy array (lo que usa PipeVoice)

```python
import whisper
import numpy as np
import sounddevice as sd

# Grabar audio
audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
sd.wait()

# Cargar modelo y transcribir
model = whisper.load_model("small")
result = model.transcribe(audio.flatten())

print(result["text"])
```

### Ejemplo 3: Con timestamps y segmentos

```python
import whisper

model = whisper.load_model("small")
result = model.transcribe("audio.mp3", language="es")

for segment in result["segments"]:
    start = segment["start"]
    end = segment["end"]
    text = segment["text"]
    print(f"[{start:.1f}s - {end:.1f}s] {text}")
```

### Ejemplo 4: Lazy loading con cache (lo que usa PipeVoice)

```python
class Transcriber:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            # Carga solo cuando se necesita (lazy)
            self._model = whisper.load_model("small")
        return self._model

    def transcribe(self, audio):
        # Primera llamada: carga modelo + transcribe (~5s)
        # Llamadas siguientes: solo transcribe (~1s)
        return self.model.transcribe(audio)

# Uso
t = Transcriber()
t.transcribe(audio1)  # Carga modelo, luego transcribe
t.transcribe(audio2)  # Modelo ya cargado, más rápido
```

## Conceptos profesionales

### Model caching

Whisper cachea los modelos descargados en `~/.cache/whisper/`. La primera vez descarga el archivo `.pt` (~466 MB para small), las siguientes veces lo carga del cache.

```python
# Ubicación del cache por plataforma:
# Windows: C:\Users\<user>\.cache\whisper\
# Linux:   ~/.cache/whisper/
# macOS:   ~/.cache/whisper/

# Puedes verificar si un modelo está cacheado:
import os
cache_path = os.path.expanduser("~/.cache/whisper/small.pt")
if os.path.exists(cache_path):
    print("Modelo ya descargado")
else:
    print("Primera vez, descargando modelo...")
```

### Optimización para CPU

Sin GPU, la inferencia es el cuello de botella. Optimizaciones:

**1. Pre-cargar el modelo**
```python
# Cargar al inicio, no en cada transcripción
model = whisper.load_model("small")  # ~3s una vez
# vs
model = whisper.load_model("small")  # ~3s CADA transcripción (MAL)
```

**2. Usar el modelo más pequeño que dé buena calidad**
```python
# Benchmarks aproximados en CPU moderna (frase de 5s):
# tiny:   ~1.5s
# base:   ~2.5s
# small:  ~4s    ← Sweet spot
# medium: ~12s
# large:  ~25s
```

**3. Forzar idioma**
```python
# Sin forzar: Whisper detecta idioma + transcribe
result = model.transcribe(audio)

# Con idioma: Solo transcribe (más rápido)
result = model.transcribe(audio, language="es")
```

**4. Reducir sample rate si es necesario**
```python
# Whisper requiere 16kHz. Si tu audio es 44.1kHz:
import librosa
audio_16k = librosa.resample(audio, orig_sr=44100, target_sr=16000)

# Pero si grabas a 16kHz desde el inicio, te ahorras este paso
```

### Memory management

Los modelos grandes consumen RAM significativa:

```python
# Ver consumo de memoria del modelo
import torch
model = whisper.load_model("small")
params = sum(p.numel() for p in model.parameters())
print(f"Parámetros: {params:,}")  # ~244,000,000

# En CPU, cada parámetro float32 = 4 bytes
# 244M params × 4 bytes = ~976 MB de memoria
```

### Manejo de errores

```python
try:
    result = model.transcribe(audio)
except RuntimeError as e:
    if "CUDA" in str(e):
        print("Error de GPU, usando CPU...")
        model = whisper.load_model("small", device="cpu")
    else:
        raise
except Exception as e:
    print(f"Transcripción fallida: {e}")
```

### Punctuation y formatting

Whisper genera texto con puntuación automática, pero no es perfecta:

```python
# Output típico de Whisper:
# "Hola, ¿cómo estás? Estoy bien, gracias."

# A veces puede faltar puntuación o tener errores:
# "hola como estas estoy bien gracias"

# Para mejorar: usar modelos más grandes o forzar idioma
result = model.transcribe(audio, language="es", task="transcribe")
```

## Debugging tips

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| "Model not found" | Primera ejecución | Esperar a que descargue (~466MB para small) |
| Transcripción lenta | CPU limitado | Usar modelo `base` o `tiny` |
| Texto en inglés cuando hablas español | Auto-detect falló | Forzar `language="es"` |
| Memoria insuficiente | Modelo muy grande | Usar `small` o `base` |
| Audio distorsionado | Sample rate incorrecto | Asegurar 16kHz float32 |
| "CUDA out of memory" | GPU sin suficiente VRAM | Usar `device="cpu"` |

## Referencias

- [Whisper GitHub (openai/whisper)](https://github.com/openai/whisper)
- [Whisper paper](https://cdn.openai.com/papers/whisper.pdf)
- [Transformer Architecture](https://arxiv.org/abs/1706.03762)
- [Byte-Pair Encoding](https://huggingface.co/learn/nlp-course/chapter6/5)
