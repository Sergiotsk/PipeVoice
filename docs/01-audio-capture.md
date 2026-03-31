# 01 - Audio Capture con sounddevice

## Concepto: ¿Qué es el audio digital?

El audio analógico (ondas sonoras continuas) necesita convertirse en datos digitales para que una computadora lo procese. Este proceso se llama **digitalización** y tiene dos pasos fundamentales:

### Muestreo (Sampling)

Tomar "fotos" de la onda sonora a intervalos regulares. La frecuencia de muestreo (**sample rate**) indica cuántas muestras por segundo se toman, medida en **Hertz (Hz)**.

```
Onda analógica continua:  ~~~~~∿~~~~~∿~~~~~
Muestreo a 8 Hz:          ·   ·   ·   ·   ·
```

**Teorema de Nyquist-Shannon**: Para reconstruir fielmente una señal, necesitas muestrear al menos al **doble de la frecuencia máxima** que quieres capturar.

- Oído humano: 20 Hz - 20,000 Hz (20 kHz)
- CD audio: 44,100 Hz (44.1 kHz) → captura hasta ~22 kHz
- Teléfono: 8,000 Hz → captura hasta ~4 kHz (voz suficiente)
- **Whisper: 16,000 Hz (16 kHz)** → captura hasta ~8 kHz, optimizado para voz

### Cuantización (Quantization)

Cada muestra se representa con un número. La **profundidad de bits** (bit depth) determina la precisión:

| Bit Depth | Valores posibles | Uso típico |
|-----------|-----------------|------------|
| 8-bit (uint8) | 256 | Retro gaming, muy baja calidad |
| 16-bit (int16) | 65,536 | CD audio, estándar |
| **32-bit (float32)** | 4.29 mil millones | **Procesamiento profesional** |

**¿Por qué float32 para procesamiento?**
- Rango dinámico enorme sin clipping
- Operaciones matemáticas precisas (promedios, filtros, FFT)
- Valores normalizados entre -1.0 y 1.0 (independiente del hardware)
- Evita overflow en cadenas de procesamiento

### Canales

- **Mono (1 canal)**: Una sola señal de audio. Ideal para voz.
- **Stereo (2 canales)**: Dos señales (izquierda/derecha). Para música.
- **Multi-canal**: 4+ canales para surround, interfaces profesionales.

**PipeVoice usa mono** porque:
1. La voz humana es una fuente puntual (no necesita stereo)
2. Whisper espera input mono
3. Menos datos = más rápido = mejor para CPU

## Especificaciones técnicas de PipeVoice

```python
SAMPLE_RATE = 16000    # Hz - nativo de Whisper
CHANNELS    = 1        # Mono - voz solamente
DTYPE       = "float32" # Precisión profesional, rango dinámico
```

**¿Por qué 16kHz y no 44.1kHz?**

| Sample Rate | Ancho de banda | Calidad voz | Datos/seg (float32, mono) |
|-------------|---------------|-------------|---------------------------|
| 8,000 Hz | 0-4 kHz | Telefonía | 32 KB |
| **16,000 Hz** | **0-8 kHz** | **Voz clara** | **64 KB** |
| 44,100 Hz | 0-22 kHz | Música | 176 KB |
| 48,000 Hz | 0-24 kHz | Música profesional | 192 KB |

La voz humana tiene energía principal entre 300 Hz y 3,400 Hz. Con 16 kHz cubrimos hasta 8 kHz, incluyendo armónicos que dan naturalidad sin desperdiciar recursos.

## sounddevice y PortAudio

### ¿Qué es sounddevice?

`sounddevice` es una librería Python que proporciona bindings para **PortAudio**, una librería C cross-platform de audio.

```
Tu código Python
      ↓
sounddevice (bindings Python → C)
      ↓
PortAudio (abstracción cross-platform)
      ↓
┌─────────┬──────────┬──────────┐
│  WASAPI │   ALSA   │ CoreAudio│  ← APIs nativas del SO
│ Windows │  Linux   │  macOS   │
└─────────┴──────────┴──────────┘
      ↓
   Hardware (micrófono)
```

### Blocking vs Non-blocking (Streaming)

Hay dos formas de grabar audio:

**Blocking (síncrono)**:
```python
# Grabas una cantidad fija de tiempo
audio = sd.rec(int(duration * sample_rate), samplerate=16000, channels=1)
sd.wait()  # Bloquea hasta terminar
```
Problema: Necesitas saber la duración de antemano. No sirve para push-to-talk donde el usuario decide cuándo parar.

**Non-blocking (streaming con callback)**:
```python
def callback(indata, frames, time_info, status):
    # Se llama automáticamente cada ~23ms con nuevos datos
    buffer.append(indata.copy())

stream = sd.InputStream(callback=callback, samplerate=16000, channels=1)
stream.start()  # No bloquea, el callback se ejecuta en otro thread
# ... el usuario habla ...
stream.stop()
```
Ventaja: Grabas indefinidamente hasta que decidas parar. Perfecto para push-to-talk.

### El callback de audio: reglas de oro

El callback se ejecuta en un **thread de tiempo real** del sistema operativo. Violaciones = audio roto (glitches, clicks, silence):

