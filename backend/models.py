from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime


class Especie(Base):
    __tablename__ = "especies"

    id               = Column(Integer, primary_key=True, index=True)
    numero_pokedex   = Column(Integer, unique=True, nullable=False)
    nombre           = Column(String, nullable=False)
    tipo1            = Column(String, nullable=False)
    tipo2            = Column(String, nullable=True)

    # Stats base
    hp_base          = Column(Integer)
    ataque_base      = Column(Integer)
    defensa_base     = Column(Integer)
    sp_ataque_base   = Column(Integer)
    sp_defensa_base  = Column(Integer)
    velocidad_base   = Column(Integer)

    # Breeding
    grupo_huevo1     = Column(String, nullable=True)
    grupo_huevo2     = Column(String, nullable=True)
    tasa_huevo       = Column(Integer, nullable=True)
    tasa_captura     = Column(Integer, nullable=True)
    ratio_genero     = Column(Float, nullable=True)

    # Sistema propio
    es_raiz          = Column(Boolean, default=False)
    desbloqueada     = Column(Boolean, default=False)
    es_forma_final   = Column(Boolean, default=False)  # NUEVO — solo formas finales crían

    # NUEVO — cómo se obtiene esta especie
    # "raiz"      → especie inicial
    # "breeding"  → resultado de RecetaBreeding
    # "evolucion" → sube de nivel u otra condición
    # "objeto"    → piedra u objeto especial
    # "mutacion"  → breeding + zona de crianza
    metodo_obtencion = Column(String, default="evolucion")  # NUEVO

    # Evolución
    evoluciona_de    = Column(Integer, ForeignKey("especies.id"), nullable=True)

    # Relaciones
    instancias            = relationship("Pokemon", back_populates="especie")
    como_padre1           = relationship("RecetaBreeding",
                                         foreign_keys="RecetaBreeding.especie_padre1_id",
                                         back_populates="padre1")
    como_padre2           = relationship("RecetaBreeding",
                                         foreign_keys="RecetaBreeding.especie_padre2_id",
                                         back_populates="padre2")
    evoluciones_desde_aqui = relationship("CondicionEvolucion",  # NUEVO
                                          foreign_keys="CondicionEvolucion.especie_origen_id",
                                          back_populates="especie_origen")


class CondicionEvolucion(Base):  # NUEVO — tabla completa
    __tablename__ = "condiciones_evolucion"

    id                    = Column(Integer, primary_key=True, index=True)
    especie_origen_id     = Column(Integer, ForeignKey("especies.id"), nullable=False)
    especie_destino_id    = Column(Integer, ForeignKey("especies.id"), nullable=False)

    # Tipo de condición: "nivel", "objeto", "amistad", "zona"
    tipo_condicion        = Column(String, nullable=False)

    # Valores según el tipo (solo se usa el relevante para cada caso)
    valor_nivel           = Column(Integer, nullable=True)   # tipo "nivel"
    objeto_requerido      = Column(String, nullable=True)    # tipo "objeto" ej: "piedra-hoja"
    zona_tipo_requerido   = Column(String, nullable=True)    # tipo "zona"  ej: "psychic"
    amistad_minima        = Column(Integer, nullable=True)   # tipo "amistad" 0-255

    # Relaciones
    especie_origen        = relationship("Especie",
                                         foreign_keys=[especie_origen_id],
                                         back_populates="evoluciones_desde_aqui")
    especie_destino       = relationship("Especie",
                                         foreign_keys=[especie_destino_id])


class RecetaBreeding(Base):
    __tablename__ = "recetas_breeding"

    id                  = Column(Integer, primary_key=True, index=True)
    especie_padre1_id   = Column(Integer, ForeignKey("especies.id"), nullable=False)
    especie_padre2_id   = Column(Integer, ForeignKey("especies.id"), nullable=False)
    orden_importa       = Column(Boolean, default=False)
    notas               = Column(String, nullable=True)

    padre1              = relationship("Especie",
                                       foreign_keys=[especie_padre1_id],
                                       back_populates="como_padre1")
    padre2              = relationship("Especie",
                                       foreign_keys=[especie_padre2_id],
                                       back_populates="como_padre2")
    resultados          = relationship("ResultadoBreeding", back_populates="receta")


class ResultadoBreeding(Base):
    __tablename__ = "resultados_breeding"

    id                    = Column(Integer, primary_key=True, index=True)
    receta_id             = Column(Integer, ForeignKey("recetas_breeding.id"), nullable=False)
    especie_resultado_id  = Column(Integer, ForeignKey("especies.id"), nullable=False)
    probabilidad          = Column(Float, nullable=False)
    condicion             = Column(String, nullable=True)

    receta                = relationship("RecetaBreeding", back_populates="resultados")
    especie_resultado      = relationship("Especie")


