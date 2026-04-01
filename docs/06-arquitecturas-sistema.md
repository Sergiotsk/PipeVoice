# Arquitecturas de Sistema Aplicadas en PipeVoice

## Guía para Estudiantes de Programación

---

## 1. Patrones Arquitectónicos Presentes

### 1.1 Pipeline / Pipe-and-Filter

**Qué es:** Los datos fluyen a través de una cadena de procesamiento donde cada etapa (filtro) transforma los datos y pasa el resultado a la siguiente etapa.

**En PipeVoice:**
```
Teclado → Grabación → Transcripción → stdout → Agente IA
(pynput)  (sounddevice)  (Whisper)    (print)   (opencode)
```

**Conceptos clave:**
- Cada componente tiene una sola responsabilidad
- La comunicación es unidireccional (flujo lineal)
- Los filtros son independientes y reemplazables
- `stdout` actúa como el "bus" de comunicación entre filtros

**Por qué importa:** Este patrón viene de Unix y es la base de herramientas como `grep`, `awk`, `sed`. Aprenderlo te da poder para componer herramientas simples en sistemas complejos.

---

### 1.2 Event-Driven Architecture (Arquitectura Dirigida por Eventos)

**Qué es:** El flujo del programa está determinado por eventos externos (teclas, audio, señales) en lugar de un flujo secuencial predecible.

**En PipeVoice:**
```python
# El programa NO controla cuándo pasa algo
# REACCIONA a eventos del sistema
keyboard.Listener(on_press=callback, on_release=callback)
```

**Conceptos clave:**
- **Event emitter:** `pynput` emite eventos de teclado
- **Event handler:** `on_key_press`, `on_key_release` reaccionan
- **Event loop:** El listener corre en un loop infinito esperando eventos
- **Callback:** Función que se ejecuta cuando ocurre un evento

**Por qué importa:** Es el patrón dominante en UIs, servidores web, y sistemas en tiempo real. Todo framework moderno (React, Node.js, Flutter) usa este patrón.

---

### 1.3 Producer-Consumer

**Qué es:** Un componente produce datos y otro los consume, desacoplados por un buffer.

**En PipeVoice:**
```
Productor: AudioRecorder._audio_callback() → agrega chunks al buffer
Buffer: self._buffer (lista de numpy arrays)
Consumidor: get_audio() → concatena y transcribe
```

**Conceptos clave:**
- **Desacoplamiento:** El productor no sabe quién consume
- **Buffer:** Punto de sincronización entre velocidades diferentes
- **Thread safety:** Múltiples hilos acceden al mismo buffer

**Por qué importa:** Este patrón es la base de colas de mensajes (RabbitMQ, Kafka), streams de datos, y procesamiento asíncrono.

---

### 1.4 Lazy Loading (Carga Perezosa)

**Qué es:** Cargar recursos solo cuando se necesitan, no al inicio.

**En PipeVoice:**
```python
@property
def model(self):
    if self._model is None:  # Solo carga si no existe
        self._load_model()
    return self._model
```

**Conceptos clave:**
- **Inicialización diferida:** El modelo de ~500MB no se carga hasta la primera transcripción
- **Cache:** Una vez cargado, se reutiliza
- **Property decorator:** Hace que el acceso parezca un atributo normal

**Por qué importa:** Optimiza memoria y tiempo de inicio. Usado en ORMs (Django, SQLAlchemy), frameworks web, y cualquier sistema con recursos pesados.

---

## 2. Concurrencia y Paralelismo

### 2.1 Threading en PipeVoice

**Hilos activos simultáneamente:**
1. **Main thread:** Loop principal + signal handler
2. **Keyboard listener thread:** Escucha F9 (daemon thread de pynput)
3. **Recording animation thread:** Spinner de "Escuchando..."
4. **Transcription thread:** Procesa audio con Whisper
5. **Transcribing animation thread:** Spinner de "Procesando..."

**Conceptos críticos:**
- **Daemon threads:** Se matan automáticamente cuando el main thread termina
- **Race conditions:** Múltiples hilos accediendo a `recording_indicator_active`
- **Thread safety:** `threading.Lock()` en `PushToTalk._is_holding`
- **Synchronization:** `time.sleep()` como sincronización básica (no ideal)

