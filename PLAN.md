# Plan técnico: Doom Eternal interactivo para TikTok LIVE

## 1. Contexto y Objetivo

Crear un software interactivo en Python para transmisiones en vivo de **Doom Eternal** en TikTok LIVE. 
Cada donación de los espectadores (monedas de TikTok) invoca automáticamente en tiempo real a un demonio dentro de la partida del streamer. 
A mayor cantidad de monedas donadas, mayor nivel y dificultad tendrá el demonio invocado.

- **Referencia:** Modalidades interactivas virales en TikTok (estilo *bedrock box* de Minecraft).
- **Entorno de juego:** El streamer juega en una arena continua de combate donde los demonios son invocados principalmente por la audiencia.

---

## 2. Arquitectura del Sistema (Opción Modular Limpia)

El proyecto se estructura bajo **Clean Architecture Ligera**, separando la recepción de eventos de TikTok, las reglas de negocio/cola y la inyección en Windows.

```
DoomEternalInteractivoTT/
│── config.json             # Ajustes de streamer, niveles de monedas y límites
│── requirements.txt        # Dependencias (TikTokLive, etc.)
│── main.py                 # Punto de entrada CLI (soporta --test, --streamer, --panic)
│── src/
│   ├── __init__.py
│   ├── config.py           # Cargador y validador de configuración
│   ├── models.py           # Modelos de datos (Donación, SpawnTask, DemonTier)
│   ├── core/
│   │   ├── rate_limiter.py # Control de ritmo para evitar saturar o crashear el motor
│   │   └── queue_worker.py # Cola de procesamiento en hilo secundario
│   └── adapters/
│       ├── doom_injector.py # Inyección de comandos/teclas con Windows API (ctypes/SendInput)
│       └── tiktok_client.py # Receptor de TikTokLive con filtrado de rachas
```

### 2.1 Flujo de datos

```text
TikTok LIVE ──► [TikTokClient]
                     │ Filtra combo/rachas (repeat_end)
                     │ Calcula monedas = diamond_count × repeat_count
                     ▼
                [QueueWorker & RateLimiter]
                     │ Determina entidad según rangos de config.json
                     │ Encola y dosifica según max_spawns_por_minuto
                     ▼
                [DoomInjector]
                     │ Enfoca ventana de Doom Eternal
                     │ Envía comando Meathook (chrispy ai/...) o bind directo
                     ▼
                Doom Eternal (Partida en Vivo)
```

---

## 3. Especificaciones del Juego y Conectividad

### 3.1 Doom Eternal y Meathook
- **Ejecutable objetivo:** `DOOMEternalx64vk.exe` (Steam, versión base).
- **Mecanismo de spawn:** **Meathook v7.2** (`XINPUT1_3.dll`).
  - Comando de spawn: `chrispy <entitydef>`.
  - Botón de pánico: `mh_killAi` (elimina toda la IA viva en caso de saturación).
- **Hallazgo técnico confirmado:** El launcher oficial con mods (`DOOMSandBox64vk.exe`) es incompatible con Meathook. Por lo tanto, el juego se ejecuta en el binario base `DOOMEternalx64vk.exe`.

### 3.2 Arenas de Combate
1. **Opción A (Nativa sin mods):** Modo Horda oficial (Cultist Base, Reclaimed Earth, The Holt), Slayer Gates o Master Levels. Estabilidad 100% nativa.
2. **Opción B (Arena comunitaria):** *Infinite Arena Mode* (Nexus Mods #1049), mod de arena infinita que reemplaza el Modo Horda y se inyecta con `EternalModInjector` en el juego base.

### 3.3 Gestión de Donaciones de TikTok
- Conexión mediante la librería `TikTokLive`.
- **Control de rachas:** Los regalos con multiplicador se procesan únicamente cuando el evento indica fin de racha (`repeat_end = 1`) o si es un regalo único, multiplicando `diamond_count × repeat_count`.
- **Rate Limiting:** Cola deslizante para limitar spawns por minuto (`max_spawns_por_minuto`), evitando congelamientos del juego o sobrecarga de entidades.

---

## 4. Estructura de Configuración (`config.json`)

```json
{
  "usuario_tiktok": "nombre_de_usuario",
  "max_spawns_por_minuto": 20,
  "delay_entre_spawns_ms": 2500,
  "tecla_panico": "F12",
  "niveles": [
    {
      "min_monedas": 1,
      "max_monedas": 29,
      "categoria": "Fodder",
      "demonios": ["ai/fodder/imp", "ai/fodder/zombie_tier_1"]
    },
    {
      "min_monedas": 30,
      "max_monedas": 299,
      "categoria": "Heavy",
      "demonios": ["ai/heavy/cacodemon", "ai/heavy/hellknight", "ai/heavy/mancubus"]
    },
    {
      "min_monedas": 300,
      "max_monedas": 99999,
      "categoria": "Super Heavy",
      "demonios": ["ai/superheavy/tyrant", "ai/superheavy/baron", "ai/superheavy/marauder"]
    }
  ]
}
```

---

## 5. Fases de Implementación

- **Fase 1: Módulo de inyección y pruebas locales**
  - Implementación de `DoomInjector` con `ctypes.windll.user32.SendInput`.
  - Modo `--test <monedas>` para validar spawns sin conexión a internet.
  - Verificación del botón de pánico (`--panic` y tecla global).

- **Fase 2: Conexión con TikTok y Worker en segundo plano**
  - Integración de `TikTokClient` con eventos `on_gift`.
  - Conexión con `QueueWorker` y `RateLimiter`.
  - Pruebas de estrés y conteo de rachas.

- **Fase 3: Ajuste fino y Live de prueba**
  - Calibración de dificultad (monedas vs demonios).
  - Stream de prueba privado/controlado.
