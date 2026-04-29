function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"))
  event.target.classList.add("active")
  document.getElementById("pokemon-list").style.display = tab === "pokemon" ? "" : "none"
  document.getElementById("huevos-list").style.display  = tab === "huevos"  ? "" : "none"
  document.getElementById("zonas-list").style.display   = tab === "zonas"   ? "" : "none"
}

function actualizarListaPokemon(pokemonList) {
  const lista = document.getElementById("pokemon-list")
  lista.innerHTML = ""

  // Separar originales (sin padre) de criados
  const originales = pokemonList.filter(p => p.padre_id === null)
  const criados    = pokemonList.filter(p => p.padre_id !== null)

  const grupos = []
  if (originales.length) grupos.push({ titulo: "── Rancho ──", items: originales })
  if (criados.length)    grupos.push({ titulo: "── Criados ──", items: criados })

  grupos.forEach(grupo => {
    const sep = document.createElement("div")
    sep.style.cssText = "font-size:7px;color:#444;padding:6px 4px 4px;font-family:'Press Start 2P'"
    sep.textContent = grupo.titulo
    lista.appendChild(sep)

    grupo.items.forEach(pkmn => {
      const card = document.createElement("div")
      card.className = "pokemon-card"
      card.id = `card-${pkmn.id}`
      card.onclick = () => window.ranchScene?.seleccionarPokemon(pkmn.id)

      const genSym   = pkmn.genero === "F" ? "♀" : pkmn.genero === "M" ? "♂" : ""
      const genClass = pkmn.genero === "F" ? "gender-f" : "gender-m"
      const shiny    = pkmn.es_shiny ? '<span class="shiny">★</span>' : ""
      const tipo2    = pkmn.tipo2
        ? `<span class="type-pill t-${pkmn.tipo2}">${pkmn.tipo2}</span>` : ""
      const ivTotal  = pkmn.iv_hp + pkmn.iv_ataque + pkmn.iv_defensa +
                      pkmn.iv_sp_ataque + pkmn.iv_sp_defensa + pkmn.iv_velocidad
      const ivPct    = Math.round((ivTotal / 186) * 100)
      const ivColor  = ivPct >= 80 ? "#7ec850" : ivPct >= 50 ? "#e8c840" : "#e85040"

      // Sprite: huevo si nivel 1 y tiene padre, normal si no
      const esHuevo    = pkmn.nivel === 1 && pkmn.padre_id !== null
      const spriteUrl  = esHuevo
        ? "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/lucky-egg.png"
        : API.spriteUrl(pkmn.numero_pokedex)
      const spriteAlt  = esHuevo ? "huevo" : pkmn.nombre

      card.innerHTML = `
        <img class="card-sprite" src="${spriteUrl}" alt="${spriteAlt}"
            onerror="this.src='${API.spriteUrl(pkmn.numero_pokedex)}'"/>
        <div class="card-info">
          <div class="card-name">
            ${esHuevo ? "🥚 " : ""}${pkmn.apodo || pkmn.nombre}
            <span class="${genClass}">${genSym}</span>${shiny}
          </div>
          <div class="card-types">
            <span class="type-pill t-${pkmn.tipo1}">${pkmn.tipo1}</span>${tipo2}
          </div>
          <div style="display:flex;align-items:center;gap:4px;margin-top:3px">
            <div class="iv-track" style="flex:1">
              <div class="iv-fill" style="width:${ivPct}%;background:${ivColor}"></div>
            </div>
            <span style="font-size:6px;color:${ivColor}">${ivPct}%</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;min-width:24px">
          ${pkmn.nivel > 1 ? `<span style="font-size:7px;color:#888">Nv${pkmn.nivel}</span>` : ""}
          <button class="delete-btn" title="Eliminar"
            onclick="event.stopPropagation(); eliminarPokemon(${pkmn.id})">✕</button>
        </div>
      `
      lista.appendChild(card)
    })
  })

  // Tab huevos — Pokémon nivel 1 criados
  const huevos = pokemonList.filter(p => p.nivel === 1 && p.padre_id !== null)
  const huevosList = document.getElementById("huevos-list")
  huevosList.innerHTML = huevos.length
    ? ""
    : `<div style="font-size:7px;color:#444;padding:16px 8px;text-align:center;font-family:'Press Start 2P'">Sin huevos</div>`

  huevos.forEach(pkmn => {
    const div = document.createElement("div")
    div.className = "pokemon-card"
    div.innerHTML = `
      <img class="card-sprite" src="${API.spriteUrl(pkmn.numero_pokedex)}" alt="${pkmn.nombre}"/>
      <div class="card-info">
        <div class="card-name">${pkmn.nombre} 🥚</div>
        <div class="card-types">
          <span class="type-pill t-${pkmn.tipo1}">${pkmn.tipo1}</span>
        </div>
        <div style="font-size:6px;color:#666;margin-top:2px">
          ${pkmn.genero === "F" ? "♀" : "♂"} · ${pkmn.naturaleza}
        </div>
      </div>
    `
    huevosList.appendChild(div)
  })
}

