const config = {
  type: Phaser.CANVAS,
  canvas: document.getElementById("phaser-canvas"),
  width:  800,
  height: 600,
  backgroundColor: "#3a7a22",
  scene: [BootScene, RanchScene],
  pixelArt: true,
}

const game = new Phaser.Game(config)

// Referencia global a la escena para que el HTML pueda comunicarse
game.events.on("ready", () => {
  window.ranchScene = game.scene.getScene("RanchScene")
})

// También lo asignamos cuando la escena arranca
game.events.on("step", () => {
  if (!window.ranchScene) {
    const scene = game.scene.getScene("RanchScene")
    if (scene && scene.sys.isActive()) {
      window.ranchScene = scene
    }
  }
})