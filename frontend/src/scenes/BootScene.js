class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: "BootScene" })
  }

  preload() {
    // Tiles del mapa
    this.load.image("grass",  "assets/grass.png")

    // Cargar sprites de los Pokémon del jugador desde PokéAPI
    // Los cargamos dinámicamente en RanchScene al tener los datos
  }

  create() {
    this.scene.start("RanchScene")
  }
}