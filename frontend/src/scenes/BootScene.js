class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: "BootScene" })
  }

  preload() {
    this.load.image("tileset", "assets/tilesets/exterior.png")
    this.load.json("mapa", "assets/tilemaps/rancho.json")
  }

  create() {
    this.scene.start("RanchScene")
  }
}