import path from 'node:path'
import { loadImage } from '@napi-rs/canvas'
import { begin, label, lines, caption, P } from './rebuild/stage.mjs'

const clamp = x => Math.max(0, Math.min(1, x))
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x) }
const cache = new Map()
async function image(root, name) {
  const key = path.resolve(root, name)
  if (!cache.has(key)) cache.set(key, await loadImage(key))
  return cache.get(key)
}
function card(c, x, y, w, h) {
  c.save(); c.shadowColor = '#372d2520'; c.shadowBlur = 24; c.shadowOffsetY = 12
  c.fillStyle = '#fff'; c.fillRect(x, y, w, h); c.restore()
}
function stroke(c, points, color, width = 4) {
  c.beginPath(); points.forEach(([x, y], i) => i ? c.lineTo(x, y) : c.moveTo(x, y))
  c.strokeStyle = color; c.lineWidth = width; c.lineJoin = 'round'; c.lineCap = 'round'; c.stroke()
}
function footer(c, shot) {
  label(c, shot.credit, 120, 873, 24, { max: 1680, fill: '#5d564c' })
}

// All geometry uses the unchanged 1920×1080 Goo stage. Source rectangles are
// expressed in original image pixels; the marker and image share one transform.
export async function paintEvidence(c, shot, frame, language, root, subtitle = '') {
  const t = (frame - shot.start) / 24, duration = (shot.end - shot.start) / 24
  begin(c, frame, language, P.paper, { floor: false })
  label(c, shot.kicker, 120, 79, 28, { fill: '#637972' })
  label(c, shot.title, 120, 151, 57, { kind: 'slab', max: 1680 })
  if (shot.type === 'document') {
    const img = await image(root, shot.asset), crop = shot.crop ?? [0, 0, img.width, img.height]
    const [sx, sy, sw, sh] = crop, target = shot.target ?? [150, 245, 1620, 480]
    const [x, y, w, h] = target, scale = Math.min((w - 70) / sw, (h - 50) / sh)
    const zoom = 1 + .025 * ease(t / Math.max(1, duration - 1))
    card(c, x - 18, y - 20, w + 36, h + 40)
    c.save(); c.beginPath(); c.rect(x - 8, y - 10, w + 16, h + 20); c.clip()
    c.translate(x + w / 2, y + h / 2); c.scale(zoom, zoom)
    c.translate(-sw * scale / 2, -sh * scale / 2); c.scale(scale, scale)
    c.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh)
    for (const mark of shot.highlights ?? []) {
      const u = ease((t - mark.at) / (mark.seconds ?? .55))
      if (!u) continue
      const [mx, my, mw, mh] = mark.rect
      c.save(); c.fillStyle = '#ffe34b'
      if (mark.mode === 'underline') {
        c.fillRect(mx - sx - 3, my - sy + mh + 5, (mw + 6) * u, Math.max(4, mh * .08))
      } else {
        c.globalCompositeOperation = 'multiply'; c.globalAlpha = .76
        c.fillRect(mx - sx - 3, my - sy - 1, (mw + 6) * u, mh + 2)
      }
      c.restore()
    }
    c.restore()
    if (shot.takeaway) lines(c, shot.takeaway, 960, 789, 1630, 43, { align: 'center', kind: 'slab' })
  } else if (shot.type === 'chart') {
    const data = shot.points, x0 = 280, y0 = 734, w = 1300, h = 440
    const maxX = shot.x_max, maxY = shot.y_max
    const xy = ([x, y]) => [x0 + x / maxX * w, y0 - y / maxY * h]
    card(c, 125, 220, 1670, 605)
    for (let i = 0; i <= 4; i++) {
      const y = y0 - h * i / 4
      stroke(c, [[x0, y], [x0 + w, y]], '#e4e1d8', 2)
      label(c, Math.round(maxY * i / 4).toLocaleString('en-US'), x0 - 24, y + 10, 26, { align: 'right' })
    }
    stroke(c, [[x0, y0 - h], [x0, y0], [x0 + w + 20, y0]], '#40372d', 3)
    for (const x of shot.x_ticks) label(c, String(x), x0 + x / maxX * w, y0 + 42, 29, { align: 'center' })
    label(c, shot.y_label, 155, 264, 25, { max: 1200 })
    label(c, shot.x_label, 1707, 814, 25, { align: 'right' })
    // Reveal a fixed dataset; never interpolate or fabricate observations.
    const progress = ease((t - .65) / 4.8), limit = progress * maxX
    const visible = data.filter(p => p[0] <= limit)
    if (visible.length > 1) stroke(c, visible.map(xy), '#277f74', 6)
    if (visible.length) {
      const [x, y] = xy(visible.at(-1))
      c.fillStyle = '#e8b22e'; c.beginPath(); c.arc(x, y, 10, 0, 2 * Math.PI); c.fill()
    }
    for (const note of shot.annotations) {
      if (t < note.at) continue
      const [x, y] = xy(note.point)
      c.fillStyle = '#c35f45'; c.beginPath(); c.arc(x, y, 8, 0, Math.PI * 2); c.fill()
      label(c, note.label, x + note.dx, y + note.dy, 35, { align: note.align ?? 'left', kind: 'slab', max: 1000 })
    }
  } else if (shot.type === 'image') {
    const img = await image(root, shot.asset)
    const scale = Math.min(560 / img.width, 600 / img.height) * (1.025 - .025 * ease(t / duration))
    const x = 438 - img.width * scale / 2, y = 218
    card(c, x - 8, y - 8, img.width * scale + 16, img.height * scale + 16)
    c.drawImage(img, x, y, img.width * scale, img.height * scale)
    const [sx, sy, sw, sh] = shot.detail_crop
    card(c, 820, 250, 945, 390)
    c.drawImage(img, sx, sy, sw, sh, 846, 276, 893, 338)
    label(c, shot.detail_label, 834, 701, 32, { fill: '#637972' })
    lines(c, shot.takeaway, 834, 761, 900, 40, { kind: 'slab' })
  } else if (shot.type === 'footage') {
    const local = frame - shot.start
    // Extract once at the delivery cadence; random access remains deterministic.
    const img = await loadImage(path.resolve(root, shot.frames_dir, `${String(local + 1).padStart(6, '0')}.jpg`))
    const x = 130, y = 205, w = 1660, h = 615
    c.save(); c.beginPath(); c.rect(x, y, w, h); c.clip()
    const scale = Math.max(w / img.width, h / img.height)
    c.drawImage(img, x + (w - img.width * scale) / 2, y + (h - img.height * scale) / 2, img.width * scale, img.height * scale)
    c.restore(); c.fillStyle = '#f6eddb'; c.fillRect(148, 225, 310, 45)
    label(c, shot.context_label, 164, 257, 26, { max: 285 })
  } else throw new Error(`Unknown evidence type: ${shot.type}`)
  footer(c, shot)
  // Source pages stay untextured for legibility. Captions keep the host style.
  caption(c, subtitle)
}
