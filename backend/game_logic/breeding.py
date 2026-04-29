import random
from sqlalchemy.orm import Session
from models import Especie, Pokemon, RecetaBreeding, ResultadoBreeding, Jugador

# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────
PROB_SHINY = 1 / 4096
LEGENDARIOS = {
    144, 145, 146, 150, 151,
    243, 244, 245, 249, 250, 251,
    377, 378, 379, 380, 381, 382, 383, 384, 385, 386
}


# ─────────────────────────────────────────
# 1. VALIDACIÓN
# ─────────────────────────────────────────
class BreedingError(Exception):
    """Error controlado del sistema de breeding."""
    pass


def validar_pareja(pokemon1: Pokemon, pokemon2: Pokemon, db: Session):
    """Valida que dos Pokémon pueden criar juntos."""
    esp1 = db.query(Especie).filter(Especie.id == pokemon1.especie_id).first()
    esp2 = db.query(Especie).filter(Especie.id == pokemon2.especie_id).first()

    # Formas finales
    if not esp1.es_forma_final:
        raise BreedingError(f"{esp1.nombre} no es una forma final y no puede criar.")
    if not esp2.es_forma_final:
        raise BreedingError(f"{esp2.nombre} no es una forma final y no puede criar.")

    # Legendarios
    if esp1.numero_pokedex in LEGENDARIOS:
        raise BreedingError(f"{esp1.nombre} es legendario y no puede criar.")
    if esp2.numero_pokedex in LEGENDARIOS:
        raise BreedingError(f"{esp2.nombre} es legendario y no puede criar.")

    # Géneros compatibles
    es_ditto1 = esp1.numero_pokedex == 132
    es_ditto2 = esp2.numero_pokedex == 132

    if not es_ditto1 and not es_ditto2:
        if pokemon1.genero == "N" or pokemon2.genero == "N":
            raise BreedingError("Pokémon sin género no pueden criar sin Ditto.")
        if pokemon1.genero == pokemon2.genero:
            raise BreedingError("Los dos Pokémon tienen el mismo género.")

    if es_ditto1 and es_ditto2:
        raise BreedingError("Dos Ditto no pueden criar entre sí.")

    return esp1, esp2


# ─────────────────────────────────────────
# 2. BUSCAR RECETA
# ─────────────────────────────────────────
def buscar_receta(esp1: Especie, esp2: Especie, db: Session):
    """
    Busca receta cruzada para esta pareja.
    Prueba ambos órdenes ya que orden_importa=False en la mayoría.
    """
    receta = db.query(RecetaBreeding).filter(
        RecetaBreeding.especie_padre1_id == esp1.id,
        RecetaBreeding.especie_padre2_id == esp2.id
    ).first()

    if not receta:
        receta = db.query(RecetaBreeding).filter(
            RecetaBreeding.especie_padre1_id == esp2.id,
            RecetaBreeding.especie_padre2_id == esp1.id
        ).first()

    return receta


def buscar_receta_basica(esp1: Especie, esp2: Especie, db: Session):
    """
    Si no hay receta cruzada, usa la receta básica.
    Si son la misma especie → receta básica de esa especie.
    Si son distintas → receta básica de la hembra (o del que no es Ditto).
    """
    if esp1.id == esp2.id:
        especie_base = esp1
    elif esp1.numero_pokedex == 132:
        especie_base = esp2
    elif esp2.numero_pokedex == 132:
        especie_base = esp1
    else:
        # Distintas especies sin receta cruzada → usamos la hembra
        especie_base = esp1  # el caller decide el orden

    # Receta básica = especie × misma especie
    receta = db.query(RecetaBreeding).filter(
        RecetaBreeding.especie_padre1_id == especie_base.id,
        RecetaBreeding.especie_padre2_id == especie_base.id
    ).first()

    return receta


# ─────────────────────────────────────────
# 3. CALCULAR RESULTADO
# ─────────────────────────────────────────
def calcular_resultado(
    receta: RecetaBreeding,
    zona_tipo: str | None,
    zona_intensidad: float,
    db: Session
) -> Especie:
    """
    Elige la especie resultado según probabilidades.
    Si hay zona activa, comprueba si algún resultado requiere esa zona.
    """
    resultados = db.query(ResultadoBreeding).filter(
        ResultadoBreeding.receta_id == receta.id
    ).all()

    # Filtrar por zona si es necesario
    candidatos = []
    for r in resultados:
        if r.condicion:
            # Este resultado requiere una zona específica
            if zona_tipo == r.condicion and zona_intensidad >= 1.8:
                candidatos.append(r)
        else:
            candidatos.append(r)

    if not candidatos:
        raise BreedingError("Las condiciones de zona no se cumplen para esta receta.")

    # Tirada de probabilidad
    tirada = random.random()
    acumulado = 0.0
    for candidato in candidatos:
        acumulado += candidato.probabilidad
        if tirada <= acumulado:
            return db.query(Especie).filter(
                Especie.id == candidato.especie_resultado_id
            ).first()

    # Fallback al primero si hay error de redondeo
    return db.query(Especie).filter(
        Especie.id == candidatos[0].especie_resultado_id
    ).first()


# ─────────────────────────────────────────
# 4. HERENCIA DE IVs
# ─────────────────────────────────────────
STATS_IV = ["iv_hp", "iv_ataque", "iv_defensa",
            "iv_sp_ataque", "iv_sp_defensa", "iv_velocidad"]


