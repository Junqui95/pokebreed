from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import Especie
from pydantic import BaseModel

router = APIRouter(prefix="/especies", tags=["Especies"])


# ─────────────────────────────────────────
# SCHEMAS — definen la forma de las respuestas
# ─────────────────────────────────────────
class EspecieResumen(BaseModel):
    """Versión compacta para listar."""
    id: int
    numero_pokedex: int
    nombre: str
    tipo1: str
    tipo2: Optional[str]
    es_raiz: bool
    desbloqueada: bool

    class Config:
        from_attributes = True


class EspecieDetalle(EspecieResumen):
    """Versión completa para el detalle."""
    hp_base: int
    ataque_base: int
    defensa_base: int
    sp_ataque_base: int
    sp_defensa_base: int
    velocidad_base: int
    grupo_huevo1: Optional[str]
    grupo_huevo2: Optional[str]
    tasa_huevo: Optional[int]
    tasa_captura: Optional[int]
    ratio_genero: Optional[float]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────
@router.get("/", response_model=list[EspecieResumen])
def listar_especies(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ej: fire, water)"),
    grupo_huevo: Optional[str] = Query(None, description="Filtrar por grupo de huevo"),
    solo_raiz: bool = Query(False, description="Mostrar solo especies raíz"),
    solo_desbloqueadas: bool = Query(False, description="Mostrar solo desbloqueadas"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Lista especies con filtros opcionales."""
    query = db.query(Especie)

    if tipo:
        query = query.filter(
            (Especie.tipo1 == tipo) | (Especie.tipo2 == tipo)
        )
    if grupo_huevo:
        query = query.filter(
            (Especie.grupo_huevo1 == grupo_huevo) | (Especie.grupo_huevo2 == grupo_huevo)
        )
    if solo_raiz:
        query = query.filter(Especie.es_raiz == True)
    if solo_desbloqueadas:
        query = query.filter(Especie.desbloqueada == True)

    return query.order_by(Especie.numero_pokedex).offset(offset).limit(limit).all()


@router.get("/{especie_id}", response_model=EspecieDetalle)
def obtener_especie(especie_id: int, db: Session = Depends(get_db)):
    """Detalle completo de una especie."""
    especie = db.query(Especie).filter(Especie.id == especie_id).first()
    if not especie:
        raise HTTPException(status_code=404, detail="Especie no encontrada")
    return especie


@router.get("/{especie_id}/compatibles", response_model=list[EspecieResumen])
def especies_compatibles(especie_id: int, db: Session = Depends(get_db)):
    """
    Devuelve qué especies pueden criar con esta.
    Por ahora usa grupos de huevo — más adelante usará el grafo de recetas.
    """
    especie = db.query(Especie).filter(Especie.id == especie_id).first()
    if not especie:
        raise HTTPException(status_code=404, detail="Especie no encontrada")

    grupos = [g for g in [especie.grupo_huevo1, especie.grupo_huevo2] if g]
    if not grupos:
        return []

    compatibles = db.query(Especie).filter(
        (Especie.grupo_huevo1.in_(grupos)) | (Especie.grupo_huevo2.in_(grupos)),
        Especie.id != especie_id
    ).order_by(Especie.numero_pokedex).all()

    return compatibles