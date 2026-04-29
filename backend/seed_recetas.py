import json
import os
from database import SessionLocal
from models import Especie, RecetaBreeding, ResultadoBreeding

db = SessionLocal()
DATA_DIR = "../data"


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def get_especie(pokedex):
    return db.query(Especie).filter(Especie.numero_pokedex == pokedex).first()


def upsert_receta(padre1_id, padre2_id, notas, resultados_data, condicion=None):
    """
    Upsert de una receta:
    - Si no existe → la crea
    - Si existe → actualiza notas y sincroniza resultados
    Devuelve 'created', 'updated' o 'unchanged'
    """
    receta = db.query(RecetaBreeding).filter(
        RecetaBreeding.especie_padre1_id == padre1_id,
        RecetaBreeding.especie_padre2_id == padre2_id
    ).first()

    if not receta:
        # Crear
        receta = RecetaBreeding(
            especie_padre1_id=padre1_id,
            especie_padre2_id=padre2_id,
            orden_importa=False,
            notas=notas
        )
        db.add(receta)
        db.flush()
        _insertar_resultados(receta.id, resultados_data, condicion)
        return "created"

    # Actualizar notas si cambiaron
    changed = False
    if receta.notas != notas:
        receta.notas = notas
        changed = True

    # Sincronizar resultados
    resultados_actuales = db.query(ResultadoBreeding).filter(
        ResultadoBreeding.receta_id == receta.id
    ).all()

    # Construir mapa actual: {especie_resultado_id: ResultadoBreeding}
    mapa_actual = {r.especie_resultado_id: r for r in resultados_actuales}

    # Construir mapa deseado: {especie_resultado_id: {probabilidad, condicion}}
    mapa_deseado = {}
    for res in resultados_data:
        especie_res = get_especie(res["pokedex"])
        if especie_res:
            mapa_deseado[especie_res.id] = {
                "probabilidad": res["probabilidad"],
                "condicion": condicion
            }

    # Eliminar resultados que ya no están en el JSON
    for esp_id, resultado in mapa_actual.items():
        if esp_id not in mapa_deseado:
            db.delete(resultado)
            changed = True

    # Insertar o actualizar resultados
    for esp_id, datos in mapa_deseado.items():
        if esp_id in mapa_actual:
            # Actualizar si cambiaron probabilidad o condición
            r = mapa_actual[esp_id]
            if r.probabilidad != datos["probabilidad"] or r.condicion != datos["condicion"]:
                r.probabilidad = datos["probabilidad"]
                r.condicion = datos["condicion"]
                changed = True
        else:
            # Insertar nuevo resultado
            db.add(ResultadoBreeding(
                receta_id=receta.id,
                especie_resultado_id=esp_id,
                probabilidad=datos["probabilidad"],
                condicion=datos["condicion"]
            ))
            changed = True

    return "updated" if changed else "unchanged"


def _insertar_resultados(receta_id, resultados_data, condicion):
    for res in resultados_data:
        especie_res = get_especie(res["pokedex"])
        if not especie_res:
            print(f"   ⚠️  Resultado no encontrado: #{res['pokedex']}")
            continue
        db.add(ResultadoBreeding(
            receta_id=receta_id,
            especie_resultado_id=especie_res.id,
            probabilidad=res["probabilidad"],
            condicion=condicion
        ))


def seed_basicas(legendarios):
    """Upsert de recetas básicas para todas las formas finales no legendarias."""
    print("🌱 Sincronizando recetas básicas...")
    created = updated = unchanged = 0

    formas_finales = db.query(Especie).filter(
        Especie.es_forma_final == True,
        ~Especie.numero_pokedex.in_(legendarios)
    ).all()

    for especie in formas_finales:
        # Remontar hasta la forma base
        forma_base = especie
        visited = set()
        while forma_base.evoluciona_de and forma_base.id not in visited:
            visited.add(forma_base.id)
            padre = db.query(Especie).filter(
                Especie.id == forma_base.evoluciona_de
            ).first()
            if padre:
                forma_base = padre
            else:
                break

        resultados_data = [{"pokedex": forma_base.numero_pokedex, "probabilidad": 1.0}]
        notas = f"{especie.nombre} + {especie.nombre} → {forma_base.nombre}"

        estado = upsert_receta(
            padre1_id=especie.id,
            padre2_id=especie.id,
            notas=notas,
            resultados_data=resultados_data
        )
        if estado == "created":   created += 1
        elif estado == "updated": updated += 1
        else:                     unchanged += 1

    db.commit()
    print(f"   ✅ {created} creadas, {updated} actualizadas, {unchanged} sin cambios")


def seed_cruzadas(legendarios):
    """Upsert de recetas cruzadas desde JSONs."""
    print("🌱 Sincronizando recetas cruzadas...")
    created = updated = unchanged = errores = 0

    for gen in ["gen1", "gen2", "gen3"]:
        ruta = os.path.join(DATA_DIR, gen, "recetas_breeding.json")
        if not os.path.exists(ruta):
            print(f"   ⏭️  No existe aún: {ruta}")
            continue

        datos = cargar_json(ruta)
        for r in datos["recetas"]:
            probabilidad_base = r.get("probabilidad_base", 1.0)
            zona = r.get("zona_requerida")

            resultados_data = [
                {"pokedex": r["resultado_pokedex"], "probabilidad": probabilidad_base}
            ]
            for alt in r.get("resultados_alternativos", []):
                resultados_data.append({
                    "pokedex": alt["resultado_pokedex"],
                    "probabilidad": alt["probabilidad"]
                })

            for combo in r["combinaciones"]:
                padre1 = get_especie(combo["padre1_pokedex"])
                padre2 = get_especie(combo["padre2_pokedex"])

                if not padre1 or not padre2:
                    print(f"   ⚠️  No encontrados: #{combo['padre1_pokedex']} + #{combo['padre2_pokedex']}")
                    errores += 1
                    continue

                estado = upsert_receta(
                    padre1_id=padre1.id,
                    padre2_id=padre2.id,
                    notas=r.get("notas"),
                    resultados_data=resultados_data,
                    condicion=zona
                )
                if estado == "created":   created += 1
                elif estado == "updated": updated += 1
                else:                     unchanged += 1

        db.commit()

    print(f"   ✅ {created} creadas, {updated} actualizadas, {unchanged} sin cambios, {errores} errores")


def seed():
    legendarios = cargar_json(
        os.path.join(DATA_DIR, "legendarios.json")
    )["legendarios"]

    seed_basicas(legendarios)
    seed_cruzadas(legendarios)

    db.close()
    print("\n🎉 Sincronización completa.")
    print("   Para actualizar recetas: edita los JSONs y vuelve a ejecutar este script.")


if __name__ == "__main__":
    seed()