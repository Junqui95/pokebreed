import random
from sqlalchemy.orm import Session
from models import Zona, Pokemon, Especie
from game_logic.breeding import realizar_breeding, BreedingError

# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────
PASOS_POR_TICK       = 1     # cada tick = 1 paso
PASOS_PROB_HUEVO     = 256   # cada 256 pasos se tira probabilidad de huevo
MULTIPLICADOR_SPEED  = 10.0  # para pruebas — 10x más rápido

# Probabilidades de huevo por compatibilidad (estilo Gen 3)
# Los grupos de huevo compatibles aumentan la probabilidad
PROB_HUEVO_BASE      = 0.20  # 20% cada 256 pasos si son compatibles
PROB_HUEVO_MISMA_ESP = 0.70  # 70% si son de la misma especie


def calcular_compatibilidad(esp1: Especie, esp2: Especie) -> float:
    """
    Devuelve probabilidad base de generar huevo.
    0.0 = incompatibles
    """
    # Ditto es compatible con todo
    if esp1.numero_pokedex == 132 or esp2.numero_pokedex == 132:
        return PROB_HUEVO_BASE

    # Misma especie
    if esp1.id == esp2.id:
        return PROB_HUEVO_MISMA_ESP

    # Grupos de huevo compatibles
    grupos1 = {g for g in [esp1.grupo_huevo1, esp1.grupo_huevo2] if g}
    grupos2 = {g for g in [esp2.grupo_huevo1, esp2.grupo_huevo2] if g}

    if grupos1 & grupos2:  # intersección
        return PROB_HUEVO_BASE

    return 0.0


def tick_zona_cria(zona: Zona, db: Session) -> dict:
    """
    Procesa un tick en una zona de cría.
    Devuelve un dict con lo que ocurrió.
    """
    resultado = {"accion": None, "detalle": None}

    # Obtener Pokémon en la zona
    pokemon_en_zona = db.query(Pokemon).filter(
        Pokemon.zona_actual_id == zona.id,
        Pokemon.padre_id == None,  # solo adultos, no huevos
        Pokemon.nivel > 1
    ).all()

    if len(pokemon_en_zona) != 2:
        return resultado  # necesita exactamente 2

    p1, p2 = pokemon_en_zona
    esp1 = db.query(Especie).filter(Especie.id == p1.especie_id).first()
    esp2 = db.query(Especie).filter(Especie.id == p2.especie_id).first()

    # Verificar géneros
    if p1.genero == p2.genero and 132 not in [esp1.numero_pokedex, esp2.numero_pokedex]:
        return resultado

    # Si ya hay un huevo activo, no generar otro
    if zona.huevo_id:
        huevo = db.query(Pokemon).filter(Pokemon.id == zona.huevo_id).first()
        if huevo:
            return resultado  # huevo sigue ahí
        else:
            zona.huevo_id = None  # el huevo fue retirado

    # Calcular compatibilidad
    prob = calcular_compatibilidad(esp1, esp2)
    if prob == 0.0:
        return resultado

    # Tirada cada PASOS_PROB_HUEVO ticks
    if random.random() < prob:
        try:
            huevo = realizar_breeding(
                pokemon1_id=p1.id,
                pokemon2_id=p2.id,
                jugador_id=zona.jugador_id,
                zona_tipo=zona.tipo_dominante1,
                zona_intensidad=zona.intensidad,
                db=db
            )
            # Posición del huevo en la zona
            huevo.pos_x = zona.pos_x + zona.ancho  // 2
            huevo.pos_y = zona.pos_y + zona.alto   // 2
            huevo.zona_actual_id = zona.id

            db.add(huevo)
            db.flush()
            zona.huevo_id = huevo.id
            db.commit()

            esp_res = db.query(Especie).filter(
                Especie.id == huevo.especie_id
            ).first()
            resultado["accion"]  = "huevo_generado"
            resultado["detalle"] = {
                "huevo_id":    huevo.id,
                "especie":     esp_res.nombre,
                "es_shiny":    huevo.es_shiny,
                "naturaleza":  huevo.naturaleza,
            }
        except BreedingError as e:
            resultado["accion"]  = "error"
            resultado["detalle"] = str(e)

    return resultado


