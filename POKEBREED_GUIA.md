# 🎮 Pokebreed Ultimate — Guía de Desarrollo

> Guía para el desarrollador. Todo lo que necesitas saber para retomar el proyecto desde cero.

---

## 📁 Estructura del proyecto

```
POKEBREED/
├── .env                        → credenciales (nunca en git)
├── .gitignore
├── setup.ps1                   → configuración inicial (ejecutar solo una vez)
├── start.ps1                   → arranca el backend (API)
├── start-frontend.ps1          → arranca el frontend
├── backend/
│   ├── main.py                 → entrada de la API (FastAPI)
│   ├── database.py             → conexión a PostgreSQL
│   ├── models.py               → tablas de la base de datos (SQLAlchemy)
│   ├── routes/
│   │   ├── especies.py         → endpoints GET /especies/
│   │   └── breeding.py         → endpoint POST /breeding/
│   ├── game_logic/
│   │   └── breeding.py         → lógica del breeding engine
│   ├── seed_especies.py        → importa 386 especies desde PokéAPI
│   ├── seed_evolucion.py       → marca raíces, formas finales y evoluciones
│   ├── seed_recetas.py         → sincroniza recetas de breeding (upsert)
│   └── sync.py                 → ejecuta todos los seeds en orden
├── data/
│   ├── legendarios.json
│   ├── especies_raiz.json
│   ├── gen1/
│   │   ├── formas_finales.json
│   │   ├── evoluciones.json
│   │   └── recetas_breeding.json
│   ├── gen2/
│   │   └── ...
│   └── gen3/
│       └── ...
└── frontend/
    ├── index.html
    ├── assets/
    └── src/
        ├── main.js
        ├── api.js
        ├── config.js
        └── scenes/
            ├── BootScene.js
            ├── RanchScene.js
            └── UIScene.js
```

---

## 🚀 Arrancar el proyecto

### Primera vez (solo una vez)

```powershell
.\setup.ps1
```

Esto configura los permisos de PowerShell para poder ejecutar scripts `.ps1`.

### Cada vez que quieras trabajar

Abre **dos terminales** en la raíz del proyecto:

```powershell
# Terminal 1 — Backend (API)
.\start.ps1

# Terminal 2 — Frontend
.\start-frontend.ps1
```

| Servicio | URL |
|---|---|
| API | http://127.0.0.1:8000 |
| Documentación API | http://127.0.0.1:8000/docs |
| Juego | http://localhost:3000 |

> ⚠️ Ambos servidores deben estar corriendo a la vez.

---

## 🗄️ Base de datos

### Tablas

| Tabla | Descripción |
|---|---|
| `especies` | Plantilla de cada Pokémon (stats, tipos, grupos de huevo) |
| `condiciones_evolucion` | Cómo y cuándo evoluciona cada especie |
| `recetas_breeding` | Qué dos especies pueden criar juntas |
| `resultados_breeding` | Qué sale de cada receta y con qué probabilidad |
| `zonas` | Zonas de crianza y experiencia |
| `jugadores` | Save file del jugador |
| `pokemon` | Instancias concretas con IVs, nivel, zona... |
| `movimientos` | Catálogo global de movimientos |
| `pokemon_movimientos` | Qué movimientos sabe cada Pokémon |

### Resetear y recrear tablas

⚠️ **Borra todos los datos.** Solo usar en desarrollo.

```powershell
cd backend
python
```

```python
from database import engine, Base
import models
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
exit()
```

### Poblar desde cero

```powershell
cd backend
python seed_especies.py     # tarda ~3 min, llama a PokéAPI
python sync.py              # evoluciones + recetas
```

---

## 📝 Modificar recetas de breeding

**Los JSONs son la única fuente de verdad.** Nunca edites la BD directamente.

### Añadir una receta nueva

1. Abre el JSON de la generación del **resultado** (no de los padres):
   - `data/gen1/recetas_breeding.json` → resultado Gen1
   - `data/gen2/recetas_breeding.json` → resultado Gen2
   - `data/gen3/recetas_breeding.json` → resultado Gen3

2. Añade la receta:

```json
{
  "resultado_pokedex": 79,
  "notas": "Slowpoke — descripción narrativa",
  "combinaciones": [
    {"padre1_pokedex": 55, "padre2_pokedex": 65}
  ]
}
```

Para recetas con zona requerida o aleatoriedad:

```json
{
  "resultado_pokedex": 146,
  "notas": "Moltres — zona fuego extrema",
  "zona_requerida": "fire",
  "intensidad_minima": 1.8,
  "probabilidad_base": 0.7,
  "combinaciones": [
    {"padre1_pokedex": 126, "padre2_pokedex": 134}
  ],
  "resultados_alternativos": [
    {"resultado_pokedex": 250, "probabilidad": 0.3}
  ]
}
```

