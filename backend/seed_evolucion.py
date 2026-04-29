import json
import os
from database import SessionLocal
from models import Especie, CondicionEvolucion

db = SessionLocal()
DATA_DIR = "../data"


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def seed():
    # ── Formas finales ──────────────────────────────
    print("🌱 Marcando formas finales...")
    count = 0
    for gen in ["gen1", "gen2", "gen3"]:
        ruta = os.path.join(DATA_DIR, gen, "formas_finales.json")
        if not os.path.exists(ruta):
            print(f"   ⚠️  No encontrado: {ruta}")
            continue
        datos = cargar_json(ruta)
        for num in datos["formas_finales"]:
            esp = db.query(Especie).filter(Especie.numero_pokedex == num).first()
            if esp:
                esp.es_forma_final = True
                count += 1
    db.commit()
    print(f"   ✅ {count} formas finales marcadas")

    # ── Especies raíz ───────────────────────────────
    print("🌱 Marcando especies raíz...")
    count = 0
    datos = cargar_json(os.path.join(DATA_DIR, "especies_raiz.json"))
    for item in datos["especies_raiz"]:
        esp = db.query(Especie).filter(
            Especie.numero_pokedex == item["numero_pokedex"]
        ).first()
        if esp:
            esp.es_raiz = True
            esp.metodo_obtencion = "raiz"
            count += 1
    db.commit()
    print(f"   ✅ {count} especies raíz marcadas")

    # ── Condiciones de evolución ────────────────────
    print("🌱 Insertando condiciones de evolución...")
    count = 0
    errores = 0
    for gen in ["gen1", "gen2", "gen3"]:
        ruta = os.path.join(DATA_DIR, gen, "evoluciones.json")
        if not os.path.exists(ruta):
            print(f"   ⚠️  No encontrado: {ruta}")
            continue
        datos = cargar_json(ruta)
        for evo in datos["evoluciones"]:
            origen = db.query(Especie).filter(
                Especie.numero_pokedex == evo["origen_pokedex"]
            ).first()
            destino = db.query(Especie).filter(
                Especie.numero_pokedex == evo["destino_pokedex"]
            ).first()
            if not origen or not destino:
                print(f"   ⚠️  No encontrado: #{evo['origen_pokedex']} → #{evo['destino_pokedex']}")
                errores += 1
                continue
            existe = db.query(CondicionEvolucion).filter(
                CondicionEvolucion.especie_origen_id == origen.id,
                CondicionEvolucion.especie_destino_id == destino.id
            ).first()
            if existe:
                continue
            condicion = CondicionEvolucion(
                especie_origen_id=origen.id,
                especie_destino_id=destino.id,
                tipo_condicion=evo["tipo_condicion"],
                valor_nivel=evo.get("valor_nivel"),
                objeto_requerido=evo.get("objeto_requerido"),
                zona_tipo_requerido=evo.get("zona_tipo_requerido"),
                amistad_minima=evo.get("amistad_minima"),
            )
            db.add(condicion)
            count += 1
    db.commit()
    print(f"   ✅ {count} condiciones insertadas, {errores} errores")

    db.close()
    print("\n🎉 Seed completo.")


if __name__ == "__main__":
    seed()