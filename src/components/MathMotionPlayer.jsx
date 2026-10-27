import React from 'react'
import { Player } from '@remotion/player'
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { WALKTHROUGH_CAPTION } from '../viewModel'

function MathSequence({ steps }) {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()
  const totalFrames = steps.reduce((sum, step) => sum + (step.durationInFrames || fps * 3), 0)
  let cursor = 0
  let current = steps[0]
  let localFrame = 0
  let index = 0
  for (const [stepIndex, step] of steps.entries()) {
    const duration = step.durationInFrames || fps * 3
    if (frame < cursor + duration) {
      current = step
      localFrame = frame - cursor
      index = stepIndex
      break
    }
    cursor += duration
    index = stepIndex
  }
  const opacity = interpolate(localFrame, [0, 12, Math.max(13, (current.durationInFrames || 90) - 10), current.durationInFrames || 90], [0, 1, 1, .25], { extrapolateRight: 'clamp' })
  const latex = katex.renderToString(current.latex || '', { throwOnError: false, displayMode: true })
  return (
    <div className="motion-canvas">
      <div className="motion-label">STEP {String(index + 1).padStart(2, '0')} / {String(steps.length).padStart(2, '0')}</div>
      <div className="motion-equation" style={{ opacity }} dangerouslySetInnerHTML={{ __html: latex }} />
      <div className="motion-narration">{current.narration_text}</div>
      <div className="motion-progress"><span style={{ width: `${Math.min(100, frame / Math.max(1, durationInFrames) * 100)}%` }} /></div>
    </div>
  )
}

export default function MathMotionPlayer({ composition }) {
  const steps = composition?.steps || []
  if (!steps.length) {
    return (
      <div className="artifact-empty">
        <strong>No walkthrough for this paper</strong>
        <span>A concept walkthrough needs an extracted equation. None was found, so there is no preview and no MP4 was created.</span>
      </div>
    )
  }
  const duration = steps.reduce((sum, step) => sum + (step.durationInFrames || 90), 0)
  return (
    <div className="motion-player-wrap">
      <Player
        component={MathSequence}
        inputProps={{ steps }}
        durationInFrames={duration}
        fps={composition?.fps || 30}
        compositionWidth={640}
        compositionHeight={360}
        controls
        clickToPlay
        style={{ width: '100%', aspectRatio: '16 / 9', borderRadius: 8, overflow: 'hidden' }}
      />
      <p className="motion-caption">{WALKTHROUGH_CAPTION}</p>
    </div>
  )
}
