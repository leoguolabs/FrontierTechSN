import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import vm from 'node:vm'
import test, { after } from 'node:test'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

function backgroundImagePage(options = {}) {
  class Element {
    constructor(attributes = {}, parentElement = null) {
      this.attributes = attributes
      this.parentElement = parentElement
      this.className = ''
      this.style = { display: 'block', visibility: 'visible', contentVisibility: 'visible' }
    }
    getAttribute(key) { return this.attributes[key] ?? null }
    getBoundingClientRect() { return { width: options.layout ? 480 : 0, height: options.layout ? 270 : 0 } }
    querySelector() { return null }
    closest(selector) {
      if (selector.startsWith('form,')) return options.composer || options.upload ? new Element() : null
      if (selector === '[data-message-author-role], [data-turn], [data-chatgpt-search-unit-key]') {
        return options.role ? new Element({ [options.roleAttribute || 'data-message-author-role']: options.role }) : null
      }
      if (selector === '[data-testid="generated-image-preview"]') return options.preview === false ? null : preview
      if (selector === '[data-testid="generated-image-gallery"]') return options.gallery === false ? null : gallery
      if (selector.startsWith('section[')) return options.upload ? new Element({ 'data-turn': 'user' }) : null
      return null
    }
  }
  class Image extends Element {}
  class Canvas extends Element {
    getContext() { return { getImageData: () => ({ data: [30, 30, 30, 255] }) } }
    toDataURL() { return 'data:image/png;base64,preview' }
  }
  const gallery = new Element({ 'data-testid': 'generated-image-gallery' })
  const preview = new Element({ 'data-testid': 'generated-image-preview' }, gallery)
  const Surface = options.surface === 'canvas' ? Canvas : options.surface === 'background' ? Element : Image
  const image = new Surface({ alt: options.alt ?? 'Generated image 1' }, preview)
  Object.assign(image, { complete: options.complete ?? true, naturalWidth: options.width ?? 1672,
    naturalHeight: 941, width: 480, height: 270, src: options.src ?? 'blob:https://chatgpt.com/owned-image' })
  image.style.backgroundImage = 'url("blob:https://chatgpt.com/owned-image")'
  if (options.hidden) gallery.style[options.hidden] = options.hidden === 'display' ? 'none' : 'hidden'
  if (options.ariaHidden) gallery.attributes['aria-hidden'] = 'true'
  if (options.hiddenAttribute) gallery.hidden = true
  const selectorForSurface = options.surface === 'canvas' ? 'canvas'
    : options.surface === 'background' ? '[style*="background-image"], [style*="background"]' : 'img'
  const context = { HTMLElement: Element, HTMLImageElement: Image, HTMLCanvasElement: Canvas, URL,
    document: { visibilityState: options.visibility ?? 'hidden', querySelectorAll(selector) { return selector === selectorForSurface ? [image] : [] } },
    window: { location: { href: savedUrl }, getComputedStyle: element => element.style } }
  return { async evaluate(script) { return vm.runInNewContext(script, context) } }
}

test('background generation result survives a zero-size gallery layout', async () => {
  const source = fs.readFileSync(path.join(copied, 'clis/chatgpt/utils.js'), 'utf8')
  const start = source.indexOf('export async function getChatGPTVisibleImageUrls(page) {')
  const end = source.indexOf('export async function waitForChatGPTImages(', start)
  const detect = vm.runInNewContext(source.slice(start, end).replace('export ', '') + '\ngetChatGPTVisibleImageUrls', {
    unwrapEvaluateResult: value => value, requireArrayEvaluateResult: value => value,
  })
  assert.deepEqual(Array.from(await detect(backgroundImagePage())), ['blob:https://chatgpt.com/owned-image'])
  assert.deepEqual(Array.from(await detect(backgroundImagePage({ layout: true, visibility: 'visible' }))), ['blob:https://chatgpt.com/owned-image'])
  for (const options of [
    { visibility: 'visible' }, { preview: false }, { gallery: false }, { complete: false }, { width: 0 },
    { alt: 'Uploaded image' }, { src: 'data:image/png;base64,partial' }, { upload: true },
    { hidden: 'display' }, { hidden: 'visibility' }, { hidden: 'contentVisibility' },
    { ariaHidden: true }, { hiddenAttribute: true },
  ]) assert.deepEqual(Array.from(await detect(backgroundImagePage(options))), [], JSON.stringify(options))
})

test('visible unsent and submitted reference images cannot complete image generation', async () => {
  const source = fs.readFileSync(path.join(copied, 'clis/chatgpt/utils.js'), 'utf8')
  const start = source.indexOf('export async function getChatGPTVisibleImageUrls(page) {')
  const end = source.indexOf('export async function waitForChatGPTImages(', start)
  const detect = vm.runInNewContext(source.slice(start, end).replace('export ', '') + '\ngetChatGPTVisibleImageUrls', {
    unwrapEvaluateResult: value => value, requireArrayEvaluateResult: value => value,
  })
  const visible = { layout: true, visibility: 'visible', alt: '', preview: false, gallery: false }
  for (const options of [
    visible, { ...visible, composer: true }, { ...visible, upload: true },
    { ...visible, role: 'user' }, { ...visible, role: 'fallback-turn-0:1:user', roleAttribute: 'data-chatgpt-search-unit-key' },
    { layout: true, composer: true }, { layout: true, upload: true },
  ]) assert.deepEqual(Array.from(await detect(backgroundImagePage(options))), [], JSON.stringify(options))
  for (const options of [
    { ...visible, role: 'assistant' }, { ...visible, role: 'assistant', roleAttribute: 'data-turn' },
    { ...visible, role: 'fallback-turn-0:2:assistant', roleAttribute: 'data-chatgpt-search-unit-key' },
  ]) assert.deepEqual(Array.from(await detect(backgroundImagePage(options))), ['blob:https://chatgpt.com/owned-image'])
  for (const surface of ['background', 'canvas']) {
    for (const extra of [{}, { composer: true }, { upload: true }]) {
      assert.deepEqual(Array.from(await detect(backgroundImagePage({ ...visible, surface, ...extra }))), [])
    }
    assert.deepEqual(Array.from(await detect(backgroundImagePage({ ...visible, surface, role: 'assistant' }))),
      [surface === 'canvas' ? 'data:image/png;base64,preview' : 'blob:https://chatgpt.com/owned-image'])
  }
})

