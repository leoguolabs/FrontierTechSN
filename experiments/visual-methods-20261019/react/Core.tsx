import React from 'react'
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
} from 'remotion'
const ink = '#e5f0f6',
  blue = '#6cd2f3',
  bg = '#0b2033'
const q = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  })
const T = ({
  children,
  x = 100,
  y = 100,
  size = 64,
  color = ink,
  style = {},
}: any) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      fontSize: size,
      fontWeight: 600,
      letterSpacing: -size * 0.035,
      color,
      ...style,
    }}
  >
    {children}
  </div>
)
const Grid = () => (
  <svg width="1920" height="1080" style={{ position: 'absolute', inset: 0 }}>
    {Array.from({ length: 25 }, (_, i) => (
      <line
        key={'v' + i}
        x1={i * 80}
        y1="0"
        x2={i * 80}
        y2="1080"
        stroke="#244154"
        strokeWidth="1"
        opacity=".5"
      />
    ))}
    {Array.from({ length: 14 }, (_, i) => (
      <line
        key={'h' + i}
        x1="0"
        y1={i * 80}
        x2="1920"
        y2={i * 80}
        stroke="#244154"
        strokeWidth="1"
        opacity=".5"
      />
    ))}
  </svg>
)
const Scene = ({ index }: { index: number }) => {
  const f = useCurrentFrame()
  const enter = spring({
    frame: f,
    fps: 24,
    config: { damping: 200 },
    durationInFrames: 28,
  })
  return (
    <AbsoluteFill style={{ background: bg, color: ink, fontFamily: 'Archivo' }}>
      <Grid />
      <T size={24} x={96} y={64} style={{ letterSpacing: 4 }}>
        BYTEFRONT / THE AGENT LOOP
      </T>
      <T size={24} x={1660} y={64}>
        0{index + 1} / 04
      </T>
      {index === 0 && (
        <>
          <T
            y={206}
            size={120}
            style={{
              transform: `translateY(${(1 - enter) * 70}px)`,
              opacity: enter,
            }}
          >
            Start with an answer.
          </T>
          <svg width="1920" height="1080" style={{ position: 'absolute' }}>
            <rect
              x="176"
              y="480"
              width="420"
              height="220"
              rx="20"
              fill="#173952"
              stroke={blue}
              strokeWidth="2"
            />
            <path
              d="M600 590 H1000"
              pathLength="1"
              strokeDasharray="1"
              strokeDashoffset={1 - q(f, 24, 56)}
              stroke={blue}
              strokeWidth="4"
            />
            <path
              d="M970 568 L1000 590 L970 612"
              fill="none"
              stroke={blue}
              strokeWidth="4"
              opacity={q(f, 46, 56)}
            />
          </svg>
          <T x={246} y={544} size={68}>
            MODEL
          </T>
          <div
            style={{
              position: 'absolute',
              left: 1090,
              top: 430,
              width: 620,
              height: 340,
              border: '2px solid ' + ink,
              borderRadius: 16,
              background: '#112c43',
              padding: 44,
              opacity: q(f, 46, 70),
              transform: `translateX(${(1 - q(f, 46, 70)) * 100}px)`,
            }}
          >
            <div style={{ fontSize: 25, color: blue, letterSpacing: 4 }}>
              RESPONSE
            </div>
            <div style={{ fontSize: 60, marginTop: 30 }}>
              One possible
              <br />
              way forward.
            </div>
          </div>
          <T x={176} y={864} size={36} color="#9bb7c8">
            Useful information. Ready for the next step.
          </T>
        </>
      )}
      {index === 1 && (
        <>
          <T y={206} size={120}>
            Give the plan a tool.
          </T>
          <div
            style={{
              position: 'absolute',
              left: 180,
              top: 450,
              width: 800,
              height: 330,
              borderRadius: 18,
              background: '#e5f0f6',
              color: bg,
              padding: 44,
              transform: `translateY(${(1 - enter) * 120}px)`,
            }}
          >
            <div style={{ fontSize: 26, letterSpacing: 3, color: '#3f687b' }}>
              CONCEPTUAL OPERATION
            </div>
            <div style={{ fontSize: 62, marginTop: 45 }}>
              read → act → inspect
            </div>
            <div style={{ height: 6, background: '#c1d4df', marginTop: 50 }}>
              <div
                style={{
                  width: `${q(f, 35, 88) * 100}%`,
                  height: '100%',
                  background: '#1482a2',
                }}
              />
            </div>
          </div>
          <svg width="1920" height="1080" style={{ position: 'absolute' }}>
            <path
              d="M980 615 H1190"
              fill="none"
              stroke={blue}
              strokeWidth="5"
              pathLength="1"
              strokeDasharray="1"
              strokeDashoffset={1 - q(f, 40, 65)}
            />
            <circle
              cx="1430"
              cy="615"
              r={150 * enter}
              fill="#173952"
              stroke={blue}
              strokeWidth="3"
            />
          </svg>
          <T x={1330} y={570} size={60} style={{ opacity: enter }}>
            TOOL
          </T>
          <T x={180} y={868} size={36} color="#9bb7c8">
            A concrete operation connects intent to a result.
          </T>
        </>
      )}
      {index === 2 && (
        <>
          <T y={206} size={112}>
            Make each step inspectable.
          </T>
          {['READ A GOAL', 'USE A TOOL', 'CHECK RESULT'].map((label, i) => {
            let a = q(f, 10 + i * 22, 34 + i * 22)
            return (
              <div
                key={label}
                style={{
                  position: 'absolute',
                  left: 96 + i * 590,
                  top: 428,
                  width: 548,
                  height: 368,
                  background: i === 2 ? '#c6ecdb' : '#173952',
                  color: i === 2 ? bg : ink,
                  border: '2px solid ' + (i === 2 ? '#88cfac' : '#537b92'),
                  borderRadius: 16,
                  padding: 40,
                  transform: `translateY(${(1 - a) * 100}px)`,
                  opacity: a,
                }}
              >
                <div style={{ fontSize: 100, fontWeight: 600 }}>0{i + 1}</div>
                <div style={{ fontSize: 43, marginTop: 36 }}>{label}</div>
                <div style={{ fontSize: 26, marginTop: 24, opacity: 0.65 }}>
                  {['Intent', 'Operation', 'Evidence'][i]}
                </div>
              </div>
            )
          })}
          <T y={867} size={36} color="#9bb7c8">
            The result can change what happens next.
          </T>
        </>
      )}
      {index === 3 && (
        <>
          <T x={96} y={210} size={124}>
            Feedback
            <br />
            closes the loop.
          </T>
          <svg width="1920" height="1080" style={{ position: 'absolute' }}>
            <path
              d="M1150 320 L1630 580 L1150 840 L1150 320"
              fill="none"
              stroke="#274c65"
              strokeWidth="8"
            />
            <path
              d="M1150 320 L1630 580 L1150 840 L1150 320"
              fill="none"
              stroke={blue}
              strokeWidth="8"
              pathLength="1"
              strokeDasharray="1"
              strokeDashoffset={1 - q(f, 12, 100)}
            />
            {[
              [1150, 320],
              [1630, 580],
              [1150, 840],
            ].map(([a, b], i) => (
              <circle
                key={i}
                cx={a}
                cy={b}
                r="38"
                fill={i === 2 ? '#88cfac' : blue}
                opacity={q(f, 10 + i * 32, 22 + i * 32)}
              />
            ))}
          </svg>
          <T x={1240} y={245} size={45}>
            Action
          </T>
          <T x={1470} y={650} size={45}>
            Feedback
          </T>
          <T x={890} y={870} size={45}>
            Correction
          </T>
          <T x={96} y={740} size={44} color="#9bb7c8">
            Try again.
            <br />
            Use what you learned.
          </T>
        </>
      )}
    </AbsoluteFill>
  )
}
export const CoreFilm = () => (
  <AbsoluteFill>
    {[0, 1, 2, 3].map((i) => (
      <Sequence key={i} from={i * 144} durationInFrames={144}>
        <Scene index={i} />
      </Sequence>
    ))}
  </AbsoluteFill>
)