function actualizarSeleccionUI(selectedIds, pokemonList) {
  document.querySelectorAll(".pokemon-card").forEach(c => c.classList.remove("selected"))
  selectedIds.forEach(id => {
    const card = document.getElementById(`card-${id}`)
    if (card) card.classList.add("selected")
  })

  const lastId = selectedIds[selectedIds.length - 1]
  const pkmn   = pokemonList.find(p => p.id === lastId)

  if (pkmn) {
    document.getElementById("selected-sprite").src = API.spriteUrl(pkmn.numero_pokedex)
    const genSym   = pkmn.genero === "F" ? "♀" : pkmn.genero === "M" ? "♂" : ""
    const genClass = pkmn.genero === "F" ? "gender-f" : "gender-m"
    document.getElementById("selected-name").innerHTML =
      `${pkmn.apodo || pkmn.nombre} <span class="${genClass}">${genSym}</span>`
    document.getElementById("selected-meta").textContent =
      `Nv.${pkmn.nivel} · ${pkmn.tipo1}${pkmn.tipo2 ? "/"+pkmn.tipo2 : ""} · ${pkmn.naturaleza || "?"}`

    const ivs = [
      { label: "HP",  val: pkmn.iv_hp },
      { label: "Atk", val: pkmn.iv_ataque },
      { label: "Def", val: pkmn.iv_defensa },
      { label: "SpA", val: pkmn.iv_sp_ataque },
      { label: "SpD", val: pkmn.iv_sp_defensa },
      { label: "Vel", val: pkmn.iv_velocidad },
    ]
    document.getElementById("iv-bars").innerHTML = ivs.map(iv => {
      const pct   = Math.round((iv.val / 31) * 100)
      const clase = iv.val >= 28 ? "high" : iv.val >= 15 ? "mid" : "low"
      return `
        <div class="iv-row">
          <span class="iv-label">${iv.label}</span>
          <div class="iv-track"><div class="iv-fill ${clase}" style="width:${pct}%"></div></div>
          <span class="iv-val">${iv.val}</span>
        </div>`
    }).join("")
  } else {
    document.getElementById("selected-sprite").src = ""
    document.getElementById("selected-name").textContent = "—"
    document.getElementById("selected-meta").textContent = "Ninguno"
    document.getElementById("iv-bars").innerHTML = ""
  }

  // Botones
  const puedeCriar = selectedIds.length === 2
  document.getElementById("btn-criar").disabled = !puedeCriar
  document.getElementById("btn-mover").disabled = selectedIds.length !== 1

  // Texto del botón según selección
  if (selectedIds.length === 2) {
    const p1 = pokemonList.find(p => p.id === selectedIds[0])
    const p2 = pokemonList.find(p => p.id === selectedIds[1])
    if (p1 && p2) {
      document.getElementById("status-bar").textContent =
        `${p1.nombre} + ${p2.nombre} · listos para criar`
    }
  }
}