// Apply the complete postinstall patch only to a disposable adapter tree.
// Nothing imports the installed adapter or contacts the browser/daemon.
const runtime = path.dirname(fileURLToPath(import.meta.url))
const installed = path.join(runtime, 'node_modules/@jackwener/opencli')
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'thumbnail-adapter-'))
const copied = path.join(temporary, 'node_modules/@jackwener/opencli')
const files = [
  'package.json', 'cli-manifest.json', 'dist/src/execution.js',
  ...['ask', 'utils', 'models', 'video'].map(name => `clis/gemini/${name}.js`),
  ...['ask', 'utils', 'model', 'detail', 'read', 'image'].map(name => `clis/chatgpt/${name}.js`),
]
const originals = new Map(files.map(name => [name, fs.readFileSync(path.join(installed, name))]))
after(() => {
  for (const [name, before] of originals) assert.deepEqual(fs.readFileSync(path.join(installed, name)), before)
  fs.rmSync(temporary, { recursive: true, force: true })
})
for (const [name, source] of originals) {
  const target = path.join(copied, name)
  fs.mkdirSync(path.dirname(target), { recursive: true })
  fs.writeFileSync(target, source)
}
fs.copyFileSync(path.join(runtime, 'patch-opencli.mjs'), path.join(temporary, 'patch-opencli.mjs'))
fs.cpSync(path.join(runtime, 'patches'), path.join(temporary, 'patches'), { recursive: true })
execFileSync(process.execPath, [path.join(temporary, 'patch-opencli.mjs')])
const patchedOnce = new Map(files.map(name => [name, fs.readFileSync(path.join(copied, name))]))
execFileSync(process.execPath, [path.join(temporary, 'patch-opencli.mjs')])

function waitSource(source) {
  const start = source.indexOf('export async function waitForChatGPTImages(')
  const end = source.indexOf('export async function getProjectList(page)', start)
  assert.ok(start >= 0 && end > start)
  return source.slice(start, end).replace('export async function', 'async function')
}
const patchedUtils = fs.readFileSync(path.join(copied, 'clis/chatgpt/utils.js'), 'utf8')
const fixedWait = waitSource(patchedUtils)
const savedUrl = 'https://chatgpt.com/c/abcd1234-saved'
const localUrl = 'https://chatgpt.com/c/local-chatgpt%3A5a445fbe-4e97-4097-8cc8-7a65077b6233'
const imageUrl = 'https://chatgpt.com/backend-api/files/image123'

class AdapterError extends Error {
  constructor(...parts) { super(parts.join(' ')) }
}

function waiter(source = fixedWait, options = {}) {
  const state = { clock: 0, reads: 0, navigations: [], progress: [], url: options.url || savedUrl }
  const page = {
    async sleep(seconds) { state.clock += seconds * 1000 },
    async evaluate(script) {
      state.reads++; state.clock += options.bridgeMs || 0
      if (script !== 'window.location.href') return options.diagnostic?.(script, state)
      return options.readUrl?.(state) ?? state.url
    },
    async goto(url) { state.navigations.push(url); state.clock += 2000 },
  }
  const context = {
    Date: { now: () => state.clock },
    TimeoutError: AdapterError, CommandExecutionError: AdapterError,
    unwrapEvaluateResult: value => value,
    isSameChatGPTConversation: (actual, expected) => actual === expected || actual.startsWith(`${expected}?`),
    async isGenerating() {
      state.clock += options.bridgeMs || 0
      return options.generating?.(state) || false
    },
    async getChatGPTVisibleImageUrls() {
      state.clock += options.bridgeMs || 0
      return options.images?.(state) || []
    },
    async resolveChatGPTConversationIdentity() { return options.identity || null },
    async getVisibleMessages(_page, readOptions) {
      state.messageReadOptions = readOptions
      return options.messages?.(state) ?? [{ Role: 'User', Text: options.actualPrompt || 'exact image prompt' }]
    },
    chatGPTPromptMatches: (actual, expected) => actual === expected,
  }
  const wait = vm.runInNewContext(source + '\nwaitForChatGPTImages', context)
  return { state, run(timeout = 30, conversation = savedUrl, extra = {}) {
    return wait(page, [], timeout, conversation, {
      onProgress(stage, url) { state.progress.push({ stage, url }) }, ...extra,
    })
  } }
}

test('postinstall patch is idempotent and leaves installed adapters byte-identical', () => {
  for (const [name, before] of patchedOnce) assert.deepEqual(fs.readFileSync(path.join(copied, name)), before, name)
})

test('reproduces installed poll-count timeout exceeding the 405 second parent ceiling', async t => {
  const legacy = waitSource(originals.get('clis/chatgpt/utils.js').toString())
  if (!legacy.includes('maxPolls')) return t.skip('Installed runtime already has the elapsed-time fix')
  const { run, state } = waiter(legacy, { bridgeMs: 2000 })
  await run(360)
  assert.ok(state.clock > 405000, `Legacy wait took ${state.clock} ms`)
  assert.ok(state.navigations.length > 0)
})

test('bridge latency counts against the image response deadline', async () => {
  const { run, state } = waiter(fixedWait, { bridgeMs: 2000 })
  assert.deepEqual(Array.from(await run(360)), [])
  assert.ok(state.clock <= 362000, `Deadline drifted to ${state.clock} ms`)
  assert.equal(state.navigations.length, 0)
  assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
})

test('idle saved conversation is never periodically reloaded before a late image', async () => {
  const { run, state } = waiter(fixedWait, { images: state => state.clock > 20000 ? [imageUrl] : [] })
  assert.deepEqual(Array.from(await run(30)), [imageUrl])
  assert.equal(state.navigations.length, 0)
  assert.equal(state.progress.at(-1).stage, 'images_detected')
})

