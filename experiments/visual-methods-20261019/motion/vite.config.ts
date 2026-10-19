import { defineConfig } from 'vite'
import motionCanvas from '@motion-canvas/vite-plugin'
import ffmpeg from '@motion-canvas/ffmpeg'
export default defineConfig({
  plugins: [
    (motionCanvas as any).default({
      output: '../../../outputs/visual-methods-20261019/motion-export',
    }),
    (ffmpeg as any).default(),
  ],
  server: {
    host: '127.0.0.1',
    port: 9019,
    fs: {
      allow: [
        process.cwd(),
        '../../../outputs/visual-methods-20261019/runtime/node_modules',
      ],
    },
  },
  esbuild: { jsx: 'automatic', jsxImportSource: '@motion-canvas/2d/lib' },
})
