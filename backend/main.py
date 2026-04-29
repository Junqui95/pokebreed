from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes import especies, breeding, pokemon, zonas

app = FastAPI(title="Pokebreed API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(especies.router)
app.include_router(breeding.router)
app.include_router(pokemon.router)

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a Pokebreed API"}

@app.get("/health")
def health():
    return {"estado": "ok"}

app.include_router(especies.router)
app.include_router(breeding.router)
app.include_router(pokemon.router)
app.include_router(zonas.router)