test('missing-image observations distinguish unloaded and loaded resources without exposing URLs', async () => {
  const observations = []
  const { run, state } = waiter(fixedWait, {
    diagnostic(script, state) {
      const image = {
        getAttribute: () => 'Generated image 1', closest: () => null,
        complete: state.clock >= 120000, naturalWidth: state.clock >= 120000 ? 1920 : 0,
        naturalHeight: state.clock >= 120000 ? 1080 : 0,
        src: 'https://private.example/image?secret=do-not-log',
        getBoundingClientRect: () => ({ width: 0, height: 0 }),
      }
      return vm.runInNewContext(script, { document: {
        visibilityState: 'hidden', readyState: 'complete', querySelectorAll: () => [image],
      } })
    },
  })
  assert.deepEqual(Array.from(await run(130, savedUrl, {
    prompt: 'exact image prompt', onDiagnostic: (data, url) => observations.push({ data, url }),
  })), [])
  assert.equal(observations.length, 2)
  assert.equal(observations[0].data.generated_images[0].complete, false)
  assert.equal(observations[0].data.generated_images[0].natural_width, 0)
  assert.equal(observations[1].data.generated_images[0].natural_width, 1920)
  assert.equal(observations[1].data.generated_images[0].layout_width, 0)
  assert.equal(observations[1].data.generated_images[0].source_kind, 'http')
  assert.equal(observations[1].url, savedUrl)
  assert.ok(!JSON.stringify(observations).includes('private.example'))
  assert.ok(!JSON.stringify(observations).includes('do-not-log'))
  assert.equal(state.clock, 130000)
  assert.equal(state.navigations.length, 0)
})

test('failed diagnostic cannot mask timeout or leak raw bridge errors', async () => {
  const observations = []
  const { run, state } = waiter(fixedWait, {
    diagnostic() { throw new Error('secret bridge response') },
  })
  assert.deepEqual(Array.from(await run(65, savedUrl, {
    onDiagnostic: data => observations.push(data),
  })), [])
  assert.equal(observations.length, 1)
  assert.equal(observations[0].observation_failed, true)
  assert.ok(!JSON.stringify(observations).includes('secret'))
  assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
  assert.equal(state.clock, 65000)
})

test('diagnostics do not read again at the deadline or while generation is active', async () => {
  for (const options of [{}, { generating: () => true }]) {
    let reads = 0
    const { run } = waiter(fixedWait, { ...options, diagnostic() { reads++; return {} } })
    const result = run(60, savedUrl, { onDiagnostic() {} })
    if (options.generating) await assert.rejects(result, /No stable finished image/)
    else assert.deepEqual(Array.from(await result), [])
    assert.equal(reads, 0)
  }
})

test('stuck generation reports elapsed state without reading images or replaying the turn', async () => {
  const observations = []
  const { run, state } = waiter(fixedWait, {
    generating: () => true,
    images() { assert.fail('Do not inspect images during generation') },
    diagnostic() { assert.fail('Do not add browser reads during generation') },
  })
  await assert.rejects(run(130, savedUrl, {
    onDiagnostic(data, url) { observations.push({ ...data, url }) },
  }), /No stable finished image/)
  assert.deepEqual(observations, [
    { still_rendering: true, elapsed_seconds: 60, url: savedUrl },
    { still_rendering: true, elapsed_seconds: 120, url: savedUrl },
  ])
  assert.equal(state.clock, 130000)
  assert.equal(state.navigations.length, 0)
})

test('a failed generation diagnostic preserves the original timeout', async () => {
  const { run, state } = waiter(fixedWait, { generating: () => true })
  await assert.rejects(run(65, savedUrl, {
    onDiagnostic() { throw new Error('observation unavailable') },
  }), /No stable finished image/)
  assert.equal(state.clock, 65000)
  assert.equal(state.navigations.length, 0)
})

const imageFailure = "I wasn't able to generate the image due to an error on my side."
const ownedFailure = [
  { Role: 'User', Text: 'exact image prompt' },
  { Role: 'Assistant', Text: imageFailure },
]

test('missing reference upload is a terminal owned response, never a fresh submission', async () => {
  const missing = { Role: 'Assistant', Text: 'Please upload the earlier image (image_01d0c2.jpg) so I can recompose it, replacing the detailed figures.' }
  const { run, state } = waiter(fixedWait, { messages: () => [ownedFailure[0], missing] })
  await assert.rejects(run(420, savedUrl, { prompt: 'exact image prompt' }), /CHATGPT_IMAGE_INPUT_MISSING/)
  assert.equal(state.clock, 6000)
  assert.equal(state.progress.at(-1).stage, 'image_input_missing')
  assert.equal(state.navigations.length, 0)
  for (const messages of [[{ Role: 'User', Text: 'other prompt' }, missing],
    [missing, ownedFailure[0]], [ownedFailure[0], { ...missing, Text: 'The earlier response said: ' + missing.Text }]]) {
    const other = waiter(fixedWait, { messages: () => messages })
    assert.deepEqual(Array.from(await other.run(12, savedUrl, { prompt: 'exact image prompt' })), [])
  }
})