def calcular_ivs(pokemon1: Pokemon, pokemon2: Pokemon, destino_nudo: bool = False) -> dict:
    """
    Hereda IVs de los padres.
    Sin Destino Nudo: 3 heredados + 3 aleatorios.
    Con Destino Nudo: 5 heredados + 1 aleatorio.
    """
    n_heredados = 5 if destino_nudo else 3
    stats_a_heredar = random.sample(STATS_IV, n_heredados)

    ivs = {}
    for stat in STATS_IV:
        if stat in stats_a_heredar:
            # Heredar de uno de los dos padres aleatoriamente
            padre = random.choice([pokemon1, pokemon2])
            ivs[stat] = getattr(padre, stat)
        else:
            ivs[stat] = random.randint(0, 31)

    return ivs


# ─────────────────────────────────────────
# 5. NATURALEZA
# ─────────────────────────────────────────
NATURALEZAS = [
    "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
    "Bold", "Docile", "Relaxed", "Impish", "Lax",
    "Timid", "Hasty", "Serious", "Jolly", "Naive",
    "Modest", "Mild", "Quiet", "Bashful", "Rash",
    "Calm", "Gentle", "Sassy", "Careful", "Quirky"
]


def calcular_naturaleza(pokemon1: Pokemon, pokemon2: Pokemon,
                         piedraeterna_padre1: bool = False,
                         piedraeterna_padre2: bool = False) -> str:
    """
    Si un padre lleva Piedraeterna hereda su naturaleza.
    Si los dos la llevan, se elige aleatoriamente entre ambas.
    Sin Piedraeterna: naturaleza aleatoria.
    """
    candidatas = []
    if piedraeterna_padre1 and pokemon1.naturaleza:
        candidatas.append(pokemon1.naturaleza)
    if piedraeterna_padre2 and pokemon2.naturaleza:
        candidatas.append(pokemon2.naturaleza)

    if candidatas:
        return random.choice(candidatas)
    return random.choice(NATURALEZAS)


# ─────────────────────────────────────────
# 6. SHINY
# ─────────────────────────────────────────
def calcular_shiny() -> bool:
    return random.random() < PROB_SHINY


# ─────────────────────────────────────────
# 7. GÉNERO
# ─────────────────────────────────────────
def calcular_genero(especie: Especie) -> str:
    """
    ratio_genero = % de ser hembra.
    -1 = sin género.
    """
    if especie.ratio_genero is None or especie.ratio_genero == -1:
        return "N"
    if random.random() * 100 <= especie.ratio_genero:
        return "F"
    return "M"


# ─────────────────────────────────────────
# 8. CREAR HUEVO
# ─────────────────────────────────────────
def crear_huevo(
    especie: Especie,
    ivs: dict,
    naturaleza: str,
    genero: str,
    es_shiny: bool,
    jugador_id: int,
    padre_id: int,
    madre_id: int
) -> Pokemon:
    """Instancia el Pokémon huevo con todos sus atributos calculados."""
    return Pokemon(
        especie_id=especie.id,
        jugador_id=jugador_id,
        genero=genero,
        nivel=1,
        experiencia=0,
        es_shiny=es_shiny,
        naturaleza=naturaleza,
        habilidad=None,  # se asignará al eclosionar
        habilidad_oculta=False,
        padre_id=padre_id,
        madre_id=madre_id,
        en_guarderia=False,
        **ivs
    )


# ─────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────
def realizar_breeding(
    pokemon1_id: int,
    pokemon2_id: int,
    jugador_id: int,
    zona_tipo: str | None = None,
    zona_intensidad: float = 0.0,
    destino_nudo: bool = False,
    piedraeterna_p1: bool = False,
    piedraeterna_p2: bool = False,
    db: Session = None
) -> Pokemon:
    """
    Orquesta todo el proceso de breeding.
    Devuelve el Pokémon huevo resultante (sin guardar en BD todavía).
    """
    # Obtener Pokémon
    pokemon1 = db.query(Pokemon).filter(Pokemon.id == pokemon1_id).first()
    pokemon2 = db.query(Pokemon).filter(Pokemon.id == pokemon2_id).first()

    if not pokemon1 or not pokemon2:
        raise BreedingError("Uno o ambos Pokémon no existen.")

    # 1. Validar
    esp1, esp2 = validar_pareja(pokemon1, pokemon2, db)

    # 2. Buscar receta
    receta = buscar_receta(esp1, esp2, db)
    if not receta:
        receta = buscar_receta_basica(esp1, esp2, db)
    if not receta:
        raise BreedingError(
            f"No existe ninguna receta para {esp1.nombre} + {esp2.nombre}."
        )

    # 3. Calcular resultado
    especie_resultado = calcular_resultado(receta, zona_tipo, zona_intensidad, db)

    # 4. IVs
    ivs = calcular_ivs(pokemon1, pokemon2, destino_nudo)

    # 5. Naturaleza
    naturaleza = calcular_naturaleza(
        pokemon1, pokemon2, piedraeterna_p1, piedraeterna_p2
    )

    # 6. Shiny
    es_shiny = calcular_shiny()

    # 7. Género
    genero = calcular_genero(especie_resultado)

    # 8. Crear huevo
    huevo = crear_huevo(
        especie=especie_resultado,
        ivs=ivs,
        naturaleza=naturaleza,
        genero=genero,
        es_shiny=es_shiny,
        jugador_id=jugador_id,
        padre_id=pokemon1.id,
        madre_id=pokemon2.id
    )

    return huevo