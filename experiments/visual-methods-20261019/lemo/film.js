// Original film: The agent loop. Style grammar from lemo-opuscar swiss-motion (MIT).
const c = document.querySelector('canvas'),
  x = c.getContext('2d')
const C = {
  paper: '#EAE9E5',
  ink: '#111111',
  signal: '#E30613',
  grey: '#c8c8c3',
  muted: '#6a6a65',
}
const clamp = (v) => Math.max(0, Math.min(1, v))
// Invert cubic x so timing follows cubic-bezier(.7,0,.2,1), not a loose approximation.
function ease(v) {
  v = clamp(v)
  let lo = 0,
    hi = 1,
    u = v
  for (let i = 0; i < 24; i++) {
    u = (lo + hi) / 2
    const xx = 3 * (1 - u) ** 2 * u * 0.7 + 3 * (1 - u) * u * u * 0.2 + u ** 3
    if (xx < v) lo = u
    else hi = u
  }
  return 3 * (1 - u) * u * u + u ** 3
}
const p = (t, s, d = 0.75) => ease((t - s) / d)
function rect(a, b, w, h, col) {
  x.fillStyle = col
  x.fillRect(a, b, w, h)
}
function text(s, a, b, size = 80, col = C.ink, w = 700) {
  x.font = `${w} ${size}px Archivo`
  x.fillStyle = col
  x.textBaseline = 'top'
  x.letterSpacing = size >= 90 ? '-2px' : '0px'
  x.fillText(s, a, b)
}
function reveal(s, a, b, size, t, at, col = C.ink) {
  const q = p(t, at, 0.75)
  x.save()
  x.beginPath()
  x.rect(a - 4, b - 4, 1700, size * 1.22 + 8)
  x.clip()
  text(s, a, b + (1 - q) * size * 1.3, size, col)
  x.restore()
}
function line(a, b, d, e, col = C.ink, w = 3, prog = 1) {
  x.strokeStyle = col
  x.lineWidth = w
  x.beginPath()
  x.moveTo(a, b)
  x.lineTo(a + (d - a) * prog, b + (e - b) * prog)
  x.stroke()
}
function base(n) {
  rect(0, 0, 1920, 1080, C.paper)
  for (let i = 0; i <= 12; i++)
    line(96 + i * 144, 96, 96 + i * 144, 984, '#deded9', 1)
  line(96, 96, 1824, 96, C.ink, 2)
  text('BYTEFRONT / FIELD NOTES', 96, 52, 24, C.ink, 600)
  text('THE AGENT LOOP', 1400, 52, 24, C.ink, 600)
  text(n + ' / 04', 96, 978, 24)
  line(96, 948, 1824, 948, C.ink, 2)
}
function module(label, a, b, w, h, fill = C.ink) {
  rect(a, b, w, h, fill)
  text(label, a + 24, b + 24, 36, fill === C.ink ? '#fff' : C.ink, 600)
}
function pathProgress(pts, q, color = C.signal, width = 10) {
  const lengths = pts
    .slice(1)
    .map((b, i) => Math.hypot(b[0] - pts[i][0], b[1] - pts[i][1]))
  let left = lengths.reduce((a, b) => a + b, 0) * clamp(q)
  for (let i = 0; i < lengths.length; i++) {
    let z = Math.min(1, left / lengths[i])
    if (z > 0) line(...pts[i], ...pts[i + 1], color, width, z)
    left -= lengths[i]
  }
}
window.DUR = 24
window.EV = [
  { t: 6, label: 'action' },
  { t: 12, label: 'check' },
  { t: 18, label: 'loop' },
]
window.render = (tt) => {
  const t = Math.max(0, Math.min(23.999, tt)),
    s = Math.floor(t / 6),
    u = t - s * 6
  base(s + 1)
  if (s === 0) {
    // The period is the sole signal-colour protagonist; an answer is terminal.
    reveal('an answer', 96, 168, 210, u, 0)
    reveal('is a beginning.', 100, 410, 128, u, 0.5)
    text('01', 96, 676, 208, C.ink, 700)
    const q = p(u, 1.25, 1.5)
    rect(990, 640, 834 * q, 232, C.ink)
    text('MODEL → RESPONSE', 1022, 678, 35, C.paper, 500)
    text('A useful starting point.', 1022, 756, 52, C.paper, 600)
    rect(1728, 810, 96, 62 * p(u, 2.75), C.signal)
    text('One goal. One returned answer.', 340, 758, 34, C.muted, 500)
  } else if (s === 1) {
    reveal('take the', 96, 168, 166, u, 0)
    reveal('next step', 96, 360, 166, u, 0.5)
    const start = 1130,
      yy = 240
    for (let i = 0; i < 3; i++) {
      const q = p(u, 0.5 + i * 0.5)
      rect(start, yy + i * 192, 600, 144 * q, i === 1 ? C.signal : C.ink)
      if (q > 0.95)
        text(
          ['GOAL', 'TOOL', 'RESULT'][i],
          start + 36,
          yy + i * 192 + 36,
          54,
          i === 1 ? C.ink : '#fff',
        )
    }
    pathProgress(
      [
        [920, 290],
        [1010, 290],
        [1010, 690],
        [1110, 690],
      ],
      p(u, 2, 1.5),
      C.ink,
      8,
    )
    text('02', 96, 704, 168)
    text('Turn intention into an operation.', 340, 798, 34, C.muted, 500)
  } else if (s === 2) {
    reveal('make the work visible.', 96, 158, 104, u, 0)
    const labels = ['read', 'use', 'check']
    for (let i = 0; i < 3; i++) {
      let q = p(u, 0.5 + i * 0.75)
      const xx = 96 + i * 576
      rect(xx, 360, 528, 414 * q, i === 2 ? C.signal : C.ink)
      if (q > 0.95) {
        text('0' + (i + 1), xx + 32, 400, 120, i === 2 ? C.ink : C.paper)
        text(labels[i], xx + 32, 570, 86, i === 2 ? C.ink : C.paper)
        text(
          ['a goal', 'a tool', 'the result'][i],
          xx + 32,
          694,
          34,
          i === 2 ? C.ink : C.paper,
          500,
        )
      }
    }
    text('03', 96, 822, 88)
    text('Each step leaves something to inspect.', 340, 846, 38, C.muted, 500)
  } else {
    reveal('close the loop.', 96, 158, 156, u, 0)
    const box = [
      [96, 432, 480, 216],
      [720, 432, 480, 216],
      [1344, 432, 480, 216],
    ]
    box.forEach((r, i) => {
      rect(...r, C.ink)
      text(
        ['action', 'feedback', 'correction'][i],
        r[0] + 24,
        r[1] + 64,
        i === 2 ? 66 : 72,
        C.paper,
      )
    })
    pathProgress(
      [
        [576, 540],
        [720, 540],
      ],
      p(u, 0.75, 0.5),
      C.ink,
      8,
    )
    pathProgress(
      [
        [1200, 540],
        [1344, 540],
      ],
      p(u, 1.25, 0.5),
      C.ink,
      8,
    )
    pathProgress(
      [
        [1584, 664],
        [1584, 800],
        [336, 800],
        [336, 664],
      ],
      p(u, 1.75, 1.5),
      C.signal,
      16,
    )
    const q = p(u, 3.25, 0.75)
    rect(312, 650, 48, 48 * q, C.signal)
    text('04', 96, 828, 80)
    text('Try. Inspect. Adjust. Repeat.', 720, 840, 48, C.ink, 600)
  }
}
await document.fonts.load('400 80px Archivo')
await document.fonts.load('600 80px Archivo')
await document.fonts.load('700 200px Archivo')
window.render(0)
window.READY = true
