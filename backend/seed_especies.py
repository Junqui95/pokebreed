import requests
import time
from database import SessionLocal
from models import Especie

# ─────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────
LIMITE = 386  # Gen 1-3
BASE_URL = "https://pokeapi.co/api/v2"

# Mapeo de grupos de huevo (inglés → español opcional, lo dejamos en inglés por ahora)
def get_session():
    db = SessionLocal()
    return db


def fetch_especie(numero: int) -> dict | None:
    """Obtiene los datos de una especie desde PokéAPI."""
    try:
        # Endpoint principal — stats, tipos, habilidades
        r_pokemon = requests.get(f"{BASE_URL}/pokemon/{numero}", timeout=10)
        r_pokemon.raise_for_status()
        data_pokemon = r_pokemon.json()

        # Endpoint de especie — grupos de huevo, ratio género, tasa captura
        r_especie = requests.get(f"{BASE_URL}/pokemon-species/{numero}", timeout=10)
        r_especie.raise_for_status()
        data_especie = r_especie.json()

        # Tipos
        tipos = data_pokemon["types"]
        tipo1 = tipos[0]["type"]["name"]
        tipo2 = tipos[1]["type"]["name"] if len(tipos) > 1 else None

        # Stats base
        stats = {s["stat"]["name"]: s["base_stat"] for s in data_pokemon["stats"]}

        # Grupos de huevo
        grupos = data_especie["egg_groups"]
        grupo1 = grupos[0]["name"] if len(grupos) > 0 else None
        grupo2 = grupos[1]["name"] if len(grupos) > 1 else None

        # Ratio de género: -1 = sin género, si no es % de ser hembra (en octavos)
        gender_rate = data_especie["gender_rate"]
        if gender_rate == -1:
            ratio_genero = -1.0
        else:
            ratio_genero = (gender_rate / 8.0) * 100  # convertimos a porcentaje

        return {
            "numero_pokedex": numero,
            "nombre": data_pokemon["name"],
            "tipo1": tipo1,
            "tipo2": tipo2,
            "hp_base": stats.get("hp", 0),
            "ataque_base": stats.get("attack", 0),
            "defensa_base": stats.get("defense", 0),
            "sp_ataque_base": stats.get("special-attack", 0),
            "sp_defensa_base": stats.get("special-defense", 0),
            "velocidad_base": stats.get("speed", 0),
            "grupo_huevo1": grupo1,
            "grupo_huevo2": grupo2,
            "tasa_huevo": data_especie["hatch_counter"],
            "tasa_captura": data_especie["capture_rate"],
            "ratio_genero": ratio_genero,
            "es_raiz": False,       # lo definirás manualmente después
            "desbloqueada": False,
        }

    except requests.RequestException as e:
        print(f"  ⚠️  Error al obtener #{numero}: {e}")
        return None


def seed():
    db = get_session()

    print(f"🌱 Iniciando importación de {LIMITE} especies desde PokéAPI...")
    print("   (esto puede tardar 2-3 minutos, hay pausas para no saturar la API)\n")

    importados = 0
    errores = 0

    for numero in range(1, LIMITE + 1):
        # Comprobamos si ya existe para poder re-ejecutar el script sin duplicar
        existe = db.query(Especie).filter(Especie.numero_pokedex == numero).first()
        if existe:
            print(f"  ⏭️  #{numero} ya existe, saltando...")
            continue

        print(f"  📥 Importando #{numero}...", end=" ")
        datos = fetch_especie(numero)

        if datos:
            especie = Especie(**datos)
            db.add(especie)
            db.commit()
            print(f"✅ {datos['nombre']}")
            importados += 1
        else:
            errores += 1

        # Pausa pequeña para no saturar PokéAPI (es una API pública y gratuita)
        time.sleep(0.3)

    db.close()
    print(f"\n🎉 Importación completa: {importados} especies añadidas, {errores} errores.")


if __name__ == "__main__":
    seed()