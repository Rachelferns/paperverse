export const ARCHITECTURE_MARKER = '%% paperverse-architecture: inferred'
export const ARCHITECTURE_UNAVAILABLE = 'PAPERVERSE_ARCHITECTURE_UNAVAILABLE'
export const WALKTHROUGH_CAPTION = 'Concept walkthrough preview. No audio track or MP4 is generated.'

export function readArchitecture(source) {
  const text = String(source || '').replace(/^\uFEFF/, '').trim()
  if (!text || text.startsWith(ARCHITECTURE_UNAVAILABLE)) {
    const note = text.startsWith(ARCHITECTURE_UNAVAILABLE) ? text.slice(ARCHITECTURE_UNAVAILABLE.length).trim() : ''
    return {
      available: false,
      note: note || 'No method architecture was inferred from the extracted text.',
      components: [],
      links: [],
      mermaid: '',
    }
  }
  if (!text.includes(ARCHITECTURE_MARKER)) {
    return {
      available: false,
      note: 'The saved diagram follows document headings. Those belong in the outline, not in a method architecture. Reprocess the paper to rebuild this view from the methodology text.',
      components: [],
      links: [],
      mermaid: '',
    }
  }
  const components = []
  const links = []
  let note = ''
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (trimmed.startsWith('%% note:')) note = trimmed.slice('%% note:'.length).trim()
    const component = trimmed.match(/^%% component:\s*([^|]+)\|\s*([^|]+)\|\s*(.*)$/)
    if (component) components.push({ id: component[1].trim(), label: component[2].trim(), detail: component[3].trim() })
    const link = trimmed.match(/^%% link:\s*([^|]+)\|\s*([^|]+)\|\s*(.*)$/)
    if (link) links.push({ src: link[1].trim(), dst: link[2].trim(), reason: link[3].trim() })
  }
  return { available: components.length > 0, note, components, links, mermaid: components.length ? text : '' }
}

export function equationStatus(equation) {
  const steps = Array.isArray(equation?.steps) ? equation.steps : []
  const checked = steps.filter(step => step?.sympy_verified)
  const unchecked = steps.filter(step => step && !step.sympy_verified)
  if (equation?.verification_status === 'partially_checked' || (checked.length && unchecked.length)) return 'partial'
  if (checked.length && !unchecked.length && steps.length) return 'verified'
  return 'extracted'
}

export function presentSymbol(symbol) {
  const dimensions = String(symbol?.dimensions || '')
  const definition = String(symbol?.definition || '').trim()
  if (dimensions === 'defined' || symbol?.status === 'defined') {
    return { status: 'defined', label: 'Defined in source', definition }
  }
  if (dimensions === 'occurrence' || symbol?.status === 'occurrence') {
    return { status: 'occurrence', label: 'Occurrence', definition }
  }
  const leftover = definition && !/^unknown$/i.test(definition) ? `${definition} ` : ''
  return {
    status: 'unknown',
    label: 'Not defined',
    definition: `${leftover}This symbol was indexed from an equation. A definition was not confirmed, so treat it as an occurrence.`.trim(),
  }
}

export function motionPresentation(composition) {
  const steps = Array.isArray(composition?.steps) ? composition.steps : []
  return {
    kind: 'storyboard',
    stepCount: steps.length,
    claimsMp4: Boolean(composition?.video_mp4_url),
    hasAudio: steps.some(step => step?.audio_url),
  }
}
