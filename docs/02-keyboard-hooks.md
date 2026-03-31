# 02 - Keyboard Hooks con pynput

## Concepto: ¿Qué son los keyboard hooks?

Un **keyboard hook** (gancho de teclado) es un mecanismo que intercepta eventos del teclado a nivel del sistema operativo, permitiendo que tu programa reaccione a teclas presionadas **incluso cuando no tiene el foco**.

### ¿Por qué no usar input() normal?

```python
# ❌ input() solo funciona cuando tu programa tiene el foco
# y bloquea la ejecución hasta que presiones Enter
tecla = input("Presiona una tecla: ")

# ✅ pynput escucha en background, sin bloquear, sin necesidad de foco
from pynput import keyboard
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()  # Escucha indefinidamente en otro thread
```

### Arquitectura de captura de teclado

```
Tu código Python
      ↓
   pynput
      ↓
┌──────────┬───────────┬──────────┐
│  Win32   │   X11/    │ Quartz   │
│  API     │   Wayland │ EventTap │  ← APIs nativas del SO
│ Windows  │   Linux   │  macOS   │
└──────────┴───────────┴──────────┘
      ↓
   Hardware (teclado)
```

pynput abstrae las diferencias entre sistemas operativos:
- **Windows**: Usa `SetWindowsHookEx` (Win32 API)
- **Linux**: Usa X11 `XRecord` o Wayland (con limitaciones)
- **macOS**: Usa `CGEventTap` (Quartz Event Taps)

## Especificaciones técnicas

### Tipos de eventos

| Evento | Descripción | Cuándo se dispara |
|--------|-------------|-------------------|
| `on_press` | Tecla presionada | En el momento exacto del keydown |
| `on_release` | Tecla soltada | Cuando se libera la tecla |

### Tipos de teclas

```python
from pynput import keyboard

# Teclas especiales (tienen atributos propios)
keyboard.Key.space      # Barra espaciadora
keyboard.Key.enter      # Enter
keyboard.Key.esc        # Escape
keyboard.Key.shift      # Shift (cualquiera)
keyboard.Key.shift_l    # Shift izquierdo
keyboard.Key.shift_r    # Shift derecho
keyboard.Key.ctrl       # Control
keyboard.Key.alt        # Alt

# Teclas normales (tienen atributo .char)
keyboard.KeyCode.from_char('a')  # Tecla 'a'
keyboard.KeyCode.from_char('A')  # Tecla 'A' (mayúscula)
keyboard.KeyCode.from_vk(65)     # Virtual key code 65
```

### El objeto Listener

```python
from pynput import keyboard

listener = keyboard.Listener(
    on_press=on_press,      # Callback para teclas presionadas
    on_release=on_release,  # Callback para teclas soltadas
    suppress=False,         # False = la tecla también llega a otras apps
)
listener.start()            # Inicia en thread separado (non-blocking)
listener.wait()             # Espera a que el listener esté listo
listener.join()             # Bloquea hasta que el listener termine
listener.stop()             # Detiene el listener manualmente
```

### suppress=True vs suppress=False

```python
# suppress=False (default): La tecla funciona normalmente en TODAS las apps
# Tu programa la detecta Y la app en foco también la recibe

# suppress=True: La tecla SOLO la recibe tu programa
# La app en foco NO recibe la tecla (se "come" el evento)
# Útil para: atajos globales, kiosk mode, game overlays
```

## Ejemplos progresivos

### Ejemplo 1: Logger de teclado básico

```python
from pynput import keyboard

def on_press(key):
    try:
        # Teclas normales tienen .char
        print(f"Presionada: {key.char}")
    except AttributeError:
        # Teclas especiales no tienen .char
        print(f"Presionada: {key}")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
```

### Ejemplo 2: Detectar combinación de teclas (Ctrl+C)

```python
from pynput import keyboard

ctrl_pressed = False

def on_press(key):
    global ctrl_pressed
    if key == keyboard.Key.ctrl:
        ctrl_pressed = True
    elif ctrl_pressed and hasattr(key, 'char') and key.char == 'c':
        print("Ctrl+C detectado!")
        return False  # Retorna False para detener el listener

def on_release(key):
    global ctrl_pressed
    if key == keyboard.Key.ctrl:
        ctrl_pressed = False

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
```

### Ejemplo 3: Push-to-Talk (lo que usa PipeVoice)

