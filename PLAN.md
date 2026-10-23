# Plan técnico: Doom Eternal interactivo para TikTok LIVE

> Documento de trabajo del equipo. La idea original está en [`planSoftware.md`](planSoftware.md).

## 1. Contexto

El objetivo es hacer lives de **Doom Eternal** en TikTok en los que **cada donación (monedas de TikTok) hace aparecer un demonio** dentro del juego. Mientras más monedas se donen, más fuerte será el demonio. La referencia son los lives de Minecraft tipo *bedrock box*, donde los espectadores donan para complicarle la partida al streamer.

El streamer juega en una arena, y los espectadores "compran" demonios para hacerle la partida más difícil.

## 2. Hallazgos clave (investigación)

### 2.1 Doom Eternal: cómo hacer aparecer demonios
- Doom Eternal **no tiene API ni soporte oficial de mods**.
- La única vía viable es **Meathook** (archivo `XINPUT1_3.dll`), un mod comunitario que desbloquea la consola de desarrollador y agrega comandos propios:
  - `chrispy <entitydef> [x y z]`: hace aparecer una entidad (por ejemplo, `chrispy ai/fodder/imp`).
  - `rechrispy`: repite el último spawn.
  - `mh_killAi` / `mh_removeAi`: mata o elimina a toda la IA viva (útil como **botón de pánico**).
  - `mh_spawnfile`, `mh_spawninfo`: aparecer entidades desde un archivo y copiar la posición actual.
