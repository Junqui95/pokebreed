from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Zona, Pokemon, Especie
from game_logic.zona_engine import (
    tick_zona_cria,
    tick_zona_incubacion,
    tick_zona_entrenamiento,
    PASOS_POR_TICK,
    PASOS_PROB_HUEVO
)

router = APIRouter(prefix="/zonas", tags=["Zonas"])


class ZonaResponse(BaseModel):
    id: int
    nombre: str
    tipo_zona: str
    pos_x: int
    pos_y: int
    ancho: int
    alto: int
    huevo_id: Optional[int]
    pokemon_ids: list[int]

    class Config:
        from_attributes = True


class MoverPokemonRequest(BaseModel):
    pokemon_id: int
    zona_id: Optional[int]  # None = fuera de toda zona
    pos_x: int
    pos_y: int


@router.get("/", response_model=list[ZonaResponse])
def listar_zonas(jugador_id: int, db: Session = Depends(get_db)):
    zonas = db.query(Zona).filter(Zona.jugador_id == jugador_id).all()
    result = []
    for zona in zonas:
        pokemon_ids = [
            p.id for p in db.query(Pokemon).filter(
                Pokemon.zona_actual_id == zona.id
            ).all()
        ]
        result.append(ZonaResponse(
            id=zona.id,
            nombre=zona.nombre,
            tipo_zona=zona.tipo_zona,
            pos_x=zona.pos_x,
            pos_y=zona.pos_y,
            ancho=zona.ancho,
            alto=zona.alto,
            huevo_id=zona.huevo_id,
            pokemon_ids=pokemon_ids
        ))
    return result


@router.post("/mover")
def mover_pokemon(req: MoverPokemonRequest, db: Session = Depends(get_db)):
    """Mueve un Pokémon a una zona (o fuera de todas)."""
    pkmn = db.query(Pokemon).filter(Pokemon.id == req.pokemon_id).first()
    if not pkmn:
        raise HTTPException(status_code=404, detail="Pokémon no encontrado")

    pkmn.zona_actual_id = req.zona_id
    pkmn.pos_x          = req.pos_x
    pkmn.pos_y          = req.pos_y
    db.commit()

    return {"mensaje": "Pokémon movido", "pokemon_id": pkmn.id,
            "zona_id": req.zona_id}


@router.post("/tick/{jugador_id}")
def procesar_tick(jugador_id: int, db: Session = Depends(get_db)):
    """
    Procesa un tick para todas las zonas del jugador.
    El frontend llama a este endpoint cada segundo.
    """
    zonas   = db.query(Zona).filter(Zona.jugador_id == jugador_id).all()
    eventos = []

    for zona in zonas:
        if zona.tipo_zona == "cria":
            res = tick_zona_cria(zona, db)
            if res["accion"]:
                eventos.append({"zona": zona.nombre, **res})

        elif zona.tipo_zona == "incubacion":
            eclosionados = tick_zona_incubacion(zona, db)
            for e in eclosionados:
                eventos.append({"zona": zona.nombre,
                                 "accion": "eclosion", "detalle": e})

        elif zona.tipo_zona == "entrenamiento":
            nivel_ups = tick_zona_entrenamiento(zona, db)
            for e in nivel_ups:
                eventos.append({"zona": zona.nombre,
                                 "accion": "nivel_up", "detalle": e})

    return {"tick": True, "eventos": eventos}


@router.get("/{zona_id}/progreso")
def progreso_incubacion(zona_id: int, db: Session = Depends(get_db)):
    """Devuelve el progreso de incubación de cada huevo en la zona."""
    zona = db.query(Zona).filter(Zona.id == zona_id).first()
    if not zona or zona.tipo_zona != "incubacion":
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    huevos = db.query(Pokemon).filter(
        Pokemon.zona_actual_id == zona_id,
        Pokemon.nivel == 1,
        Pokemon.padre_id != None
    ).all()

    result = []
    for huevo in huevos:
        esp = db.query(Especie).filter(Especie.id == huevo.especie_id).first()
        pasos_necesarios = int(((esp.tasa_huevo or 20) * 257) / 10.0)
        progreso = min(100, int(((huevo.experiencia or 0) / pasos_necesarios) * 100))
        result.append({
            "pokemon_id":      huevo.id,
            "especie":         esp.nombre,
            "progreso":        progreso,
            "pasos_actuales":  huevo.experiencia or 0,
            "pasos_necesarios":pasos_necesarios
        })

    return result