```python
# ❌ MAL: Operaciones lentas en el callback
def callback(indata, frames, time_info, status):
    print("recibido")           # I/O es lento
    result = heavy_computation() # Bloquea el thread de audio
    time.sleep(0.1)             # Pausa el audio = glitches

# ✅ BIEN: Solo copiar datos al buffer
def callback(indata, frames, time_info, status):
    buffer.append(indata.copy())  # Rápido, sin bloqueo
```

**Reglas del callback:**
1. **Nunca bloquees**: sin `print()`, `time.sleep()`, I/O de archivos, locks largos
2. **Siempre copia**: `indata.copy()` porque el buffer se reutiliza
3. **Mínima lógica**: solo almacenar datos, procesar después
4. **Maneja status**: Los flags de overflow/underflow van a stderr, no rompen el callback

## Ejemplos progresivos

### Ejemplo 1: Grabar 3 segundos fijos (blocking)

```python
import sounddevice as sd
import numpy as np

sample_rate = 16000
duration = 3  # segundos

print("Grabando 3 segundos...")
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
sd.wait()  # Espera a que termine

print(f"Audio shape: {audio.shape}")  # (48000, 1)
print(f"Duración: {len(audio) / sample_rate:.1f}s")
```

### Ejemplo 2: Listar dispositivos de audio

```python
import sounddevice as sd

devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f"[{i}] {dev['name']} ({dev['max_input_channels']}ch, {dev['default_samplerate']}Hz)")
```

### Ejemplo 3: Streaming con callback (lo que usa PipeVoice)

```python
import sounddevice as sd
import numpy as np

buffer = []

def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"Warning: {status}")
    buffer.append(indata.copy())

# Iniciar stream
stream = sd.InputStream(callback=audio_callback, samplerate=16000, channels=1, dtype='float32')
stream.start()

print("Grabando... (presiona Enter para parar)")
input()

stream.stop()
stream.close()

# Concatenar todos los chunks
audio = np.concatenate(buffer, axis=0)
print(f"Grabados {len(audio) / 16000:.1f} segundos de audio")
```

## Conceptos profesionales

### Buffer size y latencia

El `blocksize` de PortAudio determina cuántas muestras se procesan por llamada al callback:

```python
# Blocksize pequeño = baja latencia pero más overhead de CPU
stream = sd.InputStream(callback=cb, blocksize=256, samplerate=16000)
# 256 samples / 16000 Hz = 16ms de latencia

# Blocksize grande = más latencia pero menos CPU
stream = sd.InputStream(callback=cb, blocksize=4096, samplerate=16000)
# 4096 samples / 16000 Hz = 256ms de latencia
```

**Para PipeVoice**: Usamos el default de PortAudio (generalmente 1024 samples = 64ms) porque la latencia no es crítica para grabación push-to-talk.

### Overflow y Underflow

- **Overflow**: El callback no procesó datos a tiempo, se perdieron muestras. Causa: callback muy lento.
- **Underflow**: El buffer de playback se vació (no aplica para grabación).

```python
def callback(indata, frames, time_info, status):
    if status:
        # status es un objeto con flags: input_overflow, output_underflow
        if status.input_overflow:
            print("WARNING: Audio overflow - samples lost!", file=sys.stderr)
```

### Selección de dispositivo

En sistemas con múltiples micrófonos (webcam, headset, built-in), el default puede no ser el deseado:

```python
# Ver todos los dispositivos
devices = sd.query_devices()

# Usar un dispositivo específico por índice
stream = sd.InputStream(device=2, ...)  # device=2 usa el tercer dispositivo

# O buscar por nombre
for i, dev in enumerate(devices):
    if "USB" in dev['name']:
        stream = sd.InputStream(device=i, ...)
        break
```

### Normalización de audio

Los valores float32 de audio deben estar en el rango [-1.0, 1.0]. sounddevice ya entrega en este rango, pero si procesas audio de otras fuentes:

```python
# Normalizar a [-1.0, 1.0]
audio = audio / np.max(np.abs(audio))

# Cuidado: si audio es todo silencio (todo ceros), división por cero
if np.max(np.abs(audio)) > 0:
    audio = audio / np.max(np.abs(audio))
```

## Debugging tips

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| "PortAudio not found" | PortAudio no instalado (Linux) | `sudo apt install portaudio19-dev` |
| Audio con clicks/glitches | Callback muy lento | Remover operaciones lentas del callback |
| Solo graba silencio | Dispositivo equivocado | Usar `--list-devices` y seleccionar el correcto |
| "Device unavailable" | Otro programa usando el mic | Cerrar Zoom, Discord, etc. |
| Latencia alta | Blocksize muy grande | Reducir blocksize o usar default |

## Referencias

- [sounddevice docs](https://python-sounddevice.readthedocs.io/)
- [PortAudio](https://www.portaudio.com/)
- [Nyquist-Shannon Sampling Theorem](https://en.wikipedia.org/wiki/Nyquist%E2%80%93Shannon_sampling_theorem)
- [Digital Audio Concepts](https://www.britannica.com/science/digital-audio)