test('a request for the preceding illustration to preserve continuity ends only its owned idle wait', async () => {
  const text = 'Please upload the preceding illustration so I can preserve the exact floral tile motif, character design, and visual continuity while creating this frame.'
  for (const variant of [text, text.replaceAll(' ', '  '), text.replace('preceding', 'previous'),
    'I couldn’t generate the illustration because the image tool requires an existing image reference for this request. Please upload the reference frame so I can create the scene with the repeating floral tiles, empty dashed gap, and single hovering star tile.',
    text + '\nImage generation failed\nTry again']) {
    const response = { Role: 'Assistant', Text: variant }
    const { run, state } = waiter(fixedWait, { messages: () => [ownedFailure[0], response] })
    await assert.rejects(run(420, savedUrl, { prompt: 'exact image prompt' }), /CHATGPT_IMAGE_INPUT_MISSING/)
    assert.equal(state.clock, 6000)
    assert.equal(state.progress.at(-1).stage, 'image_input_missing')
    assert.equal(state.navigations.length, 0)
  }
  const response = { Role: 'Assistant', Text: text }
  for (const options of [
    { messages: () => [{ Role: 'User', Text: 'other prompt' }, response] },
    { messages: () => [response, ownedFailure[0]] },
    { messages: () => [ownedFailure[0], { ...response, Text: 'The previous response said: ' + text }] },
    { messages: () => [ownedFailure[0], response], generating: () => true },
    { messages: () => [ownedFailure[0], response], images: () => ['data:image/png;base64,preview'] },
  ]) {
    const { run, state } = waiter(fixedWait, options)
    try { await run(12, savedUrl, { prompt: 'exact image prompt' }) }
    catch (error) { assert.doesNotMatch(error.message, /CHATGPT_IMAGE_(INPUT_MISSING|GENERATION_FAILED)/) }
    assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
  }
  const completed = waiter(fixedWait, {
    messages: () => [ownedFailure[0], response],
    images: state => state.clock >= 6000 ? [imageUrl] : [],
  })
  assert.deepEqual(Array.from(await completed.run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
})

test('completed image error ends the owned wait after two stable idle readings', async () => {
  const { run, state } = waiter(fixedWait, { messages: () => ownedFailure })
  await assert.rejects(run(420, savedUrl, { prompt: 'exact image prompt' }),
    error => /CHATGPT_IMAGE_GENERATION_FAILED/.test(error.message) && error.message.includes(savedUrl))
  assert.equal(state.clock, 6000)
  assert.equal(state.navigations.length, 0)
  assert.equal(state.progress.at(-1).stage, 'image_generation_failed')
})

const failedImageWidget = 'Something went wrong while generating your image. Sorry about that.'

test('fixed image failure widget overrides a stale Stop button only in its owned empty turn', async () => {
  for (const generating of [false, true]) {
    for (const text of [failedImageWidget, failedImageWidget.replaceAll(' ', '  ')]) {
      const { run, state } = waiter(fixedWait, {
        generating: () => generating,
        messages: () => [ownedFailure[0], { Role: 'Assistant', Text: text }],
      })
      await assert.rejects(run(420, savedUrl, { prompt: 'exact image prompt' }),
        /CHATGPT_IMAGE_GENERATION_FAILED/)
      assert.equal(state.clock, 6000)
      assert.equal(state.navigations.length, 0)
      assert.equal(state.progress.at(-1).stage, 'image_generation_failed')
      assert.equal(state.messageReadOptions.expectedPrompt, 'exact image prompt')
    }
  }
})

test('failure widget cannot end an unrelated turn, a quoted error, or an image with output', async () => {
  const response = { Role: 'Assistant', Text: failedImageWidget }
  for (const options of [
    { messages: () => [{ Role: 'User', Text: 'different prompt' }, response] },
    { messages: () => [response, ownedFailure[0]] },
    { messages: () => [response] },
    { messages: () => [ownedFailure[0], { ...response, Text: 'The prior response said: ' + failedImageWidget }] },
    { messages: () => [ownedFailure[0], { ...response, Text: failedImageWidget + ' I am trying again.' }] },
    { messages: () => [ownedFailure[0], response], images: () => ['data:image/png;base64,preview'] },
    { messages: () => [ownedFailure[0], response], images: () => [imageUrl] },
  ]) {
    const { run, state } = waiter(fixedWait, { generating: () => true, ...options })
    await assert.rejects(run(12, savedUrl, { prompt: 'exact image prompt' }), /No stable finished image/)
    assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
  }
})

test('one failure widget reading cannot prevent a subsequent image from completing', async () => {
  const { run, state } = waiter(fixedWait, {
    generating: state => state.clock < 6000,
    messages: () => [ownedFailure[0], { Role: 'Assistant', Text: failedImageWidget }],
    images: state => state.clock >= 6000 ? [imageUrl] : [],
  })
  assert.deepEqual(Array.from(await run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
  assert.equal(state.clock, 9000)
})

test('a disappearing failure widget resets its confirmation even when Stop remains visible', async () => {
  const { run, state } = waiter(fixedWait, {
    generating: () => true,
    messages: state => [ownedFailure[0], {
      Role: 'Assistant', Text: state.clock === 6000 ? 'Creating image' : failedImageWidget,
    }],
  })
  await assert.rejects(run(30, savedUrl, { prompt: 'exact image prompt' }), /CHATGPT_IMAGE_GENERATION_FAILED/)
  assert.equal(state.clock, 12000)
})

test('standalone illustration failure with a reference request ends its owned wait', async () => {
  const text = "I couldn't generate the new illustration in this attempt. The image tool requires an image reference, even though your request is for a new standalone frame.\n\nPlease upload the earlier image so I can correct the magnifying glass, ensure the enlarged gauge matches the area beneath it, and show the character actively examining the clipboard."
  for (const variant of [text, text.replaceAll(' ', '  '), text.replace('\n\n', ''), text.replace("couldn't", 'couldn’t') + '\nImage generation failed\nTry again']) {
    const response = { Role: 'Assistant', Text: variant }
    const { run, state } = waiter(fixedWait, { messages: () => [ownedFailure[0], response] })
    await assert.rejects(run(420, savedUrl, { prompt: 'exact image prompt' }), /CHATGPT_IMAGE_INPUT_MISSING/)
    assert.equal(state.clock, 6000)
    assert.equal(state.progress.at(-1).stage, 'image_input_missing')
    assert.equal(state.navigations.length, 0)
  }
  for (const options of [
    { messages: () => [{ Role: 'User', Text: 'other prompt' }, { Role: 'Assistant', Text: text }] },
    { messages: () => [{ Role: 'Assistant', Text: text }, ownedFailure[0]] },
    { messages: () => [ownedFailure[0], { Role: 'Assistant', Text: 'The previous response said: ' + text }] },
    { messages: () => [ownedFailure[0], { Role: 'Assistant', Text: text }], generating: () => true },
    { messages: () => [ownedFailure[0], { Role: 'Assistant', Text: text }], images: () => ['data:image/png;base64,preview'] },
  ]) {
    const { run, state } = waiter(fixedWait, options)
    try { await run(12, savedUrl, { prompt: 'exact image prompt' }) }
    catch (error) { assert.doesNotMatch(error.message, /CHATGPT_IMAGE_(INPUT_MISSING|GENERATION_FAILED)/) }
    assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
  }
})

test('observed attempt failure with explanatory prose ends the owned wait', async () => {
  const text = "I couldn't generate the image in this attempt. Your brief is clear and specifies an original 16:9 editorial collage, so no additional reference image should be necessary."
  for (const variant of [text, text.replace("couldn't", 'couldn’t'), text + '\nImage generation failed\nTry again']) {
    const messages = [ownedFailure[0], { Role: 'Assistant', Text: variant }]
    const { run, state } = waiter(fixedWait, { messages: () => messages })
    await assert.rejects(run(420, savedUrl, { prompt: 'exact image prompt' }), /CHATGPT_IMAGE_GENERATION_FAILED/)
    assert.equal(state.clock, 6000)
    assert.equal(state.navigations.length, 0)
    assert.equal(state.progress.at(-1).stage, 'image_generation_failed')
  }
  for (const messages of [
    [{ Role: 'User', Text: 'other prompt' }, { Role: 'Assistant', Text: text }],
    [{ Role: 'Assistant', Text: text }, ownedFailure[0]],
    [ownedFailure[0], { Role: 'Assistant', Text: 'The previous response said: ' + text }],
  ]) {
    const { run } = waiter(fixedWait, { messages: () => messages })
    assert.deepEqual(Array.from(await run(12, savedUrl, { prompt: 'exact image prompt' })), [])
  }
  const { run } = waiter(fixedWait, {
    messages: () => [ownedFailure[0], { Role: 'Assistant', Text: text }],
    generating: state => state.clock < 9000,
    images: state => state.clock >= 9000 ? [imageUrl] : [],
  })
  assert.deepEqual(Array.from(await run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
})

test('completed guardrail refusal ends only its own idle image turn', async () => {
  const refusal = "We’re so sorry, but the image we created may violate our guardrails around violence. If you think we got it wrong, please retry or edit your prompt."
  const similarity = refusal.replace('around violence', 'concerning similarity to third-party content')
  for (const text of [refusal, refusal.replace('We’re', "We're"), similarity]) {
    const messages = [ownedFailure[0], { Role: 'Assistant', Text: text }]
    const { run, state } = waiter(fixedWait, { messages: () => messages })
    const diagnostics = []
    await assert.rejects(run(420, savedUrl, {
      prompt: 'exact image prompt',
      onDiagnostic(observation, url) { diagnostics.push({ ...observation, url }) },
    }), /CHATGPT_IMAGE_GENERATION_FAILED/)
    assert.deepEqual(diagnostics, [{
      terminal_error: 'CHATGPT_IMAGE_GENERATION_FAILED', provider_message: text, url: savedUrl,
    }])
    assert.equal(state.clock, 6000)
    assert.equal(state.progress.at(-1).stage, 'image_generation_failed')
    assert.equal(state.navigations.length, 0)
  }
  const response = { Role: 'Assistant', Text: similarity }
  for (const options of [
    { messages: () => [{ Role: 'User', Text: 'different prompt' }, response] },
    { messages: () => [response, ownedFailure[0]] },
    { messages: () => [ownedFailure[0], { ...response, Text: 'The earlier response said: ' + similarity }] },
    { messages: () => [ownedFailure[0], response], generating: () => true },
    { messages: () => [ownedFailure[0], response], images: () => ['data:image/png;base64,preview'] },
  ]) {
    const { run, state } = waiter(fixedWait, options)
    try { await run(12, savedUrl, { prompt: 'exact image prompt' }) }
    catch (error) { assert.doesNotMatch(error.message, /CHATGPT_IMAGE_GENERATION_FAILED/) }
    assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
  }
  const { run } = waiter(fixedWait, {
    messages: () => [ownedFailure[0], response],
    images: state => state.clock >= 6000 ? [imageUrl] : [],
  })
  assert.deepEqual(Array.from(await run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
})

test('reproduces full-deadline wait on the installed adapter for a completed provider error', async t => {
  const legacy = waitSource(originals.get('clis/chatgpt/utils.js').toString())
  if (legacy.includes('CHATGPT_IMAGE_GENERATION_FAILED')) return t.skip('Installed runtime already detects terminal errors')
  const { run, state } = waiter(legacy, { messages: () => ownedFailure })
  assert.deepEqual(Array.from(await run(420, savedUrl, { prompt: 'exact image prompt' })), [])
  assert.ok(state.clock >= 420000)
})

for (const [label, messages] of [
  ['different request', [{ Role: 'User', Text: 'other prompt' }, ownedFailure[1]]],
  ['older reply', [ownedFailure[1], ownedFailure[0]]],
  ['unhydrated user', [ownedFailure[1]]],
  ['quoted error', [ownedFailure[0], { Role: 'Assistant', Text: `The earlier error was: ${imageFailure}` }]],
]) {
  test(`does not treat ${label} as a terminal image failure`, async () => {
    const { run, state } = waiter(fixedWait, { messages: () => messages })
    assert.deepEqual(Array.from(await run(12, savedUrl, { prompt: 'exact image prompt' })), [])
    assert.equal(state.progress.at(-1).stage, 'image_wait_timeout')
  })
}

test('single error sighting does not reject an image that subsequently finishes', async () => {
  const { run, state } = waiter(fixedWait, {
    messages: () => ownedFailure, images: state => state.clock >= 6000 ? [imageUrl] : [],
  })
  assert.deepEqual(Array.from(await run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
  assert.equal(state.clock, 9000)
})

test('generation restarting between error sightings resets the failure confirmation', async () => {
  const { run } = waiter(fixedWait, {
    messages: () => ownedFailure, generating: state => state.clock === 6000,
    images: state => state.clock >= 12000 ? [imageUrl] : [],
  })
  assert.deepEqual(Array.from(await run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
})

for (const rendering of ['active generation', 'canvas preview']) {
  test(`${rendering} prevents stale failure text from terminating an image request`, async () => {
    const { run, state } = waiter(fixedWait, {
      messages: () => ownedFailure,
      generating: state => rendering === 'active generation' && state.clock < 12000,
      images: state => state.clock >= 12000 ? [imageUrl]
        : rendering === 'canvas preview' ? ['data:image/png;base64,unfinished'] : [],
    })
    assert.deepEqual(Array.from(await run(30, savedUrl, { prompt: 'exact image prompt' })), [imageUrl])
    assert.equal(state.progress.at(-1).stage, 'images_detected')
  })
}

test('known live local route remains in place while its canonical image finishes', async () => {
  const { run, state } = waiter(fixedWait, { url: localUrl,
    generating: state => state.clock < 15000, images: () => [imageUrl] })
  assert.deepEqual(Array.from(await run(30, savedUrl, { localConversationUrl: localUrl })), [imageUrl])
  assert.equal(state.navigations.length, 0)
})

test('a collapsed long prompt is verified before adopting its saved conversation identity', async () => {
  const prompt = 'Generate an image of: ' + 'owned thumbnail detail '.repeat(700)
  for (const url of [localUrl, savedUrl]) {
    const { run, state } = waiter(fixedWait, {
      url, identity: { conversationUrl: savedUrl, ...(url === localUrl ? { localConversationUrl: localUrl } : {}) },
      messages: state => [{
        Role: 'User', Text: state.messageReadOptions.expectedPrompt === prompt ? prompt : prompt.slice(0, 10240),
      }],
      images: () => [imageUrl],
    })
    assert.deepEqual(Array.from(await run(30, localUrl, { prompt })), [imageUrl])
    assert.ok(state.progress.some(entry => entry.stage === 'waiting' && entry.url === savedUrl))
    assert.equal(state.navigations.length, 0)
  }
})

test('persist canonical identity even when the owned image URL stays local', async () => {
  const { run, state } = waiter(fixedWait, { url: localUrl,
    identity: { conversationUrl: savedUrl, localConversationUrl: localUrl },
    images: () => [imageUrl] })
  assert.deepEqual(Array.from(await run(30, localUrl, { prompt: 'exact image prompt' })), [imageUrl])
  assert.equal(state.progress.at(-1).url, savedUrl)
  assert.equal(state.navigations.length, 0)
  for (const options of [
    { actualPrompt: 'different prompt' },
    { identity: { conversationUrl: savedUrl, localConversationUrl: localUrl + '-other' } },
  ]) {
    const unowned = waiter(fixedWait, { url: localUrl,
      identity: { conversationUrl: savedUrl, localConversationUrl: localUrl }, ...options })
    await unowned.run(9, localUrl, { prompt: 'exact image prompt' })
    assert.ok(unowned.state.progress.every(row => row.url === localUrl))
    assert.equal(unowned.state.navigations.length, 0)
  }
})

test('long image identity expands only the latest exact-prefix user message', async () => {
  const start = patchedUtils.indexOf('export async function getVisibleMessages(')
  const end = patchedUtils.indexOf('function formatChatGPTDetailMessages(', start)
  const read = vm.runInNewContext(patchedUtils.slice(start, end).replace('export ', '') + '\ngetVisibleMessages', {
    unwrapEvaluateResult: value => value, requireArrayEvaluateResult: value => value,
    chatgptRateLimitGuardScript: () => '',
  })
  const expected = 'x'.repeat(10240) + ' complete ending'
  for (const [prefix, full, wanted] of [
    [expected.slice(0, 10240), expected, 1],
    ['unrelated'.repeat(1280), expected, 0],
    [expected.slice(0, 10240), expected + ' wrong ending', 1],
  ]) {
    let clicks = 0; let sleeps = 0; const content = { textContent: prefix }
    const button = { textContent: 'Show more', click() { clicks++; content.textContent = full } }
    const user = { getAttribute: () => 'turn:0:user', querySelector: () => content,
      querySelectorAll: () => [button] }
    const page = {
      async sleep() { sleeps++ },
      async evaluate(script) {
        if (script.includes('const expected =')) return vm.runInNewContext(script, {
          document: { querySelectorAll: () => [user] },
        })
        return [{ role: 'User', text: content.textContent }]
      },
    }
    const messages = await read(page, { textOnly: true, expectedPrompt: expected })
    assert.equal(clicks, wanted); assert.equal(sleeps, wanted)
    // Expansion only reveals evidence; it never makes a partial match exact.
    assert.equal(messages[0].Text === expected, wanted === 1 && full === expected)
  }
})

test('local route can naturally become saved only with the exact submitted prompt', async () => {
  const { run, state } = waiter(fixedWait, { images: () => [imageUrl],
    identity: { conversationUrl: savedUrl } })
  assert.deepEqual(Array.from(await run(30, localUrl, { prompt: 'exact image prompt' })), [imageUrl])
  assert.equal(state.progress[0].url, savedUrl)
  assert.equal(state.navigations.length, 0)
})

test('saved route waits for hydrated messages before validating the original image prompt', async () => {
  const { run, state } = waiter(fixedWait, { images: () => [imageUrl],
    identity: { conversationUrl: savedUrl },
    messages: state => state.clock < 12000 ? [] : [{ Role: 'User', Text: 'exact image prompt' }] })
  assert.deepEqual(Array.from(await run(30, localUrl, { prompt: 'exact image prompt' })), [imageUrl])
  assert.ok(state.clock >= 15000)
  assert.equal(state.navigations.length, 0)
})

test('a delayed first saved route is adopted from /new only after exact prompt verification', async () => {
  const { run, state } = waiter(fixedWait, { images: () => [imageUrl],
    identity: { conversationUrl: savedUrl } })
  assert.deepEqual(Array.from(await run(30, 'https://chatgpt.com/new', { prompt: 'exact image prompt' })), [imageUrl])
  assert.equal(state.progress[0].url, savedUrl)
  assert.equal(state.navigations.length, 0)
})

test('a delayed unsaved local route is adopted from /new only after exact prompt verification', async () => {
  const { run, state } = waiter(fixedWait, { url: localUrl, images: () => [imageUrl] })
  assert.deepEqual(Array.from(await run(30, 'https://chatgpt.com/new', { prompt: 'exact image prompt' })), [imageUrl])
  assert.equal(state.progress[0].url, localUrl)
  assert.equal(state.navigations.length, 0)
})

test('a transient empty location read waits without navigating or accepting images', async () => {
  const { run, state } = waiter(fixedWait, { readUrl: state => state.reads === 1 ? '' : savedUrl,
    images: () => [imageUrl] })
  assert.deepEqual(Array.from(await run()), [imageUrl])
  assert.equal(state.reads, 3)
  assert.equal(state.navigations.length, 0)
})

for (const actualPrompt of ['different prompt', '']) {
  test(`unowned saved route is rejected without reload or replay (${actualPrompt || 'empty'})`, async () => {
    const { run, state } = waiter(fixedWait, { actualPrompt: actualPrompt || 'unrelated',
      identity: { conversationUrl: savedUrl }, images: () => [imageUrl] })
    await assert.rejects(run(30, localUrl, { prompt: 'exact image prompt' }), /left its submitted conversation/)
    assert.equal(state.navigations.length, 0)
  })
}

test('unrelated conversation is never navigated back or used as an image result', async () => {
  const { run, state } = waiter(fixedWait, { url: 'https://chatgpt.com/c/other1234', images: () => [imageUrl] })
  await assert.rejects(run(), /left its submitted conversation/)
  assert.equal(state.navigations.length, 0)
})

for (const kind of ['generating', 'canvas']) {
  test(`${kind} timeout preserves the conversation URL and never exports a partial image`, async () => {
    const { run, state } = waiter(fixedWait, {
      generating: () => kind === 'generating',
      images: () => kind === 'canvas' ? ['data:image/png;base64,unfinished'] : [],
    })
    await assert.rejects(run(12), error => error.message.includes(savedUrl) && /deadline/.test(error.message))
    assert.equal(state.clock, 12000)
  })
}

test('one image sighting is not enough to export at the response deadline', async () => {
  const { run } = waiter(fixedWait, { images: () => [imageUrl] })
  await assert.rejects(run(6), /No stable finished image/)
})

test('image command records submission, wait failure and canonical link without prompt text', async () => {
  const source = fs.readFileSync(path.join(copied, 'clis/chatgpt/image.js'), 'utf8')
    .replace(/^import .*\n/gm, '').replaceAll('export ', '')
  const diagnostics = []
  const sent = []
  const navigations = []
  const command = vm.runInNewContext(source + '\nimageCommand', {
    os, path, fs, cli: value => value, Strategy: { COOKIE: 'cookie' },
    ArgumentError: AdapterError, CommandExecutionError: AdapterError, EmptyResultError: AdapterError,
    console: { error: value => diagnostics.push(JSON.parse(value.slice('[chatgpt/image] '.length))) },
    normalizeBooleanFlag: Boolean, unwrapEvaluateResult: value => value,
    async ensureChatGPTComposer() { return { url: 'https://chatgpt.com/' } },
    async clearChatGPTDraft() {}, async getChatGPTVisibleImageUrls() { return [] },
    async sendChatGPTMessage(_page, value) { sent.push(value); return true },
    async resolveChatGPTConversationIdentity() { return { conversationUrl: savedUrl, localConversationUrl: localUrl } },
    async waitForChatGPTImages(_page, _before, timeout, url, options) {
      assert.equal(timeout, 360); assert.equal(url, savedUrl)
      assert.equal(options.localConversationUrl, localUrl)
      assert.equal(options.prompt, sent[0])
      options.onDiagnostic({ generated_image_count: 0 }, url)
      options.onProgress('image_wait_timeout', url)
      throw new AdapterError('Generation timed out')
    },
  })
  await assert.rejects(command.func({ async goto(url) { navigations.push(url) } },
    { prompt: 'Private thumbnail prompt', timeout: 360 }), /Generation timed out/)
  assert.equal(sent.length, 1)
  assert.deepEqual(navigations, ['https://chatgpt.com/new'])
  assert.deepEqual(diagnostics.map(item => item.stage), [
    'preparing', 'prompt_submitted', 'waiting', 'image_wait_diagnostic', 'image_wait_timeout', 'image_wait_failed',
  ])
  assert.equal(diagnostics.at(-1).conversation_url, savedUrl)
  assert.ok(!JSON.stringify(diagnostics).includes('Private thumbnail prompt'))
})

test('unready or wrong-origin composer never records submission or sends a prompt', async () => {
  const source = fs.readFileSync(path.join(copied, 'clis/chatgpt/image.js'), 'utf8')
    .replace(/^import .*\n/gm, '').replaceAll('export ', '')
  for (const wrongOrigin of [false, true]) {
    const stateFile = path.join(temporary, `unready-image-${wrongOrigin}.json`)
    let sends = 0
    const command = vm.runInNewContext(source + '\nimageCommand', {
      os, path, fs, cli: value => value, Strategy: { COOKIE: 'cookie' },
      ArgumentError: AdapterError, CommandExecutionError: AdapterError, EmptyResultError: AdapterError,
      console: { error() {} }, normalizeBooleanFlag: Boolean,
      async ensureChatGPTComposer() {
        if (!wrongOrigin) throw new AdapterError('ChatGPT composer is not available')
        return { url: 'about:blank' }
      },
      async sendChatGPTMessage() { sends++; return true },
    })
    await assert.rejects(command.func({ async goto() {} },
      { prompt: 'must remain unsent', timeout: 30, 'state-file': stateFile }), /composer/)
    assert.equal(sends, 0)
    assert.equal(fs.existsSync(stateFile), false)
  }
})

test('image navigation retries the same owned target and remains bounded', async () => {
  const source = fs.readFileSync(path.join(runtime, 'patches/chatgpt-image-request.js'), 'utf8').replaceAll('export ', '')
  const prepare = vm.runInNewContext(source + '\nprepareChatGPTImageComposer', {})
  const calls = []
  await prepare({
    async goto(url) { calls.push(['goto', url]); if (calls.length === 1) throw new Error('Navigation rejected.') },
    async sleep(seconds) { calls.push(['wait', seconds]) },
  })
  assert.deepEqual(calls, [
    ['goto', 'https://chatgpt.com/new'], ['wait', 1], ['goto', 'https://chatgpt.com/new'],
  ])
  let navigations = 0; let waits = 0
  await assert.rejects(prepare({
    async goto() { navigations++; throw new Error('Navigation rejected.') },
    async sleep() { waits++ },
  }), /Navigation rejected/)
  assert.equal(navigations, 3); assert.equal(waits, 2)
  await assert.rejects(prepare({
    async goto() { throw new Error('Browser permission denied') },
    async sleep() { assert.fail('Permission failures must not retry') },
  }), /permission denied/)
})

test('image setup/export allowance matches Python and preserves other command budgets', () => {
  const source = fs.readFileSync(path.join(copied, 'dist/src/execution.js'), 'utf8')
  const start = source.indexOf('const attachmentSetupSeconds =')
  const end = source.indexOf('const commandRun =', start)
  const budget = (cmd, kwargs = {}) => vm.runInNewContext(source.slice(start, end) + '\nbrowserTimeout', {
    cmd, kwargs, userTimeoutSec: 360, RUNTIME_TIMEOUT_PADDING_SECONDS: 30,
  })
  assert.equal(budget({ site: 'chatgpt', name: 'image' }), 570)
  assert.equal(budget({ site: 'chatgpt', name: 'ask' }), 390)
  assert.equal(budget({ site: 'gemini', name: 'ask' }, { file: '/mock/image.jpg' }), 570)
})

test('image timeout checkpoint recovers the original prompt without a second send', async () => {
  const stateFile = path.join(temporary, 'image-request.json')
  const source = fs.readFileSync(path.join(copied, 'clis/chatgpt/image.js'), 'utf8')
    .replace(/^import .*\n/gm, '').replaceAll('export ', '')
  const sends = []; const navigations = []; let waits = 0
  const command = vm.runInNewContext(source + '\nimageCommand', {
    os, path, fs, Date, cli: value => value, Strategy: { COOKIE: 'cookie' },
    ArgumentError: AdapterError, CommandExecutionError: AdapterError, EmptyResultError: AdapterError,
    console: { error() {} }, normalizeBooleanFlag: Boolean,
    async ensureChatGPTComposer() { return { url: 'https://chatgpt.com/' } },
    async clearChatGPTDraft() {}, async getChatGPTVisibleImageUrls() { return [] },
    async sendChatGPTMessage(_page, value) { sends.push(value); return true },
    async resolveChatGPTConversationIdentity() { return { conversationUrl: savedUrl } },
    async getVisibleMessages() { return [{ Role: 'User', Text: sends[0] }] },
    chatGPTPromptMatches: (a, b) => a === b,
    parseChatGPTConversationId: url => url.split('/c/')[1],
    async waitForChatGPTImages(_page, _before, _timeout, url, options) {
      const checkpoint = fs.readFileSync(stateFile, 'utf8')
      options.onDiagnostic({ generated_image_count: 0 }, url)
      assert.equal(fs.readFileSync(stateFile, 'utf8'), checkpoint)
      if (++waits === 1) throw new AdapterError('response timeout')
      return [imageUrl]
    },
  })
  const page = { async goto(url) { navigations.push(url) } }
  const args = { prompt: 'original still', timeout: 30, sd: true, 'state-file': stateFile }
  await assert.rejects(command.func(page, args), /response timeout/)
  assert.equal(JSON.parse(fs.readFileSync(stateFile)).stage, 'image_wait_failed')
  const result = await command.func(page, args)
  assert.equal(result[0].link, `🔗 ${savedUrl}`)
  assert.equal(sends.length, 1)
  assert.deepEqual(navigations, ['https://chatgpt.com/new', savedUrl])
  await assert.rejects(command.func(page, { ...args, prompt: 'different still' }), /saved image prompt differs/)
  const prior = JSON.parse(fs.readFileSync(stateFile))
  fs.writeFileSync(stateFile, JSON.stringify({ ...prior, stage: 'submitting', conversationUrl: '' }))
  await assert.rejects(command.func(page, args), /no saved conversation URL/)
  assert.equal(sends.length, 1)
  assert.equal(navigations.length, 2)
})

test('image composer waits for hydration in the same slot and fails within a bounded deadline', async () => {
  const helper = fs.readFileSync(path.join(runtime, 'patches/chatgpt-image-request.js'), 'utf8').replaceAll('export ', '')
  for (const readyAt of [3000, Infinity]) {
    let clock = 0
    const wait = vm.runInNewContext(helper + '\nwaitForChatGPTImageComposer', {
      Date: { now: () => clock },
      async ensureChatGPTComposer() {
        if (clock < readyAt) throw new Error('ChatGPT composer is not available on the current page.')
        return { hasComposer: true }
      },
    })
    const result = wait({
      async sleep(seconds) { clock += seconds * 1000 },
      async evaluate() { return false },
    })
    if (readyAt === Infinity) await assert.rejects(result, /composer is not available/)
    else assert.equal((await result).hasComposer, true)
    assert.equal(clock, Math.min(readyAt, 30000))
  }
  const wait = vm.runInNewContext(helper + '\nwaitForChatGPTImageComposer', {
    Date, async ensureChatGPTComposer() { throw new Error('AUTH_REQUIRED') },
  })
  await assert.rejects(wait({}), /AUTH_REQUIRED/)
})

test('image composer recovers only an empty home once within the original deadline', async () => {
  const helper = fs.readFileSync(path.join(runtime, 'patches/chatgpt-image-request.js'), 'utf8').replaceAll('export ', '')
  for (const options of [
    { url: 'https://chatgpt.com/', readyAfterReload: true },
    { url: 'https://chatgpt.com/new', readyAfterReload: true },
    { url: 'https://chatgpt.com/', readyAfterReload: false },
    { url: savedUrl, readyAfterReload: true },
    { url: 'https://example.com/', readyAfterReload: true },
    { url: 'https://chatgpt.com/', messages: true, readyAfterReload: true },
    { url: 'https://chatgpt.com/', draft: 'unsent user text', readyAfterReload: true },
  ]) {
    let clock = 0; let reloads = 0; let evaluations = 0
    const wait = vm.runInNewContext(helper + '\nwaitForChatGPTImageComposer', {
      Date: { now: () => clock },
      async ensureChatGPTComposer() {
        if (reloads && options.readyAfterReload) return { hasComposer: true }
        throw new Error('ChatGPT composer is not available on the current page.')
      },
    })
    const result = wait({
      async sleep(seconds) { clock += seconds * 1000 },
      async evaluate(script) {
        evaluations++
        return vm.runInNewContext(script, {
          URL,
          window: { location: { href: options.url, reload() { reloads++ } } },
          document: {
            querySelector() { return options.messages ? {} : null },
            querySelectorAll() { return options.draft ? [{ textContent: options.draft }] : [] },
          },
        })
      },
    })
    const freshHome = ['https://chatgpt.com/', 'https://chatgpt.com/new'].includes(options.url)
      && !options.messages && !options.draft
    if (freshHome && options.readyAfterReload) {
      assert.equal((await result).hasComposer, true)
      assert.ok(clock >= 10000 && clock < 30000)
    } else {
      await assert.rejects(result, /composer is not available/)
      assert.equal(clock, 30000)
    }
    assert.equal(reloads, freshHome ? 1 : 0, JSON.stringify(options))
    assert.equal(evaluations, 1, JSON.stringify(options))
  }
})

test('image composer does not retry authentication errors with the generic composer message', async () => {
  const helper = fs.readFileSync(path.join(runtime, 'patches/chatgpt-image-request.js'), 'utf8').replaceAll('export ', '')
  let clock = 0
  const authError = Object.assign(new Error('ChatGPT composer is not available on the current page.'), {
    code: 'AUTH_REQUIRED',
  })
  const wait = vm.runInNewContext(helper + '\nwaitForChatGPTImageComposer', {
    Date: { now: () => clock },
    async ensureChatGPTComposer() { throw authError },
  })
  await assert.rejects(wait({
    async sleep(seconds) { clock += seconds * 1000 },
    async evaluate() { assert.fail('Authentication failure must not reload') },
  }), error => error === authError)
  assert.equal(clock, 0)
})

test('image recovery rejects a different visible user prompt and never submits', async () => {
  const helper = fs.readFileSync(path.join(runtime, 'patches/chatgpt-image-request.js'), 'utf8').replaceAll('export ', '')
  const recover = vm.runInNewContext(helper + '\nrecoverChatGPTImageRequest', {
    Date, CommandExecutionError: AdapterError,
    async getVisibleMessages() { return [{ Role: 'User', Text: 'someone else' }] },
    chatGPTPromptMatches: (a, b) => a === b,
  })
  await assert.rejects(recover({ async goto() {} }, { conversationUrl: savedUrl }, 'owned prompt', 30), /recovery prompt mismatch/)
})
