import assert from 'node:assert/strict'
import test from 'node:test'
import { ARCHITECTURE_UNAVAILABLE, WALKTHROUGH_CAPTION, equationStatus, motionPresentation, presentSymbol, readArchitecture } from './viewModel.js'

test('document headings are not treated as an architecture', () => {
  const legacy = `flowchart TD
  P["Attention Is All You Need"]
  S1["Abstract · p. 1"]
  S2["Introduction · p. 1"]
  P --> S1
  S1 --> S2`
  const reading = readArchitecture(legacy)
  assert.equal(reading.available, false)
  assert.equal(reading.components.length, 0)
  assert.match(reading.note, /outline/i)
})

test('a marked method diagram exposes components and not a fabricated fallback', () => {
  const source = `%% paperverse-architecture: inferred
%% note: Inferred interpretation of components named in Model Architecture.
%% component: encoder | Encoder | Maps an input sequence.
%% component: mha | Multi-head attention | Parallel attention.
%% link: encoder | mha | The decoder attends over the encoder output.
flowchart TD
  encoder["Encoder"]
  mha["Multi-head attention"]
  encoder --> mha`
  const reading = readArchitecture(source)
  assert.equal(reading.available, true)
  assert.deepEqual(reading.components.map(item => item.label), ['Encoder', 'Multi-head attention'])
  assert.equal(reading.links.length, 1)
  assert.equal(reading.components.some(item => item.label === 'Abstract'), false)
})

test('missing architecture stays empty', () => {
  const reading = readArchitecture(`${ARCHITECTURE_UNAVAILABLE}\nNo methodology section was found.`)
  assert.equal(reading.available, false)
  assert.equal(reading.mermaid, '')
  assert.match(reading.note, /methodology/i)
})

test('an extracted equation is not marked fully verified', () => {
  assert.equal(equationStatus({
    verification_status: 'extracted_only',
    steps: [{ sympy_verified: false, is_intermediate_derived: false }],
  }), 'extracted')
  assert.equal(equationStatus({
    verification_status: 'partially_checked',
    steps: [{ sympy_verified: false }, { sympy_verified: true, is_intermediate_derived: true }],
  }), 'partial')
})

test('the walkthrough caption does not claim an MP4 render', () => {
  assert.match(WALKTHROUGH_CAPTION, /concept walkthrough/i)
  assert.match(WALKTHROUGH_CAPTION, /no audio/i)
  assert.match(WALKTHROUGH_CAPTION, /no .{0,40}mp4/i)
  assert.equal(motionPresentation({ steps: [{ audio_url: null }] }).claimsMp4, false)
  assert.equal(motionPresentation({ steps: [], video_mp4_url: 'file.mp4' }).claimsMp4, true)
})

test('symbol occurrences are not labeled as unknown definitions', () => {
  const occurrence = presentSymbol({ symbol: 'W', dimensions: 'occurrence', definition: 'Occurrence in Loss. A definition was not extracted from the surrounding text.' })
  assert.equal(occurrence.label, 'Occurrence')
  assert.doesNotMatch(occurrence.label, /unknown/i)
  const legacy = presentSymbol({ symbol: 'Q', dimensions: 'Unknown', definition: 'Unknown' })
  assert.equal(legacy.label, 'Not defined')
  assert.match(legacy.definition, /occurrence/i)
})
