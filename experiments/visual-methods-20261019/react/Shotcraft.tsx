import React from 'react'
import { AbsoluteFill, Sequence, useCurrentFrame } from 'remotion'
import { RecipeFrameProvider } from './RecipeClock'
import { OrbitRingTitleOpen } from './vendor/OrbitRingTitleOpen'
import { ScanlineAnnotateFocus } from './vendor/ScanlineAnnotateFocus'
import { WordRelayGeometry } from './vendor/WordRelayGeometry'
import { EASE, ramp } from './vendor/_fixtures/Polish'
const Recipe = ({ component: Comp }: { component: React.FC }) => {
  const f = useCurrentFrame()
  return (
    <RecipeFrameProvider frame={(f * 30) / 24}>
      <Comp />
      {Comp === WordRelayGeometry && <LoopCue frame={(f * 30) / 24} />}
    </RecipeFrameProvider>
  )
}
// Original explanatory overlay, outside the borrowed typography recipe.
const LoopCue = ({ frame: f }: { frame: number }) => {
  let p = ramp(f, 120, 28, EASE.smooth)
  return (
    <svg
      viewBox="0 0 1920 1080"
      style={{
        position: 'absolute',
        inset: 0,
        opacity: ramp(f, 116, 12, EASE.out),
      }}
    >
      <path
        d="M620 858H1300Q1340 858 1340 826Q1340 802 1300 802H620Q580 802 580 826Q580 858 620 858"
        pathLength={1}
        stroke="#a8bf8b"
        strokeWidth="3"
        fill="none"
        strokeDasharray={1}
        strokeDashoffset={1 - p}
      />
      {[620, 960, 1300].map((x) => (
        <circle key={x} cx={x} cy={858} r={7} fill="#e7ecd9" opacity={p} />
      ))}
      <path
        d="m610 849 12 9-12 9"
        fill="none"
        stroke="#e7ecd9"
        strokeWidth="3"
        opacity={p}
      />
    </svg>
  )
}
// Original bridge; explicitly not presented as an upstream shot recipe.
const Bridge = () => {
  let f = (useCurrentFrame() * 30) / 24
  let q = ramp(f, 0, 32, EASE.snappy)
  return (
    <AbsoluteFill
      style={{
        background: '#10120e',
        color: '#eef2e8',
        fontFamily: 'Archivo',
        padding: 120,
      }}
    >
      <div style={{ fontSize: 26, letterSpacing: 5, color: '#a6b78a' }}>
        02 / THE NEXT STEP
      </div>
      <div
        style={{
          fontSize: 130,
          fontWeight: 650,
          letterSpacing: -5,
          marginTop: 70,
          transform: `translateY(${(1 - q) * 60}px)`,
          opacity: q,
        }}
      >
        An agent takes action.
      </div>
      <div style={{ display: 'flex', gap: 70, marginTop: 120 }}>
        {['GOAL', 'TOOL', 'RESULT'].map((s, i) => {
          let z = ramp(f, 22 + i * 22, 28, EASE.snappy)
          return (
            <div
              key={s}
              style={{
                width: 480,
                height: 330,
                padding: 44,
                border: '1px solid #4b553f',
                background: i === 1 ? '#c6f432' : '#1c2117',
                color: i === 1 ? '#171d0b' : '#eef2e8',
                borderRadius: 18,
                transform: `translateY(${(1 - z) * 160}px)`,
                opacity: z,
              }}
            >
              <div style={{ fontSize: 90, fontWeight: 600 }}>0{i + 1}</div>
              <div style={{ fontSize: 55, marginTop: 44 }}>{s}</div>
            </div>
          )
        })}
      </div>
      <div style={{ fontSize: 34, marginTop: 70, color: '#a6b78a' }}>
        A plan becomes a concrete operation.
      </div>
    </AbsoluteFill>
  )
}
export const ShotcraftFilm = () => (
  <AbsoluteFill>
    <Sequence from={0} durationInFrames={144}>
      <Recipe component={OrbitRingTitleOpen} />
    </Sequence>
    <Sequence from={144} durationInFrames={144}>
      <Bridge />
    </Sequence>
    <Sequence from={288} durationInFrames={144}>
      <Recipe component={ScanlineAnnotateFocus} />
    </Sequence>
    <Sequence from={432} durationInFrames={144}>
      <Recipe component={WordRelayGeometry} />
    </Sequence>
  </AbsoluteFill>
)
