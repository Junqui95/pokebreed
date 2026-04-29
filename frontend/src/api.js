const API_BASE = "http://127.0.0.1:8000"
const JUGADOR_ID = 2  // hardcoded por ahora, luego vendrá del login

const API = {

  async getEspecies(limit = 100) {
    const res = await fetch(`${API_BASE}/especies/?limit=${limit}`)
    return res.json()
  },

  async getEspecie(id) {
    const res = await fetch(`${API_BASE}/especies/${id}`)
    return res.json()
  },

  async getPokemon(jugadorId = JUGADOR_ID) {
    const res = await fetch(`${API_BASE}/pokemon/?jugador_id=${jugadorId}`)
    return res.json()
  },

  async realizar_breeding(pokemon1Id, pokemon2Id, zonaId = null) {
    const res = await fetch(`${API_BASE}/breeding/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pokemon1_id: pokemon1Id,
        pokemon2_id: pokemon2Id,
        jugador_id: JUGADOR_ID,
        zona_tipo: zonaId,
        zona_intensidad: 0.0
      })
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "Error en breeding")
    }
    return res.json()
  },

  async eliminarPokemon(pokemonId) {
    const res = await fetch(`${API_BASE}/pokemon/${pokemonId}`, {
      method: "DELETE"
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "Error al eliminar")
    }
    return res.json()
  },

  spriteUrl(numeroPokdex) {
    return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${numeroPokdex}.png`
  },

  async getZonas(jugadorId = JUGADOR_ID) {
    const res = await fetch(`${API_BASE}/zonas/?jugador_id=${jugadorId}`)
    return res.json()
  },

  async tick(jugadorId = JUGADOR_ID) {
    const res = await fetch(`${API_BASE}/zonas/tick/${jugadorId}`, {
      method: "POST"
    })
    return res.json()
  },

  async moverPokemon(pokemonId, zonaId, posX, posY) {
    const res = await fetch(`${API_BASE}/zonas/mover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pokemon_id: pokemonId,
        zona_id:    zonaId,
        pos_x:      Math.round(posX),
        pos_y:      Math.round(posY)
      })
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "Error al mover")
    }
    return res.json()
  },

  async getProgreso(zonaId) {
    const res = await fetch(`${API_BASE}/zonas/${zonaId}/progreso`)
    return res.json()
  },

  eggSpriteUrl() {
    return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/lucky-egg.png"
  }
}