```python
from pynput import keyboard
import time

class PushToTalk:
    def __init__(self):
        self.is_holding = False
        self.last_release = 0
        self.debounce = 0.3  # 300ms entre triggers

    def on_press(self, key):
        if key == keyboard.Key.space and not self.is_holding:
            self.is_holding = True
            print("START recording")
            # Aquí iniciarías la grabación de audio

    def on_release(self, key):
        if key == keyboard.Key.space and self.is_holding:
            self.is_holding = False
            self.last_release = time.time()
            print("STOP and transcribe")
            # Aquí detendrías la grabación y transcribirías

ptt = PushToTalk()
with keyboard.Listener(on_press=ptt.on_press, on_release=ptt.on_release) as listener:
    listener.join()
```

## Conceptos profesionales

### Thread safety con keyboard hooks

Los callbacks de pynput se ejecutan en un **thread interno del listener**. Si accedes a estado compartido desde otros threads, necesitas synchronization:

```python
import threading

class SafePushToTalk:
    def __init__(self):
        self.is_holding = False
        self._lock = threading.Lock()  # Protege el estado compartido

    def on_press(self, key):
        with self._lock:  # Adquire el lock
            if not self.is_holding:
                self.is_holding = True
                # Iniciar grabación...

    def on_release(self, key):
        with self._lock:  # Adquire el lock
            if self.is_holding:
                self.is_holding = False
                # Detener grabación...

    @property
    def is_recording(self):
        with self._lock:  # Lectura thread-safe
            return self.is_holding
```

### Debounce: evitar double-trigger

El **debounce** previene que un evento se dispare múltiples veces por una sola acción física:

```python
import time

class DebouncedListener:
    def __init__(self, debounce_seconds=0.3):
        self.debounce = debounce_seconds
        self.last_trigger = 0

    def can_trigger(self):
        return (time.time() - self.last_trigger) >= self.debounce

    def on_press(self, key):
        if key == keyboard.Key.space and self.can_trigger():
            self.last_trigger = time.time()
            # Procesar evento...
```

**¿Por qué 300ms?**
- Humanos no pueden presionar/soltar consistentemente más rápido que ~150-200ms
- 300ms da margen para evitar triggers accidentales por rebote mecánico
- No es perceptible como "lag" para el usuario

### Manejo de AttributeError

Algunos eventos de teclado pueden tener atributos inesperados. Siempre usa try/except:

```python
def on_press(key):
    try:
        # Intentar acceder a .char (teclas normales)
        print(f"Carácter: {key.char}")
    except AttributeError:
        # Teclas especiales (shift, ctrl, etc.) no tienen .char
        print(f"Tecla especial: {key}")
```

### Daemon threads y limpieza

El listener de pynput corre en un thread separado. Si tu programa principal termina, necesitas asegurarte de que el thread del listener también termine:

```python
# Opción 1: Daemon thread (muere cuando el main thread muere)
listener = keyboard.Listener(...)
listener.daemon = True  # ← Importante
listener.start()

# Opción 2: Context manager (limpieza automática)
with keyboard.Listener(...) as listener:
    # ... hacer cosas ...
# ← listener.stop() se llama automáticamente al salir del with
```

### Limitaciones por plataforma

| Plataforma | Limitación | Workaround |
|-----------|-----------|------------|
| **Windows** | Requiere permisos de usuario normal | Funciona out-of-the-box |
| **Linux X11** | Necesita `python3-xlib` | `pip install python3-xlib` |
| **Linux Wayland** | Restricciones de seguridad | Usar X11 o permisos especiales |
| **macOS** | Requiere permisos de Accessibility | System Preferences → Security → Accessibility |
| **SSH/Remote** | No captura teclas locales | Ejecutar localmente, no por SSH |

## Debugging tips

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| No detecta teclas | Sin permisos en macOS | Dar permisos de Accessibility |
| Detecta teclas duplicadas | Múltiples listeners | Usar un solo listener global |
| Callbacks lentos | Operaciones bloqueantes | Mover lógica pesada a otro thread |
| No funciona en terminal remota | SSH no forward hooks | Ejecutar localmente |
| "Xlib.error.DisplayConnectionError" | Linux sin X11 | Instalar `python3-xlib` o usar X11 |

## Referencias

- [pynput documentation](https://pynput.readthedocs.io/)
- [Win32 Keyboard Hooks](https://docs.microsoft.com/en-us/windows/win32/winmsg/keyboard-input)
- [macOS Event Taps](https://developer.apple.com/documentation/coregraphics/quartz_event_services)
- [X11 Record Extension](https://www.x.org/releases/X11R7.6/doc/recordproto/recordproto.txt)
