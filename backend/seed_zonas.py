from database import SessionLocal
from models import Jugador, Zona, Pokemon, Especie

db = SessionLocal()

# Jugador
jugador = Jugador(nombre="Ash", dinero=5000)
db.add(jugador)
db.flush()

# Zonas fijas
zonas = [
    Zona(
        nombre="Zona de Cría",
        tipo_zona="cria",
        jugador_id=jugador.id,
        pos_x=12, pos_y=20, ancho=160, alto=130
    ),
    Zona(
        nombre="Zona de Experiencia",
        tipo_zona="entrenamiento",
        jugador_id=jugador.id,
        pos_x=292, pos_y=20, ancho=160, alto=130
    ),
    Zona(
        nombre="Zona de Incubación",
        tipo_zona="incubacion",
        jugador_id=jugador.id,
        pos_x=200, pos_y=260, ancho=160, alto=110
    ),
]
for z in zonas:
    db.add(z)
db.flush()

# Pokémon de prueba
venusaur  = db.query(Especie).filter(Especie.numero_pokedex == 3).first()
charizard = db.query(Especie).filter(Especie.numero_pokedex == 6).first()
blastoise = db.query(Especie).filter(Especie.numero_pokedex == 9).first()

zona_cria = zonas[0]
zona_exp  = zonas[1]

pokemon = [
    Pokemon(especie_id=venusaur.id,  jugador_id=jugador.id, genero="F",
            nivel=50, naturaleza="Bold",
            iv_hp=31, iv_ataque=20, iv_defensa=31,
            iv_sp_ataque=25, iv_sp_defensa=28, iv_velocidad=15,
            zona_actual_id=zona_cria.id, pos_x=70, pos_y=100),
    Pokemon(especie_id=charizard.id, jugador_id=jugador.id, genero="M",
            nivel=50, naturaleza="Adamant",
            iv_hp=15, iv_ataque=31, iv_defensa=20,
            iv_sp_ataque=10, iv_sp_defensa=25, iv_velocidad=31,
            zona_actual_id=zona_cria.id, pos_x=110, pos_y=120),
    Pokemon(especie_id=blastoise.id, jugador_id=jugador.id, genero="M",
            nivel=50, naturaleza="Modest",
            iv_hp=20, iv_ataque=10, iv_defensa=25,
            iv_sp_ataque=31, iv_sp_defensa=31, iv_velocidad=20,
            zona_actual_id=zona_exp.id, pos_x=330, pos_y=100),
]
for p in pokemon:
    db.add(p)

db.commit()
print(f"✅ Jugador id={jugador.id}")
print(f"✅ Zonas: {[z.id for z in zonas]}")
print(f"✅ Pokémon: {[p.id for p in pokemon]}")
db.close()