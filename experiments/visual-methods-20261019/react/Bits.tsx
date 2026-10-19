import React from 'react'
import { AbsoluteFill, Sequence, useCurrentFrame } from 'remotion'
import {
  AnimatedText,
  StaggeredMotion,
  Scene3D,
  Element3D,
} from 'remotion-bits'
const purple = '#c1adff',
  white = '#f1eef9'
const textIn = {
  y: [65, 0],
  opacity: [0, 1],
  blur: [14, 0],
  duration: 26,
  split: 'word',
  splitStagger: 2,
}
const Title = ({ children }: { children: React.ReactNode }) => (
  <AnimatedText
    transition={textIn}
    style={{
      fontSize: 126,
      fontWeight: 650,
      lineHeight: 1.02,
      letterSpacing: -5,
    }}
  >
    {children}
  </AnimatedText>
)
const panel: React.CSSProperties = {
  width: 540,
  height: 340,
  border: '1px solid #75678b',
  borderRadius: 28,
  background: 'linear-gradient(140deg,#443754,#1d1b2b)',
  boxShadow: '0 30px 60px #08071180',
  color: white,
  padding: 44,
}
const Scene = ({ i }: { i: number }) => {
  const f = useCurrentFrame()
  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at 60% 10%,#332644,#100f1b 70%)',
        color: white,
        fontFamily: 'Archivo',
        padding: 96,
      }}
    >
      <div style={{ fontSize: 24, letterSpacing: 4, color: '#ad9cbf' }}>
        BYTEFRONT / FIELD NOTES{' '}
        <span style={{ float: 'right' }}>0{i + 1} / 04</span>
      </div>
      {i === 0 && (
        <>
          <div style={{ position: 'absolute', left: 96, top: 220, width: 880 }}>
            <Title>{'Every action starts somewhere.'}</Title>
            <AnimatedText
              transition={{ ...textIn, delay: 36 }}
              style={{ fontSize: 42, marginTop: 50, color: '#b5a6c4' }}
            >
              An AI model gives you an answer.
            </AnimatedText>
          </div>
          <div
            style={{
              position: 'absolute',
              left: 1030,
              top: 300,
              width: 770,
              height: 570,
            }}
          >
            <Scene3D width={770} height={570} perspective={1400}>
              <Element3D
                centered
                x={0}
                y={0}
                z={0}
                rotateY={-10 + 14 * Math.max(0, 1 - f / 48)}
                rotateX={3}
                transition={{ opacity: [0, 1], duration: 30 }}
                style={{ ...panel, width: 620, height: 440 }}
              >
                <div style={{ fontSize: 27, color: purple, letterSpacing: 3 }}>
                  THE RESPONSE
                </div>
                <div style={{ fontSize: 70, marginTop: 64, fontWeight: 600 }}>
                  One way
                  <br />
                  forward.
                </div>
                <div style={{ height: 2, background: purple, marginTop: 42 }} />
              </Element3D>
            </Scene3D>
          </div>
        </>
      )}
      {i === 1 && (
        <>
          <div style={{ position: 'absolute', left: 96, top: 205 }}>
            <Title>Put the answer to work.</Title>
          </div>
          <StaggeredMotion
            transition={{
              y: [180, 0],
              rotateX: [25, 0],
              opacity: [0, 1],
              stagger: 16,
              duration: 34,
              delay: 16,
            }}
            style={{
              position: 'absolute',
              left: 100,
              top: 465,
              display: 'flex',
              gap: 50,
              perspective: 1400,
            }}
          >
            {['Goal', 'Tool', 'Result'].map((s, n) => (
              <div key={s} style={panel}>
                <div style={{ fontSize: 27, color: purple }}>0{n + 1}</div>
                <div style={{ fontSize: 84, marginTop: 65, fontWeight: 600 }}>
                  {s}
                </div>
                <div style={{ fontSize: 27, marginTop: 32, color: '#c1b4d0' }}>
                  {
                    [
                      'Read the intention',
                      'Take the next step',
                      'Inspect the evidence',
                    ][n]
                  }
                </div>
              </div>
            ))}
          </StaggeredMotion>
        </>
      )}
      {i === 2 && (
        <>
          <div style={{ position: 'absolute', left: 96, top: 200 }}>
            <Title>Check what came back.</Title>
          </div>
          <div
            style={{
              position: 'absolute',
              left: 96,
              top: 450,
              width: 1728,
              height: 400,
              background: '#eeebf4',
              color: '#242031',
              borderRadius: 30,
              padding: 48,
            }}
          >
            <StaggeredMotion
              transition={{
                x: [-100, 0],
                opacity: [0, 1],
                stagger: 18,
                duration: 30,
                delay: 12,
              }}
              style={{ display: 'flex', gap: 42 }}
            >
              {['Read a goal', 'Use a tool', 'Check the result'].map((s, n) => (
                <div
                  key={s}
                  style={{
                    width: 510,
                    padding: 30,
                    borderRight: n < 2 ? '1px solid #c7bfd3' : undefined,
                  }}
                >
                  <div style={{ fontSize: 94, color: '#796095' }}>0{n + 1}</div>
                  <div style={{ fontSize: 48, marginTop: 42, fontWeight: 600 }}>
                    {s}
                  </div>
                </div>
              ))}
            </StaggeredMotion>
          </div>
        </>
      )}
      {i === 3 && (
        <>
          <div style={{ position: 'absolute', left: 96, top: 200, width: 660 }}>
            <Title>{'Try again. With feedback.'}</Title>
          </div>
          <div
            style={{
              position: 'absolute',
              left: 850,
              top: 180,
              width: 950,
              height: 720,
            }}
          >
            <Scene3D width={950} height={720} perspective={1600}>
              {['Action', 'Feedback', 'Correction'].map((s, n) => (
                <Element3D
                  key={s}
                  centered
                  x={[-180, 180, 0][n]}
                  y={[-160, 60, 260][n]}
                  z={[-90, 0, 90][n]}
                  rotateY={-12}
                  transition={{
                    opacity: [0, 1],
                    delay: 12 + n * 23,
                    duration: 32,
                  }}
                  style={{ ...panel, width: 500, height: 210, padding: 38 }}
                >
                  <div style={{ fontSize: 24, color: purple }}>0{n + 1}</div>
                  <div style={{ fontSize: 65, marginTop: 20 }}>{s}</div>
                </Element3D>
              ))}
            </Scene3D>
          </div>
          <div style={{ position: 'absolute', left: 96, bottom: 140 }}>
            <AnimatedText
              transition={{ ...textIn, delay: 70 }}
              style={{ fontSize: 36, color: purple }}
            >
              The result shapes the next action.
            </AnimatedText>
          </div>
        </>
      )}
    </AbsoluteFill>
  )
}
export const BitsFilm = () => (
  <AbsoluteFill>
    {[0, 1, 2, 3].map((i) => (
      <Sequence key={i} from={144 * i} durationInFrames={144}>
        <Scene i={i} />
      </Sequence>
    ))}
  </AbsoluteFill>
)
