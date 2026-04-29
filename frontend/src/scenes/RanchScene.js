class RanchScene extends Phaser.Scene {
  constructor() {
    super({ key: "RanchScene" })
    this.pokemonList  = []
    this.zonasList    = []
    this.selectedIds  = []
    this.sprites      = {}
    this.zonaRects    = []   // rectángulos de zonas para hit-test
    this.tickInterval = null
    this.dragTarget   = null
  }

  create() {
    const W = this.scale.width
    const H = this.scale.height

    // ── Fondo ─────────────────────────────────────
    this.add.rectangle(0, 0, W, H, 0x3a7a22).setOrigin(0)
    const gfondo = this.add.graphics()
    for (let x = 0; x < W; x += 32) {
      for (let y = 0; y < H; y += 32) {
        if ((x + y) % 64 === 0) {
          gfondo.fillStyle(0x347020, 0.4)
          gfondo.fillRect(x, y, 32, 32)
        }
      }
    }

    // ── Caminos ───────────────────────────────────
    const paths = this.add.graphics()
    paths.fillStyle(0xc0a060, 0.45)
    paths.fillRect(W / 2 - 5, 0, 10, H)
    paths.fillRect(0, H / 2 - 5, W, 10)

    // ── Estanque ──────────────────────────────────
    const pond = this.add.graphics()
    pond.fillStyle(0x2050b0, 0.55)
    pond.fillEllipse(W - 75, 65, 85, 55)
    pond.fillStyle(0x4080e0, 0.25)
    pond.fillEllipse(W - 78, 60, 60, 35)

    // ── Árboles ───────────────────────────────────
    const trees = [[W-28,18],[W-58,8],[12,H-48],[W-18,H-38],[28,H-75]]
      trees.forEach(function(pos) {
        const x = pos[0], y = pos[1]
        this.add.text(x, y, "🌲", { fontSize: "18px" }).setOrigin(0.5)
      }, this)

    // ── Input teclado ─────────────────────────────
    this.input.keyboard.on("keydown-ESC", () => {
      this.selectedIds = []
      this.actualizarSeleccion()
    })

    // ── Cargar datos y arrancar ticks ─────────────
    this.cargarTodo()
  }

  async cargarTodo() {
    try {
      const [pokemon, zonas] = await Promise.all([
        API.getPokemon(JUGADOR_ID),
        API.getZonas(JUGADOR_ID)
      ])
      this.zonasList  = zonas
      this.pokemonList = pokemon

      this.dibujarZonas()
      this.colocarSprites()
      window.actualizarListaPokemon(this.pokemonList)
      window.actualizarZonasUI(this.zonasList)

      // Arrancar loop de ticks
      this.arrancarTicks()

    } catch(e) {
      console.error("Error cargando datos:", e)
      document.getElementById("status-bar").textContent = "Error conectando con la API."
    }
  }

  dibujarZonas() {
    this.zonaRects = []
    const colores = {
      cria:          { borde: 0xd4a030, relleno: 0xd4a030, label: "🥚 CRIANZA",      color: "#f0c060" },
      entrenamiento: { borde: 0x50c050, relleno: 0x50c050, label: "⚡ ENTRENAMIENTO", color: "#80f080" },
      incubacion:    { borde: 0x8040c0, relleno: 0x201040, label: "🔮 INCUBACIÓN",    color: "#a060e0" },
    }

    this.zonasList.forEach(zona => {
      const cfg = colores[zona.tipo_zona] || colores.cria
      const g   = this.add.graphics()

      g.lineStyle(2, cfg.borde, 0.9)
      g.fillStyle(cfg.relleno, 0.12)
      g.strokeRect(zona.pos_x, zona.pos_y, zona.ancho, zona.alto)
      g.fillRect(zona.pos_x, zona.pos_y, zona.ancho, zona.alto)

      this.add.text(
        zona.pos_x + zona.ancho / 2,
        zona.pos_y + 14,
        cfg.label,
        { fontSize: "7px", fontFamily: "'Press Start 2P'", color: cfg.color }
      ).setOrigin(0.5)

      // Guardar rect para hit-test en drag
      this.zonaRects.push({
        id:   zona.id,
        tipo: zona.tipo_zona,
        x:    zona.pos_x,
        y:    zona.pos_y,
        w:    zona.ancho,
        h:    zona.alto
      })
    })
  }

  colocarSprites() {
    this.pokemonList.forEach(pkmn => {
      const x = pkmn.pos_x || 80 + Math.random() * 200
      const y = pkmn.pos_y || 80 + Math.random() * 100
      this.cargarSpritePokemon(pkmn, x, y)
    })
  }

  cargarSpritePokemon(pkmn, x, y) {
    const esHuevo = pkmn.nivel === 1 && pkmn.padre_id !== null
    const key     = `pkmn_${pkmn.numero_pokedex}`
    const url     = API.spriteUrl(pkmn.numero_pokedex)

    if (this.textures.exists(key)) {
      this.crearSprite(pkmn, key, x, y, esHuevo)
    } else {
      this.load.image(key, url)
      this.load.once("complete", () => this.crearSprite(pkmn, key, x, y, esHuevo))
      this.load.start()
    }
  }

  crearSprite(pkmn, key, x, y, esHuevo = false) {
    // Eliminar sprite anterior si existe
    if (this.sprites[pkmn.id]) {
      this.sprites[pkmn.id].destroy()
    }

    const sprite = this.add.image(x, y, key)
      .setScale(esHuevo ? 1.0 : 1.5)
      .setInteractive({ draggable: true, cursor: "pointer" })
      .setData("pokemonId", pkmn.id)
      .setData("esHuevo", esHuevo)

    if (esHuevo) sprite.setTint(0x8888ff)

    // ── Animación idle ────────────────────────────
    const tween = this.tweens.add({
      targets:  sprite,
      y:        y - 4,
      duration: 700 + Math.random() * 600,
      yoyo:     true,
      repeat:   -1,
      ease:     "Sine.easeInOut",
      delay:    Math.random() * 800
    })
    sprite.setData("tween", tween)
    sprite.setData("baseY", y)

    // ── Hover ────────────────────────────────────
    sprite.on("pointerover", () => {
      if (!this.dragTarget) {
        sprite.setTint(esHuevo ? 0xaaaaff : 0xdddddd)
        const gen = pkmn.genero === "F" ? "♀" : pkmn.genero === "M" ? "♂" : ""
        document.getElementById("status-bar").textContent = esHuevo
          ? `🥚 Huevo de ${pkmn.nombre.toUpperCase()} · ${gen} · ${pkmn.naturaleza}`
          : `${pkmn.nombre.toUpperCase()} · Nv.${pkmn.nivel} ${gen} · ${pkmn.naturaleza || ""}`
      }
    })
    sprite.on("pointerout", () => {
      if (!this.selectedIds.includes(pkmn.id) && !this.dragTarget) {
        esHuevo ? sprite.setTint(0x8888ff) : sprite.clearTint()
      }
      document.getElementById("status-bar").textContent = ""
    })

    // ── Click (selección) ─────────────────────────
    sprite.on("pointerdown", () => {
      if (!this.dragTarget) this.seleccionarPokemon(pkmn.id)
    })

    // ── Drag ──────────────────────────────────────
    sprite.on("dragstart", (pointer) => {
      this.dragTarget = pkmn.id
      // Guardar offset entre el centro del sprite y donde se clickó
      sprite.setData("offsetX", sprite.x - pointer.x)
      sprite.setData("offsetY", sprite.y - pointer.y)
      tween.stop()
      sprite.setDepth(10)
      sprite.setScale(esHuevo ? 1.2 : 1.8)
      sprite.setAlpha(0.85)
    })

    sprite.on("drag", (pointer) => {
      sprite.x = pointer.x + sprite.getData("offsetX")
      sprite.y = pointer.y + sprite.getData("offsetY")
    })

    sprite.on("dragend", async (pointer) => {
      const finalX = pointer.x + (sprite.getData("offsetX") || 0)
      const finalY = pointer.y + (sprite.getData("offsetY") || 0)

      this.dragTarget = null
      sprite.setDepth(0)
      sprite.setScale(esHuevo ? 1.0 : 1.5)
      sprite.setAlpha(1)

      // Detectar zona
      const zonaDestino = this.zonaRects.find(z =>
        finalX >= z.x && finalX <= z.x + z.w &&
        finalY >= z.y && finalY <= z.y + z.h
      )

      try {
        await API.moverPokemon(
          pkmn.id,
          zonaDestino ? zonaDestino.id : null,
          Math.round(finalX),
          Math.round(finalY)
        )

        pkmn.pos_x = Math.round(finalX)
        pkmn.pos_y = Math.round(finalY)
        sprite.x   = finalX
        sprite.y   = finalY

        // Crear tween nuevo desde posición final
        const nuevoTween = this.tweens.add({
          targets:  sprite,
          y:        finalY - 4,
          duration: 700 + Math.random() * 600,
          yoyo:     true,
          repeat:   -1,
          ease:     "Sine.easeInOut"
        })
        sprite.setData("tween", nuevoTween)

        const zonaMsg = zonaDestino ? zonaDestino.tipo : "fuera de zona"
        document.getElementById("status-bar").textContent =
          `${pkmn.nombre} movido a ${zonaMsg}`

        const zonas = await API.getZonas(JUGADOR_ID)
        this.zonasList = zonas
        window.actualizarZonasUI(zonas)

      } catch(e) {
        sprite.x = pkmn.pos_x || x
        sprite.y = pkmn.pos_y || y
        this.tweens.add({
          targets:  sprite,
          y:        (pkmn.pos_y || y) - 4,
          duration: 700,
          yoyo:     true,
          repeat:   -1,
          ease:     "Sine.easeInOut"
        })
        document.getElementById("status-bar").textContent = `✗ ${e.message}`
      }
    })

    this.input.setDraggable(sprite)
    this.sprites[pkmn.id] = sprite
  }

  arrancarTicks() {
    if (this.tickInterval) clearInterval(this.tickInterval)

    this.tickInterval = setInterval(async () => {
      try {
        const data = await API.tick(JUGADOR_ID)
        if (data.eventos && data.eventos.length > 0) {
          this.procesarEventos(data.eventos)
        }
      } catch(e) {
        console.error("Error en tick:", e)
      }
    }, 1000) // 1 tick por segundo
  }

  async procesarEventos(eventos) {
    for (const ev of eventos) {
      if (ev.accion === "huevo_generado") {
        const d = ev.detalle
        document.getElementById("status-bar").textContent =
          `🥚 ¡Nuevo huevo en ${ev.zona}! → ${d.especie.toUpperCase()}${d.es_shiny ? " ★" : ""}`

        // Recargar Pokémon para mostrar el huevo
        await this.recargarPokemon()

      } else if (ev.accion === "eclosion") {
        const d = ev.detalle
        document.getElementById("status-bar").textContent =
          `🐣 ¡${d.especie.toUpperCase()} ha eclosionado!${d.es_shiny ? " ★ SHINY" : ""}`
        await this.recargarPokemon()

      } else if (ev.accion === "nivel_up") {
        const d = ev.detalle
        const msg = d.evoluciono
          ? `⬆ ¡${d.nombre} evolucionó a ${d.especie_nueva.toUpperCase()}!`
          : `⬆ ${d.nombre} subió al nivel ${d.nivel_nuevo}`
        document.getElementById("status-bar").textContent = msg
        if (d.evoluciono) await this.recargarPokemon()
      }
    }
  }

  async recargarPokemon() {
    const data = await API.getPokemon(JUGADOR_ID)
    const nuevos = data.filter(p => !this.sprites[p.id])

    // Añadir sprites de Pokémon nuevos
    nuevos.forEach(pkmn => {
      const zona = this.zonasList.find(z => z.id === pkmn.zona_actual_id)
      const x = pkmn.pos_x || (zona ? zona.pos_x + zona.ancho / 2 : 200)
      const y = pkmn.pos_y || (zona ? zona.pos_y + zona.alto  / 2 : 200)
      this.cargarSpritePokemon(pkmn, x, y)
    })

    // Actualizar sprites que evolucionaron
    data.forEach(pkmn => {
      const anterior = this.pokemonList.find(p => p.id === pkmn.id)
      if (anterior && anterior.numero_pokedex !== pkmn.numero_pokedex) {
        const sprite = this.sprites[pkmn.id]
        if (sprite) {
          this.cargarSpritePokemon(pkmn, sprite.x, sprite.y)
        }
      }
    })

    this.pokemonList = data
    window.actualizarListaPokemon(data)
  }

  seleccionarPokemon(id) {
    const idx = this.selectedIds.indexOf(id)
    if (idx !== -1) {
      this.selectedIds.splice(idx, 1)
    } else {
      if (this.selectedIds.length >= 2) {
        const quitado = this.selectedIds.shift()
        if (this.sprites[quitado]) this.sprites[quitado].clearTint()
      }
      this.selectedIds.push(id)
    }
    this.actualizarSeleccion()
  }

  actualizarSeleccion() {
    Object.entries(this.sprites).forEach(([id, sprite]) => {
      const esHuevo = sprite.getData("esHuevo")
      if (this.selectedIds.includes(parseInt(id))) {
        sprite.setTint(0x90ff90)
      } else {
        esHuevo ? sprite.setTint(0x8888ff) : sprite.clearTint()
      }
    })
    window.actualizarSeleccionUI(this.selectedIds, this.pokemonList)
  }

  getSelectedIds() { return this.selectedIds }
  getPokemonList()  { return this.pokemonList }
}