class Jugador(Base):
    __tablename__ = "jugadores"

    id               = Column(Integer, primary_key=True, index=True)
    nombre           = Column(String, nullable=False)
    dinero           = Column(Integer, default=1000)
    fecha_creacion   = Column(DateTime, default=datetime.datetime.utcnow)

    pokemon          = relationship("Pokemon", back_populates="jugador")


class Pokemon(Base):
    __tablename__ = "pokemon"

    id               = Column(Integer, primary_key=True, index=True)
    especie_id       = Column(Integer, ForeignKey("especies.id"), nullable=False)
    jugador_id       = Column(Integer, ForeignKey("jugadores.id"), nullable=True)

    # NUEVO — posición visual en el mapa
    pos_x            = Column(Integer, nullable=True)
    pos_y            = Column(Integer, nullable=True)
    zona_actual_id   = Column(Integer, ForeignKey("zonas.id"), nullable=True)

    apodo            = Column(String, nullable=True)
    genero           = Column(String, nullable=False)
    nivel            = Column(Integer, default=1)
    experiencia      = Column(Integer, default=0)
    es_shiny         = Column(Boolean, default=False)
    fecha_nacimiento = Column(DateTime, default=datetime.datetime.utcnow)

    naturaleza       = Column(String, nullable=True)
    habilidad        = Column(String, nullable=True)
    habilidad_oculta = Column(Boolean, default=False)

    # Amistad (0-255) — NUEVO campo relevante para evoluciones
    amistad          = Column(Integer, default=70)

    # IVs
    iv_hp            = Column(Integer, default=0)
    iv_ataque        = Column(Integer, default=0)
    iv_defensa       = Column(Integer, default=0)
    iv_sp_ataque     = Column(Integer, default=0)
    iv_sp_defensa    = Column(Integer, default=0)
    iv_velocidad     = Column(Integer, default=0)

    # EVs
    ev_hp            = Column(Integer, default=0)
    ev_ataque        = Column(Integer, default=0)
    ev_defensa       = Column(Integer, default=0)
    ev_sp_ataque     = Column(Integer, default=0)
    ev_sp_defensa    = Column(Integer, default=0)
    ev_velocidad     = Column(Integer, default=0)

    # Breeding
    en_guarderia     = Column(Boolean, default=False)
    padre_id         = Column(Integer, ForeignKey("pokemon.id"), nullable=True)
    madre_id         = Column(Integer, ForeignKey("pokemon.id"), nullable=True)

    # Zona actual — NUEVO
    zona_actual = relationship(
        "Zona",
        foreign_keys="Pokemon.zona_actual_id",
        back_populates="pokemon"
    )

    # Relaciones
    especie          = relationship("Especie", back_populates="instancias")
    jugador          = relationship("Jugador", back_populates="pokemon")
    movimientos      = relationship("PokemonMovimiento", back_populates="pokemon")


class Zona(Base):
    __tablename__ = "zonas"

    id               = Column(Integer, primary_key=True, index=True)
    nombre           = Column(String, nullable=False)
    tipo_zona        = Column(String, nullable=False)  # "cria", "incubacion", "entrenamiento"
    tipo_dominante1  = Column(String, nullable=True)
    tipo_dominante2  = Column(String, nullable=True)
    intensidad       = Column(Float, default=1.0)
    jugador_id       = Column(Integer, ForeignKey("jugadores.id"), nullable=True)

    # NUEVO — posición y tamaño en el mapa (para cuando implementemos tiles)
    pos_x            = Column(Integer, default=0)
    pos_y            = Column(Integer, default=0)
    ancho            = Column(Integer, default=160)
    alto             = Column(Integer, default=130)

    # NUEVO — huevo activo en zona de cría
    huevo_id = Column(Integer, ForeignKey("pokemon.id", use_alter=True, name="fk_zona_huevo"), nullable=True)

    pokemon = relationship(
        "Pokemon",
        foreign_keys="[Pokemon.zona_actual_id]",
        back_populates="zona_actual"
    )
    huevo = relationship(
        "Pokemon",
        foreign_keys=[huevo_id],
        post_update=True
    )


class Movimiento(Base):
    __tablename__ = "movimientos"

    id               = Column(Integer, primary_key=True, index=True)
    nombre           = Column(String, nullable=False, unique=True)
    tipo             = Column(String, nullable=False)
    categoria        = Column(String, nullable=False)
    potencia         = Column(Integer, nullable=True)
    precision        = Column(Integer, nullable=True)
    pp               = Column(Integer, nullable=False)


class PokemonMovimiento(Base):
    __tablename__ = "pokemon_movimientos"

    id               = Column(Integer, primary_key=True, index=True)
    pokemon_id       = Column(Integer, ForeignKey("pokemon.id"), nullable=False)
    movimiento_id    = Column(Integer, ForeignKey("movimientos.id"), nullable=False)
    pp_actuales      = Column(Integer, nullable=False)
    slot             = Column(Integer, nullable=False)

    pokemon          = relationship("Pokemon", back_populates="movimientos")
    movimiento       = relationship("Movimiento")