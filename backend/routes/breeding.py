from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from game_logic.breeding import realizar_breeding, BreedingError

router = APIRouter(prefix="/breeding", tags=["Breeding"])


class BreedingRequest(BaseModel):
    pokemon1_id: int
    pokemon2_id: int
    jugador_id: int
    zona_tipo: Optional[str] = None
    zona_intensidad: float = 0.0
    destino_nudo: bool = False
    piedraeterna_p1: bool = False
    piedraeterna_p2: bool = False


class BreedingResponse(BaseModel):
    mensaje: str
    especie_resultado: str
    numero_pokedex: int
    genero: str
    es_shiny: bool
    naturaleza: str
    ivs: dict
    pokemon_id: int


@router.post("/", response_model=BreedingResponse)
def breed(request: BreedingRequest, db: Session = Depends(get_db)):
    try:
        huevo = realizar_breeding(
            pokemon1_id=request.pokemon1_id,
            pokemon2_id=request.pokemon2_id,
            jugador_id=request.jugador_id,
            zona_tipo=request.zona_tipo,
            zona_intensidad=request.zona_intensidad,
            destino_nudo=request.destino_nudo,
            piedraeterna_p1=request.piedraeterna_p1,
            piedraeterna_p2=request.piedraeterna_p2,
            db=db
        )

        db.add(huevo)
        db.commit()
        db.refresh(huevo)

        from models import Especie
        especie = db.query(Especie).filter(Especie.id == huevo.especie_id).first()

        return BreedingResponse(
            mensaje="¡Huevo creado con éxito!",
            especie_resultado=especie.nombre,
            numero_pokedex=especie.numero_pokedex,
            genero=huevo.genero,
            es_shiny=huevo.es_shiny,
            naturaleza=huevo.naturaleza,
            ivs={
                "hp":        huevo.iv_hp,
                "ataque":    huevo.iv_ataque,
                "defensa":   huevo.iv_defensa,
                "sp_ataque": huevo.iv_sp_ataque,
                "sp_defensa":huevo.iv_sp_defensa,
                "velocidad": huevo.iv_velocidad,
            },
            pokemon_id=huevo.id
        )

    except BreedingError as e:
        raise HTTPException(status_code=400, detail=str(e))