from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from database import get_db
from models import Pokemon, Especie

router = APIRouter(prefix="/pokemon", tags=["Pokemon"])


class PokemonResponse(BaseModel):
    id: int
    especie_id: int
    numero_pokedex: int
    nombre: str
    tipo1: str
    tipo2: Optional[str]
    apodo: Optional[str]
    genero: str
    nivel: int
    experiencia: int
    es_shiny: bool
    naturaleza: Optional[str]
    habilidad: Optional[str]
    amistad: int
    en_guarderia: bool
    iv_hp: int
    iv_ataque: int
    iv_defensa: int
    iv_sp_ataque: int
    iv_sp_defensa: int
    iv_velocidad: int
    ev_hp: int
    ev_ataque: int
    ev_defensa: int
    ev_sp_ataque: int
    ev_sp_defensa: int
    ev_velocidad: int
    padre_id: Optional[int]
    madre_id: Optional[int]

    class Config:
        from_attributes = True


@router.get("/", response_model=list[PokemonResponse])
def listar_pokemon(
    jugador_id: int,
    en_guarderia: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Pokemon, Especie).join(
        Especie, Pokemon.especie_id == Especie.id
    ).filter(Pokemon.jugador_id == jugador_id)

    if en_guarderia is not None:
        query = query.filter(Pokemon.en_guarderia == en_guarderia)

    resultados = query.all()

    response = []
    for pkmn, esp in resultados:
        response.append(PokemonResponse(
            id=pkmn.id,
            especie_id=pkmn.especie_id,
            numero_pokedex=esp.numero_pokedex,
            nombre=esp.nombre,
            tipo1=esp.tipo1,
            tipo2=esp.tipo2,
            apodo=pkmn.apodo,
            genero=pkmn.genero,
            nivel=pkmn.nivel,
            experiencia=pkmn.experiencia,
            es_shiny=pkmn.es_shiny,
            naturaleza=pkmn.naturaleza,
            habilidad=pkmn.habilidad,
            amistad=pkmn.amistad,
            en_guarderia=pkmn.en_guarderia,
            iv_hp=pkmn.iv_hp,
            iv_ataque=pkmn.iv_ataque,
            iv_defensa=pkmn.iv_defensa,
            iv_sp_ataque=pkmn.iv_sp_ataque,
            iv_sp_defensa=pkmn.iv_sp_defensa,
            iv_velocidad=pkmn.iv_velocidad,
            ev_hp=pkmn.ev_hp,
            ev_ataque=pkmn.ev_ataque,
            ev_defensa=pkmn.ev_defensa,
            ev_sp_ataque=pkmn.ev_sp_ataque,
            ev_sp_defensa=pkmn.ev_sp_defensa,
            ev_velocidad=pkmn.ev_velocidad,
            padre_id=pkmn.padre_id,
            madre_id=pkmn.madre_id,
        ))

    return response


@router.get("/{pokemon_id}", response_model=PokemonResponse)
def obtener_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    resultado = db.query(Pokemon, Especie).join(
        Especie, Pokemon.especie_id == Especie.id
    ).filter(Pokemon.id == pokemon_id).first()

    if not resultado:
        raise HTTPException(status_code=404, detail="Pokémon no encontrado")

    pkmn, esp = resultado
    return PokemonResponse(
        id=pkmn.id,
        especie_id=pkmn.especie_id,
        numero_pokedex=esp.numero_pokedex,
        nombre=esp.nombre,
        tipo1=esp.tipo1,
        tipo2=esp.tipo2,
        apodo=pkmn.apodo,
        genero=pkmn.genero,
        nivel=pkmn.nivel,
        experiencia=pkmn.experiencia,
        es_shiny=pkmn.es_shiny,
        naturaleza=pkmn.naturaleza,
        habilidad=pkmn.habilidad,
        amistad=pkmn.amistad,
        en_guarderia=pkmn.en_guarderia,
        iv_hp=pkmn.iv_hp,
        iv_ataque=pkmn.iv_ataque,
        iv_defensa=pkmn.iv_defensa,
        iv_sp_ataque=pkmn.iv_sp_ataque,
        iv_sp_defensa=pkmn.iv_sp_defensa,
        iv_velocidad=pkmn.iv_velocidad,
        ev_hp=pkmn.ev_hp,
        ev_ataque=pkmn.ev_ataque,
        ev_defensa=pkmn.ev_defensa,
        ev_sp_ataque=pkmn.ev_sp_ataque,
        ev_sp_defensa=pkmn.ev_sp_defensa,
        ev_velocidad=pkmn.ev_velocidad,
        padre_id=pkmn.padre_id,
        madre_id=pkmn.madre_id,
    )

@router.delete("/{pokemon_id}")
def eliminar_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    pkmn = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pkmn:
        raise HTTPException(status_code=404, detail="Pokémon no encontrado")
    
    # Evitar borrar Pokémon que son padres de otros
    from models import Pokemon as P
    es_padre = db.query(P).filter(
        (P.padre_id == pokemon_id) | (P.madre_id == pokemon_id)
    ).first()
    if es_padre:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar un Pokémon que es padre de otros"
        )
    
    db.delete(pkmn)
    db.commit()
    return {"mensaje": f"Pokémon #{pokemon_id} eliminado"}