async function iniciarCrianza() {
  const ids = window.ranchScene?.getSelectedIds()
  if (!ids || ids.length !== 2) return

  const btn = document.getElementById("btn-criar")
  btn.disabled = true
  btn.textContent = "▶ Criando..."
  document.getElementById("status-bar").textContent = "Iniciando crianza..."

  try {
    const resultado = await API.realizar_breeding(ids[0], ids[1])
    const shiny = resultado.es_shiny ? "★ SHINY " : ""
    document.getElementById("status-bar").textContent =
      `¡Huevo obtenido! → ${resultado.especie_resultado.toUpperCase()} ${shiny}· ${resultado.genero === "F" ? "♀" : "♂"} · ${resultado.naturaleza}`

    // Recargar lista con el nuevo Pokémon
    const data = await API.getPokemon(1)
    const lista = data.filter(p => p.padre_id === null || p.nivel >= 10)
    window.ranchScene.pokemonList = data.filter(p => p.padre_id === null || p.nivel >= 1)
    actualizarListaPokemon(window.ranchScene.pokemonList)

  } catch(e) {
    document.getElementById("status-bar").textContent = `✗ ${e.message}`
  } finally {
    btn.disabled = false
    btn.textContent = "▶ Iniciar crianza"
  }
}

function moverZona() {
  document.getElementById("status-bar").textContent = "Mover zona — próximamente."
}

function verPokedex() {
  document.getElementById("status-bar").textContent = "Pokédex — próximamente."
}

async function eliminarPokemon(id) {
  const lista = window.ranchScene?.pokemonList
  const pkmn  = lista?.find(p => p.id === id)
  if (!pkmn) return

  const nombre = pkmn.apodo || pkmn.nombre
  if (!confirm(`¿Eliminar a ${nombre}?`)) return

  try {
    await API.eliminarPokemon(id)

    // Quitar del mapa
    const sprite = window.ranchScene?.sprites[id]
    if (sprite) {
      sprite.destroy()
      delete window.ranchScene.sprites[id]
    }

    // Quitar de selectedIds si estaba seleccionado
    if (window.ranchScene) {
      window.ranchScene.selectedIds =
        window.ranchScene.selectedIds.filter(sid => sid !== id)
      window.ranchScene.pokemonList =
        window.ranchScene.pokemonList.filter(p => p.id !== id)
    }

    // Actualizar sidebar
    actualizarListaPokemon(window.ranchScene?.pokemonList || [])
    actualizarSeleccionUI(
      window.ranchScene?.selectedIds || [],
      window.ranchScene?.pokemonList || []
    )

    document.getElementById("status-bar").textContent =
      `${nombre} eliminado del rancho.`

  } catch(e) {
    document.getElementById("status-bar").textContent = `✗ ${e.message}`
  }

  function actualizarZonasUI(zonas) {
    const lista = document.getElementById("zonas-list")
    if (!lista) return
    lista.innerHTML = ""

    zonas.forEach(zona => {
      const iconos = { cria: "🥚", entrenamiento: "⚡", incubacion: "🔮" }
      const icono  = iconos[zona.tipo_zona] || "📦"
      const count  = zona.pokemon_ids.length
      const huevo  = zona.huevo_id ? "· 🥚 huevo activo" : ""

      const div = document.createElement("div")
      div.style.cssText = `
        padding: 8px;
        border: 1px solid #333;
        border-radius: 4px;
        margin-bottom: 6px;
        font-size: 7px;
        font-family: 'Press Start 2P';
      `
      div.innerHTML = `
        <div style="color:#aaa;margin-bottom:4px">${icono} ${zona.nombre}</div>
        <div style="color:#666">${count} Pokémon ${huevo}</div>
      `
      lista.appendChild(div)
    })
  }

  window.actualizarZonasUI    = actualizarZonasUI
  window.actualizarListaPokemon = actualizarListaPokemon
  window.actualizarSeleccionUI  = actualizarSeleccionUI
}