- Repositorio: [brongo/m3337ho0o0ok](https://github.com/brongo/m3337ho0o0ok), versión 7.2, compatible con la actualización 6.66 rev 2 del juego.
- **Solo funciona en modo offline** (campaña, Master Levels, arenas). Nunca se debe usar en partidas online.
- ⚠️ **Compatibilidad sin confirmar:** Meathook es de 2021. La actualización de mods oficiales (2025) cambió el ejecutable del juego, y no hay confirmación de que Meathook siga funcionando. **Es lo primero que se verifica en la Fase 0** (ver sección 2.5 y los planes B en la sección 6).

### 2.2 Versión del juego
- **Decisión: se usará la versión de Steam.** La versión de Xbox / Microsoft Store se instala en una carpeta protegida (`WindowsApps`) y no hay evidencia de que Meathook funcione en ella.
- **El disco de instalación no importa** (C:, D:, etc.). Meathook se copia en la misma carpeta que `DOOMEternalx64vk.exe`, y nuestra app encuentra el juego por el **título de su ventana**, no por su ruta.

### 2.3 TikTok LIVE: cómo leer las donaciones
- **TikTok LIVE Studio no tiene API pública.**
- Opciones:
  - **TikTokLive (Python)**: librería no oficial que recibe en tiempo real los eventos del live (regalos, comentarios, likes) usando solo el nombre de usuario. **Es la opción elegida.**
  - **TikFinity**: herramienta lista para usar que puede simular teclas por cada regalo. Sirve para una prueba rápida sin código, pero ofrece menos control.
- **Particularidad de las rachas:** un regalo enviado en racha (x2, x3...) genera eventos repetidos. Solo se debe contar **cuando la racha termina** (`repeat_end`), o de inmediato si el regalo no admite rachas. Si no, se aparecen demonios duplicados.

### 2.4 Límite de spawns
- No hay documentación que confirme que el juego elimine demonios por sí solo cuando hay demasiados. Sí se sabe que el motor tiene un límite de entidades: si se exceden, lo esperable es **lag o que el juego se cierre**.
- Por eso el diseño incluye un **límite configurable** de spawns por minuto, una **cola** para las donaciones que excedan el límite y un **botón de pánico** (`mh_killAi`).

### 2.5 Mapas de la comunidad (arenas para el live)
- Desde **agosto de 2025**, Doom Eternal tiene **soporte oficial de mods en Steam** (en Microsoft Store está anunciado como "próximamente").
- Al abrir el juego aparece un **launcher** con la pestaña **Mods**: un navegador con más de 650 mods de la comunidad. El flujo es: **Download** → cola de descargas → en **Play** se activa el mod (aparece en *Active Mods*) → se lanza el juego con mods.
- **Decisión: las pruebas de spawn se harán en mapas/arenas de la comunidad.** Candidatos:
  | Mapa | Origen | Notas |
  |---|---|---|
  | **Graveyard** | Mod oficial de Bethesda (navegador de mods) | Arena pequeña. **Primera opción** para las primeras pruebas. |
  | Arenas de la comunidad | Navegador oficial de mods | Buscar con las etiquetas *arena* / *horde*. |
  | **Infinite Arena Mode** | Nexus Mods (#1049) | Modo horda infinito sobre mapas de BATTLEMODE. |
  | Arena slaughter | Nexus Mods (#1129), migrado al portal oficial | Oleadas aleatorias en arenas de BATTLEMODE. |
- **Regla:** solo **un mod de nivel activo a la vez**. Sus autores advierten que varios a la vez pueden cerrar el juego.
- **Plan de respaldo sin mods:** Master Levels, Slayer Gates o el Horde Mode oficial (Cultist Base, Reclaimed Earth, The Holt).
- **Por verificar:** que Meathook (`chrispy`) funcione dentro de un mapa cargado desde el launcher de mods. Si no funciona, el plan B es usar idStudio (sección 6).

## 3. Solución propuesta

### 3.1 Por qué una app propia y no TikFinity
| Criterio | App propia (Python) | TikFinity + teclas |
|---|---|---|
| Elegir el demonio según el **total de monedas** | ✅ | ❌ (solo por tipo de regalo) |
| Cola y límite de spawns | ✅ | ❌ |
| Registro de donaciones | ✅ | Parcial |
| Esfuerzo inicial | Medio | Muy bajo |

### 3.2 Flujo

```
TikTok LIVE ──(TikTokLive: GiftEvent)──► doom_tiktok.py
                                           │ monedas = diamond_count × repeat_count
                                           │ nivel según config.json
                                           ▼
                                     Cola + límite/min
                                           │
                                           ▼
                          Doom Eternal (ventana enfocada)
              tecla de consola → "chrispy ai/..." → Enter → cerrar consola
```

**Alternativa de inyección (preferida si funciona):** definir *binds* en la configuración de Doom (`bind F5 "chrispy ai/fodder/imp"`) para que la app solo tenga que pulsar una tecla, sin escribir texto en la consola. Es más rápida y robusta. En la Fase 0 se verifica si `bind` acepta los comandos de Meathook.

### 3.3 Archivos del proyecto
| Archivo | Propósito |
|---|---|
| `doom_tiktok.py` | Conexión con TikTokLive, cálculo de monedas, cola con un hilo *worker*, envío de teclas con `ctypes` + `SendInput` (biblioteca estándar, sin dependencias extra) y log en consola. |
| `config.json` | Usuario de TikTok, niveles de donación y límite de spawns (ver ejemplo abajo). |
| `requirements.txt` | `TikTokLive` |

Ejemplo de `config.json` (los *entitydefs* definitivos se obtienen en la Fase 0):

```json
{
  "usuario_tiktok": "nombre_de_usuario",
  "max_spawns_por_minuto": 20,
  "niveles": [
    { "min_monedas": 1,    "demonios": ["ai/fodder/imp"] },
    { "min_monedas": 100,  "demonios": ["ai/heavy/..."] },
    { "min_monedas": 1000, "demonios": ["ai/superheavy/..."] }
  ]
}
```

La app incluye un modo `--test <monedas>` que **simula una donación** sin conectarse a TikTok, para probar los spawns sin estar en vivo.

### 3.4 Fuera de alcance (por ahora)
Overlay en OBS / TikTok LIVE Studio con el nombre del donador, ranking de donadores e interfaz gráfica. Se evaluarán después del primer live de prueba.

## 4. Fases de trabajo

### Fase 0: Validación (sin código)
**A. Preparar el juego y la arena**
1. Instalar Doom Eternal desde **Steam**.
2. Abrir el launcher → pestaña **Mods** → descargar **Graveyard** (y, como alternativa, una arena de la comunidad).
3. Activar **solo** ese mod de nivel y lanzar el juego con mods. Confirmar que la arena carga bien.

**B. Comprobar Meathook (punto crítico)**
4. Copiar `XINPUT1_3.dll` (Meathook v7.2) en la carpeta del juego, junto a `DOOMEternalx64vk.exe`.
5. Dentro de la arena, abrir la consola con la tecla `` ` `` (tilde) y ejecutar `chrispy ai/fodder/imp`. Debe aparecer un imp.
6. Repetir la prueba **en el juego sin mods** (por ejemplo, un Master Level) para saber si una falla viene de Meathook o del mapa de la comunidad.
7. Si Meathook no carga o el juego se cierra, **detener la fase** y pasar a los planes B (sección 6).

**C. Datos para la app**
8. Anotar los *entitydefs* de cada categoría (usar `listcmds` / `find` en la consola):
   - **Fodder:** imp, zombie, soldado...
   - **Heavy:** Cacodemon, Mancubus, Arachnotron...
   - **Super heavy:** Tyrant, Marauder, Archvile...
9. Probar si `bind <tecla> "chrispy ..."` funciona.
10. **Prueba de estrés en la arena elegida:** aparecer 10, 20 y 40 demonios seguidos y anotar con cuántos baja el FPS o se cierra el juego. Ese número define `max_spawns_por_minuto`.
11. Verificar que `mh_killAi` limpia la arena (botón de pánico).
12. Anotar en este documento la arena elegida, los *entitydefs* y el límite obtenido.

### Fase 1: Spawns desde la app
- `python doom_tiktok.py --test 500` hace aparecer el demonio del nivel correcto en el juego.

### Fase 2: Conexión con TikTok
- Conectar TikTokLive a un live de prueba y verificar que las rachas se cuentan bien.

### Fase 3: Ajuste
- Ajustar los niveles de monedas y el límite de spawns para que el juego sea desafiante pero estable.

## 5. Verificación
- `python doom_tiktok.py --test 1`, `--test 100` y `--test 1000` hacen aparecer el demonio de cada nivel en la arena.
- En un live de prueba, una Rosa (1 moneda) produce 1 spawn, y una racha de x5 produce exactamente 5 spawns, sin duplicados.
- Con la cola llena, los spawns respetan `max_spawns_por_minuto` y el juego no se cierra.

## 6. Riesgos
| Riesgo | Mitigación |
|---|---|
| **Meathook no funciona con la versión actual del juego** (después de la actualización de mods oficiales) | Plan B 1: revisar en Steam → Propiedades → **Betas** si existe una rama anterior del juego. Plan B 2: crear con **idStudio** un mod oficial que haga aparecer a los demonios (requiere investigar cómo recibiría las órdenes desde nuestra app). |
| Meathook funciona en el juego base pero no en mapas de la comunidad | Usar como arena un mapa del juego base (Master Level, Slayer Gate, Horde Mode). |
| Un mod de arena se rompe o causa crasheos | Tener al menos dos arenas probadas; activar solo un mod de nivel a la vez. |
| Una actualización del juego rompe Meathook o los mods | No actualizar el juego en la PC del stream y fijar la versión que funcione. |
| TikTok cambia su protocolo interno (TikTokLive es no oficial) | Mantener la librería actualizada; TikFinity queda como plan B. |
| Demasiados demonios cierran el juego | Límite por minuto + cola + botón de pánico `mh_killAi`. |
| Se pierde el foco de la ventana durante el live | La app vuelve a enfocar la ventana de Doom antes de cada envío de teclas. |

## 7. Referencias
- Meathook: https://github.com/brongo/m3337ho0o0ok
- Soporte oficial de mods (Bethesda): https://slayersclub.bethesda.net/en-US/news/doom-eternal-pc-mods-update
- idStudio (documentación oficial): https://idstudio.idsoftware.com
- Infinite Arena Mode: https://www.nexusmods.com/doometernal/mods/1049
- Arena slaughter: https://www.nexusmods.com/doometernal/mods/1129
- Horde Mode (Doom Wiki): https://doomwiki.org/wiki/Horde_Mode
- TikTokLive (Python): https://pypi.org/project/TikTokLive/
- TikFinity: https://tikfinity.zerody.one