3. Sincroniza la BD:

```powershell
cd backend
python sync.py
```

### Añadir Gen4+

1. Crea `data/gen4/` con `formas_finales.json`, `evoluciones.json`, `recetas_breeding.json`
2. Añade `"gen4"` a la lista de generaciones en `seed_evolucion.py` y `seed_recetas.py`
3. Ejecuta `python sync.py`

---

## 🥚 Sistema de breeding

### Reglas

- Solo pueden criar **formas finales** (Venusaur sí, Ivysaur no)
- Los **legendarios no pueden criar** (`data/legendarios.json`)
- Géneros compatibles: M+F, o uno de los dos es Ditto
- Dos Ditto no pueden criar entre sí
- Del huevo siempre sale la **forma base** de la línea

### Flujo

```
1. Validación de pareja
2. Buscar receta cruzada → si no hay, receta básica
3. Calcular resultado (probabilidades + condición de zona)
4. Herencia de IVs (3 padres + 3 aleatorios, o 5+1 con Destino Nudo)
5. Naturaleza (aleatoria, o heredada con Piedraeterna)
6. Shiny (1/4096)
7. Género (según ratio de la especie)
8. Crear el huevo
```

### Endpoint

```
POST /breeding/
```

```json
{
  "pokemon1_id": 1,
  "pokemon2_id": 2,
  "jugador_id": 1,
  "zona_tipo": "fire",
  "zona_intensidad": 1.8,
  "destino_nudo": false,
  "piedraeterna_p1": false,
  "piedraeterna_p2": false
}
```

---

## 🌿 Sistema de evolución

| `tipo_condicion` | Campo relevante | Ejemplo |
|---|---|---|
| `nivel` | `valor_nivel` | Bulbasaur nivel 16 → Ivysaur |
| `objeto` | `objeto_requerido` | Eevee + `piedra-fuego` → Flareon |
| `zona` | `zona_tipo_requerido` | Eevee en zona `psychic` → Espeon |
| `amistad` | `amistad_minima` | Feebas amistad 170 → Milotic |

---

## 🖥️ Frontend

### Stack

- **Phaser 3** — motor del juego (canvas, sprites, input)
- **HTML/CSS** — UI lateral y barras
- **Vanilla JS** — comunicación entre Phaser y el HTML

### Escenas de Phaser

| Escena | Descripción |
|---|---|
| `BootScene` | Precarga de assets, lanza RanchScene |
| `RanchScene` | Mapa del rancho, sprites, input |

### Sprites

Cargados automáticamente desde PokéAPI:
```
https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{numero_pokedex}.png
```

---

## ⚙️ Variables de entorno

Archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/pokebreed
```

---

## 🗺️ Hoja de ruta

```
✅ Fase 1 — Base de datos y modelos
✅ Fase 2 — Datos desde PokéAPI + JSONs
✅ Fase 3 — Breeding engine
🔄 Fase 5 — Frontend con Phaser.js (en curso)
   ✅ Estructura base HTML/CSS/JS
   ✅ Mapa del rancho con zonas
   ✅ Sprites de Pokémon con animación idle
   ✅ Selección de Pokémon y panel de IVs
   ✅ Botón de crianza conectado a la API
   ⬜ Endpoint GET /pokemon/ del jugador
   ⬜ Sistema de huevos visual
   ⬜ Construcción de zonas
   ⬜ Pokédex
⬜ Fase 4 — Combate por turnos
⬜ Fase 6 — Meta-juego y progresión
```

---

## 🐛 Errores comunes

| Error | Causa | Solución |
|---|---|---|
| `uvicorn no reconocido` | Venv no activado | Usar `.\start.ps1` en lugar de uvicorn directamente |
| Scripts `.ps1` bloqueados | Permisos de PowerShell | Ejecutar `.\setup.ps1` una vez |
| `UndefinedColumn` al arrancar | Modelo actualizado pero tabla no | Resetear tablas y re-seedear |
| `JSONDecodeError` en seed | JSON vacío o mal guardado | Abrir el JSON, guardar con UTF-8 sin BOM |
| Receta no encontrada | JSON no sincronizado con BD | Ejecutar `python sync.py` |
| `DATABASE_URL no definida` | Falta el `.env` | Crear `.env` en la raíz |
| Frontend no conecta con API | CORS bloqueado | Ver sección CORS abajo |

### CORS — necesario para conectar frontend con API

En `backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

*Última actualización: Fase 5 en curso — frontend base implementado.*
