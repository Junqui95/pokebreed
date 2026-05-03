class RanchScene extends Phaser.Scene {
  constructor() {
    super({ key: "RanchScene" })
    this.pokemonList  = []
    this.zonasList    = []
    this.selectedIds  = []
    this.sprites      = {}
    this.zonaRects    = []
    this.dragTarget   = null
    this.mapaData     = null
    this.TILE         = 32
    this.TILE_SRC     = 16
    this.TILESET_COLS = 8
  }

  create() {
    this.mapaData = this.cache.json.get("mapa")
    this.dibujarMapa()
    this.input.keyboard.on("keydown-ESC", () => {
      this.selectedIds = []
      this.actualizarSeleccion()
    })
    this.cargarTodo()
  }

  // ── Dibujar mapa de tiles ──────────────────────
  dibujarMapa() {
    const mapa    = this.mapaData
    const leyenda = mapa.leyenda
    const TILE    = this.TILE
    const SRC     = this.TILE_SRC

    const tileCoords = {
      "hierba":   mapa.tiles.hierba,
      "tierra":   mapa.tiles.tierra,
      "arena":    mapa.tiles.arena,
      "hierba_c": mapa.tiles["hierba_c"],
      "valla_vL": mapa.tiles["valla_vL"],
      "valla_vR": mapa.tiles["valla_vR"],
      "valla_TL": mapa.tiles["valla_TL"],
      "valla_hT": mapa.tiles["valla_hT"],
      "valla_TR": mapa.tiles["valla_TR"],
      "valla_BL": mapa.tiles["valla_BL"],
      "valla_BR": mapa.tiles["valla_BR"],
    }

    // Crear un frame por cada tile único necesario
    const tileset = this.textures.get("tileset")
    const usados  = new Set()

    mapa.mapa.forEach(fila => {
      fila.forEach(tileId => {
        const tipo   = leyenda[String(tileId)] || "hierba"
        const coords = tileCoords[tipo] || tileCoords["hierba"]
        const frameKey = `${coords[0]}_${coords[1]}`
        if (!usados.has(frameKey)) {
          usados.add(frameKey)
          // Añadir frame al tileset si no existe
          if (!tileset.has(frameKey)) {
            tileset.add(
              frameKey,
              0,
              coords[1] * SRC,  // x en el tileset (columna * SRC)
              coords[0] * SRC,  // y en el tileset (fila * SRC)
              SRC,
              SRC
            )
          }
        }
      })
    })

    // Renderizar cada tile
    mapa.mapa.forEach((fila, r) => {
      fila.forEach((tileId, c) => {
        const tipo     = leyenda[String(tileId)] || "hierba"
        const coords   = tileCoords[tipo] || tileCoords["hierba"]
        const frameKey = `${coords[0]}_${coords[1]}`

        this.add.image(c * TILE + TILE / 2, r * TILE + TILE / 2, "tileset", frameKey)
          .setDisplaySize(TILE, TILE)
      })
    })

    // Calcular zonaRects
    this.zonaRects = []
    Object.entries(mapa.zonas).forEach(([nombre, zona]) => {
      this.zonaRects.push({
        nombre,
        tipo:  zona.tipo,
        x:     zona.col_inicio * TILE,
        y:     zona.fila_inicio * TILE,
        w:     (zona.col_fin - zona.col_inicio + 1) * TILE,
        h:     (zona.fila_fin - zona.fila_inicio + 1) * TILE,
        tiles: this._getTilesDeZona(zona)
      })
    })

    // Tiles bloqueados
    this.tilesBlocking = new Set()
    mapa.mapa.forEach((fila, r) => {
      fila.forEach((tileId, c) => {
        if ([10,11,12,13,14,15,16].includes(tileId)) {
          this.tilesBlocking.add(`${c},${r}`)
        }
      })
    })
  }

  _getTilesDeZona(zona) {
    const tiles = []
    for (let r = zona.fila_inicio + 1; r < zona.fila_fin; r++) {
      for (let c = zona.col_inicio + 1; c < zona.col_fin; c++) {
        tiles.push({ col: c, fila: r })
      }
    }
    return tiles
  }

  // ── Cargar datos de la API ─────────────────────
  async cargarTodo() {
    try {
      const [pokemon, zonas] = await Promise.all([
        API.getPokemon(JUGADOR_ID),
        API.getZonas(JUGADOR_ID)
      ])
      this.zonasList   = zonas
      this.pokemonList = pokemon

      // Sincronizar zonaRects con IDs reales de la API
      this.zonasList.forEach(zona => {
        const rect = this.zonaRects.find(r => r.tipo === zona.tipo_zona)
        if (rect) rect.id = zona.id
      })

      this.colocarSprites()
      window.actualizarListaPokemon && window.actualizarListaPokemon(this.pokemonList)
      window.actualizarZonasUI      && window.actualizarZonasUI(this.zonasList)
      this.arrancarTicks()

    } catch(e) {
      console.error("Error:", e)
      document.getElementById("status-bar").textContent =
        "Error conectando con la API."
    }
  }

  // ── Colocar sprites en el mapa ─────────────────
  colocarSprites() {
    this.pokemonList.forEach(pkmn => {
      // Convertir pos_x/pos_y (px) a tile, o asignar tile libre
      let tileCol, tileFila
      if (pkmn.pos_x && pkmn.pos_y) {
        tileCol  = Math.floor(pkmn.pos_x / this.TILE)
        tileFila = Math.floor(pkmn.pos_y / this.TILE)
      } else {
        // Buscar tile libre en zona correspondiente
        const zona  = this.zonasList.find(z => z.id === pkmn.zona_actual_id)
        const rect  = this.zonaRects.find(r => zona && r.tipo === zona.tipo_zona)
        const libre = rect ? this._tileLibre(rect) : { col: 2, fila: 2 }
        tileCol  = libre.col
        tileFila = libre.fila
      }
      this.cargarSpritePokemon(pkmn, tileCol, tileFila)
    })
  }

  _tileLibre(rect) {
    const ocupados = new Set(
      Object.values(this.sprites).map(s => {
        const c = Math.floor(s.x / this.TILE)
        const f = Math.floor(s.y / this.TILE)
        return `${c},${f}`
      })
    )
    for (const t of rect.tiles) {
      if (!ocupados.has(`${t.col},${t.fila}`)) return t
    }
    return rect.tiles[0] || { col: 2, fila: 2 }
  }

  // ── Sprites PMD ────────────────────────────────
  cargarSpritePokemon(pkmn, tileCol, tileFila) {
    console.log(`Cargando sprite para ${pkmn.nombre} en tile ${tileCol},${tileFila}`)
    const esHuevo = pkmn.nivel === 1 && pkmn.padre_id !== null
    const num     = pkmn.numero_pokedex
    const key     = `pmd_${num}`
    const url     = `assets/sprites/pokemon/${num}/Walk-Anim.png`
    const fallback= `assets/sprites/pokemon/0/Walk-Anim.png`

    const onCreate = () => this.crearSprite(pkmn, key, tileCol, tileFila, esHuevo)

    if (this.textures.exists(key)) {
      onCreate()
    } else {
      this.load.image(key, url)
      this.load.once("complete", onCreate)
      this.load.once("loaderror", () => {
        if (!this.textures.exists(key)) {
          this.load.image(key, fallback)
          this.load.once("complete", onCreate)
          this.load.start()
        }
      })
      this.load.start()
    }
  }

  crearSprite(pkmn, key, tileCol, tileFila, esHuevo = false) {
    if (this.sprites[pkmn.id]) this.sprites[pkmn.id].destroy()

    const TILE = this.TILE
    const x    = tileCol  * TILE + TILE / 2
    const y    = tileFila * TILE + TILE / 2

    // Dimensiones exactas del frame PMD
    const CELL_W   = 30   // celda total incluyendo padding
    const CELL_H   = 40

    if (!textura.has("sur_0")) {
      textura.add("sur_0", 0, 0, 0, CELL_W, CELL_H)
    }

    // Los huevos usan sprite de Chikorita con tint azul por ahora
    // En el futuro tendrán sprite propio
    const sprite = this.add.image(x, y, key, "sur_0")
      .setOrigin(0.5)
      .setDisplaySize(TILE, TILE)
      .setInteractive(
        new Phaser.Geom.Rectangle(0, 0, CELL_W, CELL_H),
        Phaser.Geom.Rectangle.Contains
      )
      this.input.setDraggable(sprite)
      .setData("pokemonId", pkmn.id)
      .setData("tileCol",   tileCol)
      .setData("tileFila",  tileFila)
      .setData("esHuevo",   esHuevo)

    if (esHuevo) sprite.setTint(0x6699ff)

    // Animación idle
    this.tweens.add({
      targets:  sprite,
      y:        y - 3,
      duration: 600 + Math.random() * 400,
      yoyo:     true,
      repeat:   -1,
      ease:     "Sine.easeInOut",
      delay:    Math.random() * 500
    })

    sprite.on("pointerover", () => {
      sprite.setTint(esHuevo ? 0xaaaaff : 0xdddddd)
      const gen = pkmn.genero === "F" ? "♀" : "♂"
      document.getElementById("status-bar").textContent = esHuevo
        ? `🥚 Huevo de ${pkmn.nombre.toUpperCase()} · ${gen}`
        : `${pkmn.nombre.toUpperCase()} · Nv.${pkmn.nivel} ${gen} · ${pkmn.naturaleza || ""}`
    })
    sprite.on("pointerout", () => {
      if (!this.selectedIds.includes(pkmn.id))
        esHuevo ? sprite.setTint(0x6699ff) : sprite.clearTint()
      document.getElementById("status-bar").textContent = ""
    })
    sprite.on("pointerdown", () => {
      if (!this.dragTarget) this.seleccionarPokemon(pkmn.id)
    })

    // Drag
    sprite.on("dragstart", () => {
      this.dragTarget = pkmn.id
      this.tweens.killTweensOf(sprite)
      sprite.setDepth(10)
      sprite.setAlpha(0.85)
    })
    sprite.on("drag", (pointer) => {
      sprite.x = pointer.x
      sprite.y = pointer.y
    })
    sprite.on("dragend", async (pointer) => {
      this.dragTarget = null
      sprite.setDepth(0)
      sprite.setAlpha(1)

      const snapCol   = Math.round((pointer.x - TILE / 2) / TILE)
      const snapFila  = Math.round((pointer.y - TILE / 2) / TILE)
      const clampCol  = Math.max(0, Math.min(this.mapaData.ancho - 1, snapCol))
      const clampFila = Math.max(0, Math.min(this.mapaData.alto  - 1, snapFila))

      if (this.tilesBlocking.has(`${clampCol},${clampFila}`)) {
        sprite.x = sprite.getData("tileCol")  * TILE + TILE / 2
        sprite.y = sprite.getData("tileFila") * TILE + TILE / 2
        document.getElementById("status-bar").textContent = "No puedes colocar un Pokémon en una valla"
        this._reanudarTween(sprite)
        return
      }

      const finalX = clampCol  * TILE + TILE / 2
      const finalY = clampFila * TILE + TILE / 2
      const zonaDestino = this.zonaRects.find(z =>
        finalX >= z.x && finalX < z.x + z.w &&
        finalY >= z.y && finalY < z.y + z.h
      )

      sprite.x = finalX
      sprite.y = finalY
      sprite.setData("tileCol",  clampCol)
      sprite.setData("tileFila", clampFila)
      this._reanudarTween(sprite)

      try {
        await API.moverPokemon(
          pkmn.id,
          zonaDestino?.id || null,
          clampCol * TILE,
          clampFila * TILE
        )
        pkmn.pos_x = clampCol  * TILE
        pkmn.pos_y = clampFila * TILE

        document.getElementById("status-bar").textContent =
          zonaDestino
            ? `${pkmn.nombre} → zona ${zonaDestino.tipo}`
            : `${pkmn.nombre} → fuera de zona`

        const zonas = await API.getZonas(JUGADOR_ID)
        this.zonasList = zonas
        window.actualizarZonasUI && window.actualizarZonasUI(zonas)

      } catch(e) {
        sprite.x = sprite.getData("tileCol")  * TILE + TILE / 2
        sprite.y = sprite.getData("tileFila") * TILE + TILE / 2
        document.getElementById("status-bar").textContent = `✗ ${e.message}`
      }
    })

    this.input.setDraggable(sprite)
    this.sprites[pkmn.id] = sprite
  }

  _reanudarTween(sprite) {
    const y = sprite.y
    this.tweens.add({
      targets:  sprite,
      y:        y - 3,
      duration: 600 + Math.random() * 400,
      yoyo:     true,
      repeat:   -1,
      ease:     "Sine.easeInOut"
    })
  }

  // ── Ticks ──────────────────────────────────────
  arrancarTicks() {
    if (this.tickInterval) clearInterval(this.tickInterval)
    this.tickInterval = setInterval(async () => {
      try {
        const data = await API.tick(JUGADOR_ID)
        if (data.eventos?.length > 0) this.procesarEventos(data.eventos)
      } catch(e) { console.error("Tick error:", e) }
    }, 1000)
  }

  async procesarEventos(eventos) {
    for (const ev of eventos) {
      if (ev.accion === "huevo_generado") {
        document.getElementById("status-bar").textContent =
          `🥚 ¡Huevo de ${ev.detalle.especie}!${ev.detalle.es_shiny ? " ★" : ""}`
        await this.recargarPokemon()
      } else if (ev.accion === "eclosion") {
        document.getElementById("status-bar").textContent =
          `🐣 ¡${ev.detalle.especie} ha eclosionado!`
        await this.recargarPokemon()
      } else if (ev.accion === "nivel_up") {
        const d = ev.detalle
        document.getElementById("status-bar").textContent = d.evoluciono
          ? `⬆ ¡${d.nombre} → ${d.especie_nueva}!`
          : `⬆ ${d.nombre} Nv.${d.nivel_nuevo}`
        if (d.evoluciono) await this.recargarPokemon()
      }
    }
  }

  async recargarPokemon() {
    const data = await API.getPokemon(JUGADOR_ID)
    data.filter(p => !this.sprites[p.id]).forEach(pkmn => {
      const tileCol  = pkmn.pos_x ? Math.floor(pkmn.pos_x / this.TILE) : 2
      const tileFila = pkmn.pos_y ? Math.floor(pkmn.pos_y / this.TILE) : 2
      this.cargarSpritePokemon(pkmn, tileCol, tileFila)
    })
    this.pokemonList = data
    window.actualizarListaPokemon && window.actualizarListaPokemon(data)
  }

  seleccionarPokemon(id) {
    const idx = this.selectedIds.indexOf(id)
    if (idx !== -1) {
      this.selectedIds.splice(idx, 1)
    } else {
      if (this.selectedIds.length >= 2) {
        const q = this.selectedIds.shift()
        if (this.sprites[q]) this.sprites[q].clearTint()
      }
      this.selectedIds.push(id)
    }
    this.actualizarSeleccion()
  }

  actualizarSeleccion() {
    Object.entries(this.sprites).forEach(([id, sprite]) => {
      const esHuevo = sprite.getData("esHuevo")
      this.selectedIds.includes(parseInt(id))
        ? sprite.setTint(0x90ff90)
        : esHuevo ? sprite.setTint(0x8888ff) : sprite.clearTint()
    })
    window.actualizarSeleccionUI && window.actualizarSeleccionUI(this.selectedIds, this.pokemonList)
  }

  getSelectedIds() { return this.selectedIds }
  getPokemonList()  { return this.pokemonList }
}