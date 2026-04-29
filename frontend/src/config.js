const GAME_WIDTH  = 560
const GAME_HEIGHT = 480
const TOPBAR_H    = 30

const TYPE_COLORS = {
  grass:    { bg: 0x1a3a10, text: "#7ec850" },
  fire:     { bg: 0x3a1a10, text: "#e87040" },
  water:    { bg: 0x10203a, text: "#5090e8" },
  electric: { bg: 0x3a2a00, text: "#e8c840" },
  psychic:  { bg: 0x3a1030, text: "#e850a0" },
  poison:   { bg: 0x2a1040, text: "#a060e8" },
  normal:   { bg: 0x2a2a2a, text: "#aaaaaa" },
  dragon:   { bg: 0x1a1060, text: "#6060e8" },
  dark:     { bg: 0x1a1a1a, text: "#888888" },
  flying:   { bg: 0x102030, text: "#80b0e0" },
  rock:     { bg: 0x2a2010, text: "#c0a060" },
  ground:   { bg: 0x2a1a00, text: "#c08040" },
  ice:      { bg: 0x102030, text: "#80d0e8" },
  bug:      { bg: 0x1a2a10, text: "#80a840" },
  ghost:    { bg: 0x201040, text: "#8060c0" },
  steel:    { bg: 0x202030, text: "#a0a0c0" },
  fairy:    { bg: 0x3a1030, text: "#e880b0" },
  fighting: { bg: 0x3a1010, text: "#c04040" },
}

const ZONA_COLORS = {
  crianza:     0xd4a030,
  experiencia: 0x40a040,
  especial:    0x8040c0,
}