**Problemas que verás:**
```python
# Esto es peligroso sin locks:
nonlocal recording_indicator_active
recording_indicator_active = True  # Otro hilo puede leer al mismo tiempo
```

**Tecnologías para aprender:**
- `threading` vs `multiprocessing` vs `asyncio`
- `Lock`, `RLock`, `Semaphore`, `Event`, `Condition`
- Queue thread-safe (`queue.Queue`)
- **Asyncio** (alternativa moderna a threading en Python)

---

## 3. Separación de Responsabilidades (SoC)

### 3.1 Módulos del Proyecto

| Módulo | Responsabilidad | Patrón |
|--------|-----------------|--------|
| `main.py` | Orquestación CLI | Facade |
| `push_to_talk.py` | Detección de teclado | Observer |
| `recorder.py` | Captura de audio | Producer |
| `transcriber.py` | Speech-to-text | Consumer |

**Por qué importa:**
- Cada módulo se puede testear independientemente
- Puedes reemplazar `sounddevice` por otra librería sin tocar el resto
- El código es legible y mantenible

**Tecnologías para aprender:**
- SOLID principles (especialmente Single Responsibility)
- Dependency Injection
- Interfaces/Abstract Base Classes en Python
- Testing unitario (pytest)

---

## 4. Tecnologías para la Opción 2 (Servicio de Fondo)

### 4.1 Lo que necesitas aprender

#### A. HTTP Server (Comunicación entre procesos)
**Para qué:** La extensión del editor se comunicará con tu servicio Python vía HTTP.

**Tecnologías:**
- **FastAPI** (recomendado): Moderno, async, documentación automática
- **Flask:** Simple, bueno para empezar
- **http.server:** Built-in, solo para prototipos

**Ejemplo conceptual:**
```python
# Tu servicio expone endpoints
@app.post("/transcribe")
async def transcribe_audio():
    audio = await recorder.get_audio()
    text = transcriber.transcribe(audio)
    return {"text": text}
```

#### B. WebSockets (Comunicación en tiempo real)
**Para qué:** Streaming de audio en tiempo real, no solo request/response.

**Tecnologías:**
- `websockets` librería
- FastAPI + WebSocket support
- Socket.IO (más features, más complejo)

#### C. System Tray Application
**Para qué:** Icono en la barra de tareas para controlar el servicio.

**Tecnologías:**
- **pystray:** Simple, cross-platform
- **PyQt/PySide:** Más potente, más pesado
- **customtkinter:** Moderno, basado en tkinter

#### D. Auto-start / Daemon
**Para qué:** Que el servicio arranque con el sistema.

**Tecnologías por plataforma:**
- **Windows:** 
  - Task Scheduler (más fácil)
  - Windows Service (más robusto, necesita pywin32)
  - Startup folder (más simple)
- **Linux:** systemd service
- **macOS:** launchd plist

#### E. Process Management
**Para qué:** Controlar el ciclo de vida del servicio.

**Tecnologías:**
- `subprocess` para lanzar/parar procesos
- `multiprocessing` para procesos aislados
- **supervisor** o **pm2** (para producción)

---

## 5. Arquitectura Propuesta para Opción 2

