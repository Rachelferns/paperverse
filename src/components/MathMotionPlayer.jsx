import React from 'react'
import { Player } from '@remotion/player'
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const fallbackSteps = [
  { durationInFrames: 90, latex: String.raw`S = QK^T`, narration_text: 'First, compare every query with every key.' },
  { durationInFrames: 90, latex: String.raw`\hat S = \frac{QK^T}{\sqrt{d_k}}`, narration_text: 'Scale by the square root of the key dimension.' },
  { durationInFrames: 90, latex: String.raw`A = \operatorname{softmax}(\hat S)`, narration_text: 'Softmax turns the scores into attention weights.' },
  { durationInFrames: 90, latex: String.raw`O = AV`, narration_text: 'Finally, use the weights to blend value vectors.' },
]

function MathSequence({ steps }) {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()
  const totalFrames = steps.reduce((sum, step) => sum + (step.durationInFrames || fps * 3), 0)
  let cursor = 0
  let current = steps[0]
  let localFrame = 0
  for (const step of steps) {
    const duration = step.durationInFrames || fps * 3
    if (frame < cursor + duration) { current = step; localFrame = frame - cursor; break }
    cursor += duration
  }
  const opacity = interpolate(localFrame, [0, 12, Math.max(13, (current.durationInFrames || 90) - 10), current.durationInFrames || 90], [0, 1, 1, .25], { extrapolateRight: 'clamp' })
  const latex = katex.renderToString(current.latex || '', { throwOnError: false, displayMode: true })
  return <div className="motion-canvas"><div className="motion-orbit orbit-one"/><div className="motion-orbit orbit-two"/><div className="motion-label">ATTENTION / STEP {String(steps.indexOf(current) + 1).padStart(2, '0')}</div><div className="motion-equation" style={{ opacity, transform: `translateY(${(1-opacity)*12}px)` }} dangerouslySetInnerHTML={{ __html: latex }} /><div className="motion-narration">{current.narration_text}</div><div className="motion-progress"><span style={{ width: `${Math.min(100, frame / Math.max(1, durationInFrames) * 100)}%` }}/></div><div className="motion-frame">{String(frame).padStart(3,'0')} <i>/</i> {totalFrames}</div></div>
}

export default function MathMotionPlayer({ composition }) {
  const steps = composition?.steps?.length ? composition.steps : fallbackSteps
  if (composition && !composition.steps?.length) return <div className="artifact-empty"><span className="no-math-icon">ƒ</span><strong>No equation was extracted</strong><span>The local parser did not find display math in selectable PDF text, so there is no source-based animation to preview.</span></div>
  const duration = steps.reduce((sum, step) => sum + (step.durationInFrames || 90), 0)
  return <div className="motion-player-wrap"><Player component={MathSequence} inputProps={{ steps }} durationInFrames={duration} fps={composition?.fps || 30} compositionWidth={640} compositionHeight={360} controls clickToPlay doubleClickToFullscreen style={{ width: '100%', aspectRatio: '16 / 9', borderRadius: 7, overflow: 'hidden' }} /><p className="motion-caption">Editable Remotion preview · captions follow each derivation step</p></div>
}
