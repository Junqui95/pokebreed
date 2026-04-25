from fastapi import FastAPI
from database import engine
import models

app = FastAPI(title="Pokebreed API")

# Crea las tablas en la base de datos al arrancar
models.Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a Pokebreed API"}

@app.get("/health")
def health():
    return {"estado": "ok"}