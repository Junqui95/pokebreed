from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Especie(Base):
    """Datos estáticos de cada especie Pokémon (referencia)"""
    __tablename__ = "especies"

    id = Column(Integer, primary_key=True)
    numero_pokedex = Column(Integer, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    tipo1 = Column(String, nullable=False)
    tipo2 = Column(String, nullable=True)
    hp_base = Column(Integer)
    ataque_base = Column(Integer)
    defensa_base = Column(Integer)
    sp_ataque_base = Column(Integer)
    sp_defensa_base = Column(Integer)
    velocidad_base = Column(Integer)

class Pokemon(Base):
    """Instancia concreta de un Pokémon en el rancho del jugador"""
    __tablename__ = "pokemon"

    id = Column(Integer, primary_key=True, index=True)
    especie_id = Column(Integer, ForeignKey("especies.id"), nullable=False)
    nombre = Column(String, nullable=True)
    genero = Column(String, nullable=False)  # "M" o "F"
    nivel = Column(Integer, default=1)
    fecha_nacimiento = Column(DateTime, default=datetime.datetime.utcnow)
    posicion_x = Column(Integer, nullable=True)
    posicion_y = Column(Integer, nullable=True)

    especie = relationship("Especie")