def tick_zona_incubacion(zona: Zona, db: Session) -> list:
    """
    Procesa un tick en la zona de incubación.
    Devuelve lista de huevos eclosionados.
    """
    eclosionados = []

    huevos = db.query(Pokemon).filter(
        Pokemon.zona_actual_id == zona.id,
        Pokemon.nivel == 1,
        Pokemon.padre_id != None
    ).all()

    for huevo in huevos:
        especie = db.query(Especie).filter(
            Especie.id == huevo.especie_id
        ).first()

        # Pasos necesarios = tasa_huevo * 257 (fórmula Gen 3)
        pasos_necesarios = (especie.tasa_huevo or 20) * 257
        # Ajustar por multiplicador de velocidad
        pasos_necesarios = int(pasos_necesarios / MULTIPLICADOR_SPEED)

        # Usamos experiencia para contar ticks de incubación
        huevo.experiencia = (huevo.experiencia or 0) + PASOS_POR_TICK

        if huevo.experiencia >= pasos_necesarios:
            # ¡Eclosiona!
            huevo.nivel       = 1
            huevo.experiencia = 0
            # Lo movemos fuera de la zona de incubación
            huevo.zona_actual_id = None
            db.commit()
            eclosionados.append({
                "pokemon_id": huevo.id,
                "especie":    especie.nombre,
                "es_shiny":   huevo.es_shiny,
                "progreso":   100
            })
        else:
            db.commit()

    return eclosionados


def tick_zona_entrenamiento(zona: Zona, db: Session) -> list:
    """
    Procesa un tick en la zona de entrenamiento.
    Devuelve lista de Pokémon que subieron de nivel o evolucionaron.
    """
    from models import CondicionEvolucion
    eventos = []

    pokemon_en_zona = db.query(Pokemon).filter(
        Pokemon.zona_actual_id == zona.id,
        Pokemon.nivel > 0,
        Pokemon.padre_id == None  # solo adultos
    ).all()

    for pkmn in pokemon_en_zona:
        especie = db.query(Especie).filter(
            Especie.id == pkmn.especie_id
        ).first()

        # +1 XP por tick
        pkmn.experiencia = (pkmn.experiencia or 0) + 1

        # XP necesaria para subir de nivel (fórmula simplificada)
        xp_necesaria = _xp_para_nivel(pkmn.nivel + 1)

        if pkmn.experiencia >= xp_necesaria:
            pkmn.nivel      += 1
            pkmn.experiencia = 0
            db.commit()

            evento = {
                "pokemon_id": pkmn.id,
                "nombre":     especie.nombre,
                "nivel_nuevo": pkmn.nivel,
                "evoluciono": False,
                "especie_nueva": None
            }

            # Comprobar evolución por nivel
            condicion = db.query(CondicionEvolucion).filter(
                CondicionEvolucion.especie_origen_id == pkmn.especie_id,
                CondicionEvolucion.tipo_condicion    == "nivel",
                CondicionEvolucion.valor_nivel       <= pkmn.nivel
            ).first()

            if condicion:
                esp_nueva = db.query(Especie).filter(
                    Especie.id == condicion.especie_destino_id
                ).first()
                pkmn.especie_id = esp_nueva.id
                db.commit()
                evento["evoluciono"]    = True
                evento["especie_nueva"] = esp_nueva.nombre

            eventos.append(evento)

    return eventos


def _xp_para_nivel(nivel: int) -> int:
    """
    XP necesaria para alcanzar un nivel.
    Usamos curva 'medium fast' simplificada: nivel^3
    """
    return nivel ** 3