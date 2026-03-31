# 05 - CLI Pipe Pattern: La Filosofía Unix en Acción

## Concepto: ¿Qué es un pipe?

Un **pipe** (tubería) es un mecanismo de los sistemas Unix/Linux que conecta la **salida estándar (stdout)** de un programa con la **entrada estándar (stdin)** de otro. El operador `|` (pipe) crea esta conexión.

```
programa1 | programa2 | programa3
   stdout  →  stdin  →  stdout  →  stdin
```

### La Filosofía Unix

> "Write programs that do one thing and do it well. Write programs to work together. Write programs to handle text streams, because that is a universal interface."
> — Doug McIlory, creador de los pipes en Unix

**Tres principios:**
1. **Do one thing well**: Cada programa tiene una responsabilidad clara
2. **Work together**: Los programas se combinan para crear flujos complejos
3. **Text streams**: La interfaz universal es texto plano

### Ejemplo clásico

```bash
# Contar líneas de código Python, excluyendo comentarios y líneas vacías
find . -name "*.py" | xargs cat | grep -v "^#" | grep -v "^$" | wc -l

# Desglose:
# find . -name "*.py"        → Lista archivos .py
# xargs cat                  → Concatena su contenido
# grep -v "^#"               → Excluye líneas que empiezan con #
# grep -v "^$"               → Excluye líneas vacías
# wc -l                      → Cuenta líneas restantes
```

### PipeVoice en la filosofía Unix

```
pipevoice | agente_ia
   ↓          ↓
  Una cosa   Una cosa
  (voz→texto) (texto→respuesta)
```

PipeVoice hace **una sola cosa**: convertir voz a texto y enviarlo a stdout. El agente receptor hace **otra cosa**: procesar ese texto y responder.

## Especificaciones técnicas

### Los tres streams estándar

| Stream | Descriptor | Propósito | Redirección |
|--------|-----------|-----------|-------------|
| **stdin** | 0 | Entrada de datos | `< archivo` |
| **stdout** | 1 | Salida normal | `> archivo` |
| **stderr** | 2 | Errores y logs | `2> archivo` |

### Redirección en la práctica

```bash
# Redirigir stdout a archivo
python pipevoice > texto.txt

# Redirigir stderr a archivo (stdout sigue en pantalla)
python pipevoice 2> errores.log

# Redirigir ambos a archivos separados
python pipevoice > texto.txt 2> errores.log

# Redirigir ambos al mismo archivo
python pipevoice > todo.log 2>&1

# Descartar stderr (silenciar errores)
python pipevoice 2>/dev/null  # Linux/macOS
python pipevoice 2>NUL         # Windows
```

### ¿Por qué PipeVoice usa stderr para logs?

```python
# ❌ MAL: Los logs contaminan el pipe
print("Grabando...")           # Va a stdout → llega al agente como texto
print(texto_transcrito)        # Va a stdout → llega al agente

# El agente recibiría:
# "Grabando...\nHola, ¿cómo estás?\n"
# ← El agente procesa "Grabando..." como parte del mensaje del usuario

# ✅ BIEN: Logs a stderr, texto a stdout
print("Grabando...", file=sys.stderr)   # Va a stderr → se ve en pantalla
print(texto_transcrito)                  # Va a stdout → llega al agente

# El agente recibe SOLO:
# "Hola, ¿cómo estás?"
```

## Patrones de CLI profesionales

### Patrón 1: Filtro

Lee stdin, transforma, escribe stdout.

```python
# Ejemplo: convertir texto a mayúsculas
import sys

for line in sys.stdin:
    print(line.upper(), end='')

# Uso:
# cat archivo.txt | python upper.py
```

### Patrón 2: Generador

Produce datos en stdout sin leer stdin.

```python
# PipeVoice es un generador: produce texto transcrito
import sys

while True:
    texto = transcribir_voz()
    print(texto)
    sys.stdout.flush()  # Importante: flush inmediato

# Uso:
# python pipevoice | agente
```

### Patrón 3: Consumidor

Lee stdin y produce efectos secundarios (sin stdout).

```python
# Ejemplo: guardar en base de datos
import sys
import json

for line in sys.stdin:
    data = json.loads(line)
    save_to_database(data)

# Uso:
# python pipevoice | python save_transcripts.py
```

### Patrón 4: Tee (duplicar output)

```bash
# Ver en pantalla Y guardar en archivo
python pipevoice | tee transcripcion.txt

# Guardar en múltiples archivos
python pipevoice | tee -a diario.txt | tee -a backup.txt

# El flag -a es append (agrega al final, no sobrescribe)
```

## Ejemplos progresivos

### Ejemplo 1: Pipe simple

```bash
# Transcribir y ver en pantalla
python -m src

# Transcribir y guardar
python -m src > transcripcion.txt

# Transcribir y enviar a opencode
python -m src | opencode
```

### Ejemplo 2: Pipe con procesamiento intermedio

```bash
# Transcribir y convertir a mayúsculas
python -m src | tr '[:lower:]' '[:upper:]'

# Transcribir y contar palabras
python -m src | wc -w

# Transcribir y buscar palabras clave
python -m src | grep -i "importante"
```

### Ejemplo 3: Pipe con múltiples destinos

