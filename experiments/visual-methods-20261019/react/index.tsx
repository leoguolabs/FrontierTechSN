import React from 'react'
import { Composition, registerRoot, staticFile } from 'remotion'
import { CoreFilm } from './Core'
import { BitsFilm } from './Bits'
import { ShotcraftFilm } from './Shotcraft'
import './style.css'
registerRoot(() => (
  <>
    <style>{`@font-face{font-family:Archivo;src:url(${staticFile('Archivo.ttf')})}`}</style>
    {[
      ['RemotionCore', CoreFilm],
      ['RemotionBits', BitsFilm],
      ['Shotcraft', ShotcraftFilm],
    ].map(([id, component]) => (
      <Composition
        key={id as string}
        id={id as string}
        component={component as any}
        durationInFrames={576}
        fps={24}
        width={1920}
        height={1080}
      />
    ))}
  </>
))