```
┌─────────────────────────────────────────────────────────────┐
│                     SISTEMA OPERATIVO                       │
│                                                             │
│  ┌──────────────┐    ┌──────────────────────────────────┐  │
│  │  Hotkey      │    │  PipeVoice Service (Background)  │  │
│  │  (F9 Global) │───▶│                                  │  │
│  │  pynput      │    │  ┌────────────────────────────┐  │  │
│  └──────────────┘    │  │  HTTP Server (FastAPI)     │  │  │
│                      │  │  POST /record/start        │  │  │
│  ┌──────────────┐    │  │  POST /record/stop         │  │  │
│  │  Editor      │    │  │  GET  /status              │  │  │
│  │  (VSCode/    │───▶│  │  WS   /audio-stream        │  │  │
│  │   Cursor)    │    │  └────────────────────────────┘  │  │
│  │  Extensión   │    │                                  │  │
│  │  TypeScript  │    │  ┌────────────────────────────┐  │  │
│  └──────────────┘    │  │  Core Engine               │  │  │
│                      │  │  - AudioRecorder           │  │  │
│  ┌──────────────┐    │  │  - Transcriber             │  │  │
│  │  System Tray │    │  │  - PushToTalk              │  │  │
│  │  (pystray)   │    │  └────────────────────────────┘  │  │
│  └──────────────┘    │                                  │  │
│                      └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Roadmap de Aprendizaje (Orden Recomendado)

### Nivel 1: Fundamentos (Ya los tienes)
- [x] Python básico
- [x] Clases y objetos
- [x] Módulos y paquetes
- [x] Threading básico

### Nivel 2: Para el Servicio (Siguiente paso)
- [ ] **FastAPI** (1-2 semanas)
  - Rutas, request/response models
  - WebSockets para streaming
  - Background tasks
- [ ] **HTTP y APIs REST** (conceptos)
  - Métodos, status codes, headers
  - JSON serialization
- [ ] **Process management** (1 semana)
  - Daemon threads vs procesos
  - Graceful shutdown
  - Signal handling avanzado

### Nivel 3: Para la Extensión (Futuro)
- [ ] **TypeScript básico** (2-3 semanas)
  - Tipado, interfaces, async/await
- [ ] **VS Code Extension API** (2 semanas)
  - Commands, text editor API
  - Webview (si necesitas UI)
- [ ] **Node.js fundamentals** (1 semana)
  - npm, package.json
  - fetch/axios para HTTP

### Nivel 4: Producción (Opcional)
- [ ] **Testing** (pytest, httpx para APIs)
- [ ] **Logging** estructurado
- [ ] **Configuración** (pydantic settings, .env)
- [ ] **Empaquetado** (PyInstaller, Docker)

---

## 7. Conceptos de Sistema Operativo Importantes

### 7.1 Inter-Process Communication (IPC)
Cómo se comunican procesos separados:
- **HTTP/REST:** Tu servicio + extensión (recomendado)
- **Named Pipes:** Comunicación local rápida
- **Shared Memory:** Más rápido, más complejo
- **Sockets:** TCP/UDP para red o local

### 7.2 Signals y Process Lifecycle
- `SIGINT`, `SIGTERM`, `SIGKILL`
- Graceful shutdown vs force kill
- Zombie processes y orphan processes

### 7.3 Permisos y Seguridad
- Microphone permissions (especialmente en macOS)
- Global keyboard hooks (pueden ser detectados como malware)
- Firewall rules para puertos locales

---

## 8. Buenas Prácticas que ya aplicas (y debes mantener)

1. **Separation of Concerns:** Cada módulo hace una cosa
2. **Configuración externa:** CLI args en lugar de hardcode
3. **Stderr para status:** No contamina el pipe de stdout
4. **Thread safety:** Locks donde hay estado compartido
5. **Graceful shutdown:** Signal handler para cleanup

---

## 9. Anti-patrones a evitar

1. **God Object:** No meter todo en `main.py`
2. **Tight Coupling:** No hardcodear dependencias entre módulos
3. **Busy Waiting:** Usar `time.sleep()` en lugar de eventos/queues
4. **Global State:** Evitar variables globales mutables
5. **Blocking I/O en threads críticos:** Whisper bloquea el thread de transcripción (está bien porque es daemon, pero idealmente usar async)

---

## 10. Glosario de Términos

| Término | Definición |
|---------|-----------|
| **Daemon** | Proceso que corre en segundo plano sin interacción directa del usuario |
| **IPC** | Inter-Process Communication - mecanismos para que procesos se comuniquen |
| **Race Condition** | Bug que ocurre cuando el resultado depende del orden de ejecución de threads |
| **Thread-safe** | Código que funciona correctamente cuando múltiples hilos lo ejecutan simultáneamente |
| **Callback** | Función pasada como argumento que se ejecuta cuando ocurre un evento |
| **Event Loop** | Loop infinito que espera y despacha eventos |
| **Graceful Shutdown** | Cierre ordenado que limpia recursos antes de terminar |
| **Latency** | Tiempo entre una acción y su respuesta |
| **Throughput** | Cantidad de trabajo procesado por unidad de tiempo |
| **Blocking I/O** | Operación que pausa la ejecución hasta completarse |
| **Non-blocking I/O** | Operación que retorna inmediatamente, sin esperar |
| **Async/Await** | Patrón moderno para código asíncrono sin callbacks anidados |