```bash
# Transcribir, guardar, y enviar a agente
python -m src | tee -a historial.txt | opencode

# Transcribir, filtrar, y enviar
python -m src | grep -v "silencio" | claude
```

### Ejemplo 4: Script de automatización

```bash
#!/bin/bash
# transcribe_and_summarize.sh

# Transcribir voz
TRANSCRIPT=$(python -m src --language es)

# Enviar a agente para resumen
echo "Resume este texto: $TRANSCRIPT" | opencode

# Guardar copia
echo "$TRANSCRIPT" >> transcripciones/$(date +%Y%m%d).txt
```

## Conceptos profesionales

### Flush inmediato

Por defecto, Python bufferiza stdout cuando no es una terminal (es decir, cuando está en un pipe). Esto significa que el texto transcrito puede no llegar al receptor inmediatamente.

```python
import sys

# ❌ MAL: Bufferizado (el receptor espera)
print(texto)  # Se queda en buffer hasta que se llena o el programa termina

# ✅ BIEN: Flush inmediato
print(texto)
sys.stdout.flush()  # Fuerza el envío inmediato

# Alternativa: deshabilitar bufferizado globalmente
# python -u main.py  # Flag -u = unbuffered
# PYTHONUNBUFFERED=1 python main.py  # Variable de entorno
```

### Señales y graceful shutdown

Un CLI profesional maneja señales del sistema operativo para limpiar recursos:

```python
import signal
import sys

running = True

def signal_handler(sig, frame):
    global running
    running = False
    print("\nShutting down...", file=sys.stderr)
    cleanup()  # Cerrar streams, archivos, etc.
    sys.exit(0)

# Registrar handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # kill <pid>

# Loop principal
while running:
    # ... hacer trabajo ...
    pass
```

**Señales comunes:**
| Señal | Número | Cómo se genera | Propósito |
|-------|--------|----------------|-----------|
| SIGINT | 2 | Ctrl+C | Interrupción del usuario |
| SIGTERM | 15 | `kill <pid>` | Terminación graceful |
| SIGHUP | 1 | Cerrar terminal | Terminal colgó |
| SIGKILL | 9 | `kill -9 <pid>` | Matar forzosamente (no se puede capturar) |

### Exit codes

El exit code indica el resultado de la ejecución:

```python
import sys

# Éxito
sys.exit(0)

# Error genérico
sys.exit(1)

# Error de uso (argumentos inválidos)
sys.exit(2)

# Python tiene códigos estándar:
# 0: Success
# 1: General error
# 2: Misuse of shell builtins
# 126: Command not executable
# 127: Command not found
# 128+n: Signal n received
```

**En scripts:**
```bash
python -m src
if [ $? -eq 0 ]; then
    echo "Éxito"
else
    echo "Error: $?"
fi
```

### argparse profesional

```python
import argparse

parser = argparse.ArgumentParser(
    prog="pipevoice",
    description="Descripción corta del propósito.",
    epilog="Ejemplos de uso al final del help.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

# Argumentos posicionales (requeridos)
parser.add_argument("input", help="Archivo de entrada")

# Argumentos opcionales con flags
parser.add_argument(
    "--model",
    choices=["tiny", "base", "small", "medium", "large"],
    default="small",
    help="Modelo Whisper a usar (default: small)",
)

# Flag booleano
parser.add_argument(
    "--verbose",
    action="store_true",
    help="Mostrar información detallada",
)

# Acción especial
parser.add_argument(
    "--list-devices",
    action="store_true",
    help="Listar dispositivos de audio disponibles",
)

args = parser.parse_args()
```

### Cross-platform considerations

```python
import sys
import os

# Detectar sistema operativo
if sys.platform == "win32":
    # Windows-specific
    null_device = "NUL"
elif sys.platform == "darwin":
    # macOS-specific
    null_device = "/dev/null"
else:
    # Linux y otros Unix-like
    null_device = "/dev/null"

# Path separators (usar pathlib en vez de os.path)
from pathlib import Path
config_dir = Path.home() / ".config" / "pipevoice"
config_dir.mkdir(parents=True, exist_ok=True)
```

## Debugging tips

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| Pipe no recibe datos | Buffer de stdout | Usar `sys.stdout.flush()` o `python -u` |
| Logs aparecen en el pipe | Usando `print()` sin `file=sys.stderr` | Redirigir logs a stderr |
| Ctrl+C no funciona | Signal handler no registrado | Usar `signal.signal(signal.SIGINT, handler)` |
| "Broken pipe" error | Receptor del pipe cerró | Manejar `BrokenPipeError` gracefully |
| Encoding errors | Caracteres especiales | Usar `encoding='utf-8'` en archivos |

### BrokenPipeError

Cuando el receptor del pipe termina antes que el emisor:

```python
import sys
import signal

# Ignorar BrokenPipeError (común en pipes)
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

try:
    print(texto)
    sys.stdout.flush()
except BrokenPipeError:
    # El receptor cerró el pipe, salir gracefulmente
    sys.stderr.close()
    sys.exit(0)
```

## Referencias

- [The Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy)
- [Advanced Bash-Scripting Guide - I/O Redirection](https://tldp.org/LDP/abs/html/io-redirection.html)
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html)
- [Signal handling in Python](https://docs.python.org/3/library/signal.html)
