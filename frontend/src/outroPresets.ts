import type { OutroPreset } from './api'

// Keep interface copy in English, independent of the media catalog's language.
export const OUTRO_PRESET_COPY: Record<OutroPreset['id'], Pick<OutroPreset, 'name' | 'tone' | 'description'>> = {
  'data-extraction': {
    name: 'Data Extraction',
    tone: 'Dark tech',
    description: 'Blue data streams with copper pulses.',
  },
  'morning-brief': {
    name: 'Morning Brief',
    tone: 'Warm editorial',
    description: 'Layered paper and a soft sunrise.',
  },
  'signal-shot': {
    name: 'Signal Shot',
    tone: 'Minimal broadcast',
    description: 'Navy signal bars with copper pulses.',
  },
}
