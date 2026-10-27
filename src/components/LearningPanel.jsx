import React, { Suspense, lazy, useEffect, useState } from 'react'
import { BrainCircuit, ChevronLeft, ChevronRight, Clipboard, Code2, Download, GitBranch, Play, Sigma } from 'lucide-react'
import ExtractedEquation from './ExtractedEquation'
import { readArchitecture } from '../viewModel'

const MathMotionPlayer = lazy(() => import('./MathMotionPlayer'))
const MermaidPreview = lazy(() => import('./MermaidPreview'))
const PyodideRunner = lazy(() => import('./PyodideRunner'))

const tabs = [
  { id: 'map', label: 'Method', icon: GitBranch },
  { id: 'equations', label: 'Equations', icon: Sigma },
  { id: 'motion', label: 'Steps', icon: Play },
  { id: 'learn', label: 'Study', icon: BrainCircuit },
  { id: 'code', label: 'Code', icon: Code2 },
]

function highlightCode(line) {
  const escaped = line.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  return <span dangerouslySetInnerHTML={{ __html: escaped.replace(/(#.*)$/g, '<span class="syn-comment">$1</span>').replace(/\b(import|from|def|return|print)\b/g, '<span class="syn-keyword">$1</span>').replace(/(\d+(?:\.\d+)?)/g, '<span class="syn-number">$1</span>') }} />
}

function relation(index, total) {
  if (total <= 1) return 'This is the only step. Nothing comes before or after it.'
  if (index === 0) return 'This is the first step. The next step continues from here.'
  if (index === total - 1) return 'This step follows the previous one. Nothing follows it.'
  return 'This step follows the previous one. The next step continues from here.'
}

function storyFrom(equations, composition) {
  const steps = equations?.[0]?.steps
  if (steps?.length) {
    return steps.map(step => ({
      title: step.is_intermediate_derived ? 'Derivation step' : 'Extracted equation',
      latex: step.latex,
      explanation: step.explanation,
      verified: Boolean(step.sympy_verified),
    }))
  }
  return (composition?.steps || []).map((step, index) => ({
    title: `Step ${index + 1}`,
    latex: step.latex,
    explanation: step.narration_text,
    verified: false,
  }))
}

function Empty({ title, children }) {
  return <div className="artifact-empty"><strong>{title}</strong><span>{children}</span></div>
}

export default function LearningPanel({ tab, setTab, paper, studyKit, focusedEquation, onExport, onCopy }) {
  const equations = studyKit?.equations || []
  const cards = studyKit?.flashcards || []
  const prompts = studyKit?.viva_questions || []
  const architecture = readArchitecture(studyKit?.diagram_mermaid)
  const story = storyFrom(equations, studyKit?.video_composition_props)
  const [step, setStep] = useState(0)
  const [card, setCard] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const activeCard = cards[card] || null
  const activeStep = story[step] || null

  useEffect(() => {
    setStep(0)
    setCard(0)
    setRevealed(false)
  }, [paper?.id, equations[0]?.equation_id, cards.length])

  useEffect(() => {
    if (tab === 'equations' && focusedEquation) document.getElementById(focusedEquation)?.scrollIntoView({ block: 'nearest' })
  }, [tab, focusedEquation])

  const sourceLine = activeCard
    ? [activeCard.source_section, activeCard.source_page ? `page ${activeCard.source_page}` : ''].filter(Boolean).join(' · ')
    : ''

  return (
    <aside className="right-sidebar">
      <div className="artifact-heading">
        <div>
          <span className="eyebrow">LEARNING TOOLS</span>
          <div className="artifact-title">From this paper</div>
        </div>
      </div>
      <div className="artifact-tabs" role="tablist">
        {tabs.map(item => {
          const Icon = item.icon
          return (
            <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} className={tab === item.id ? 'tab-selected' : ''} onClick={() => setTab(item.id)}>
              <Icon size={14} /><span>{item.label}</span>
            </button>
          )
        })}
      </div>

      {tab === 'map' && (
        <div className="artifact-panel" role="tabpanel">
          <h2>Method / architecture</h2>
          {!paper ? <Empty title="No paper loaded">Upload a PDF to look for a method diagram in that document.</Empty> : !architecture.available ? (
            <Empty title="No architecture diagram">{architecture.note}</Empty>
          ) : (
            <>
              <p className="source-flag">Inferred interpretation</p>
              <p className="panel-description">{architecture.note}</p>
              <div className="diagram-stage paper-diagram">
                <Suspense fallback={<p className="loading-inline">Preparing diagram…</p>}>
                  <MermaidPreview source={architecture.mermaid} />
                </Suspense>
              </div>
              <ul className="component-list">
                {architecture.components.map(item => (
                  <li key={item.id}><strong>{item.label}</strong><span>{item.detail}</span></li>
                ))}
              </ul>
              {architecture.links.length ? architecture.links.map(link => <p className="link-reason" key={`${link.src}-${link.dst}`}>{link.reason}</p>) : <p className="panel-description">No directed flow was stated, so the diagram has no arrows.</p>}
            </>
          )}
        </div>
      )}

      {tab === 'equations' && (
        <div className="artifact-panel" role="tabpanel">
          <h2>Equation explorer</h2>
          {!paper ? <Empty title="No paper loaded">Equations are extracted from the PDF you upload.</Empty> : equations.length ? equations.map((equation, index) => (
            <ExtractedEquation key={equation.equation_id || index} equation={equation} index={index} current={focusedEquation === equation.equation_id} />
          )) : <Empty title="No equations extracted">Display equations were not found in the selectable text. Scanned-page OCR is not enabled. Nothing here is marked as verified.</Empty>}
        </div>
      )}

      {tab === 'motion' && (
        <div className="artifact-panel" role="tabpanel">
          <h2>Concept walkthrough</h2>
          <p className="panel-description">A storyboard of the first extracted equation. This is a preview timeline, not a rendered video.</p>
          {!paper ? <Empty title="No paper loaded">A walkthrough is built from an equation in the uploaded paper.</Empty> : !story.length ? (
            <Empty title="No walkthrough for this paper">No equation was extracted, so there is no sequence to show and no MP4 was created.</Empty>
          ) : (
            <>
              {equations.length > 1 && <p className="panel-description">Other extracted equations stay in the Equations tab. This sequence follows the first one only.</p>}
              <article className="story-step">
                <h3>{activeStep.title}</h3>
                <p>{activeStep.explanation}</p>
                <p className="recall-meta">{activeStep.verified ? 'SymPy checked this step only.' : 'Not a verified derivation step.'} {relation(step, story.length)}</p>
              </article>
              <div className="story-nav">
                <button type="button" disabled={step === 0} onClick={() => setStep(step - 1)}><ChevronLeft size={14} /> Previous</button>
                <span>{step + 1} / {story.length}</span>
                <button type="button" disabled={step >= story.length - 1} onClick={() => setStep(step + 1)}>Next <ChevronRight size={14} /></button>
              </div>
              <details className="timeline-preview">
                <summary>Play the timeline preview</summary>
                <Suspense fallback={<p className="loading-inline">Loading preview…</p>}>
                  <MathMotionPlayer composition={studyKit?.video_composition_props} />
                </Suspense>
              </details>
            </>
          )}
        </div>
      )}

      {tab === 'learn' && (
        <div className="artifact-panel" role="tabpanel">
          <h2>Study cards</h2>
          <p className="panel-description">One question at a time, built from extracted text. No language model is configured.</p>
          {!paper ? <Empty title="No paper loaded">Study cards are written from the paper you upload.</Empty> : !activeCard ? (
            <Empty title="Not enough extracted text">This paper does not have an abstract, method section, or equation that can support a review question.</Empty>
          ) : (
            <>
              <article className="recall-card">
                <span className="recall-meta">Question {card + 1} of {cards.length}</span>
                <p>{activeCard.question}</p>
                {revealed ? (
                  <div className="recall-answer">
                    <p>{activeCard.answer}</p>
                    {activeCard.explanation ? <p className="recall-meta">{activeCard.origin === 'extracted' ? 'From extracted text. ' : activeCard.origin === 'generated' ? 'Generated from extracted text. ' : ''}{activeCard.explanation}</p> : null}
                    <p className="recall-meta">{sourceLine ? `Source: ${sourceLine}` : 'Source location was not stored for this card.'}</p>
                    <button type="button" className="text-action" onClick={() => setRevealed(false)}>Hide answer</button>
                  </div>
                ) : <button type="button" className="secondary-action" onClick={() => setRevealed(true)}>Show answer</button>}
              </article>
              <div className="story-nav">
                <button type="button" aria-label="Previous card" disabled={card === 0} onClick={() => { setCard(card - 1); setRevealed(false) }}><ChevronLeft size={14} /> Previous</button>
                <button type="button" aria-label="Next card" disabled={card >= cards.length - 1} onClick={() => { setCard(card + 1); setRevealed(false) }}><ChevronRight size={14} /> Next</button>
              </div>
              {prompts.length > 0 && (
                <div className="viva-divider"><span>MORE REVIEW PROMPTS</span></div>
              )}
              {prompts.map((item, index) => (
                <details className="viva-item" key={`${item.question}-${index}`}>
                  <summary><span>{item.question}</span><ChevronRight size={14} /></summary>
                  <p>{item.answer_hint}</p>
                  <p className="recall-meta">{item.origin === 'extracted' ? 'Hint from extracted text. ' : ''}{[item.source_section, item.source_page ? `page ${item.source_page}` : ''].filter(Boolean).join(' · ')}</p>
                </details>
              ))}
              <button type="button" className="secondary-action export-cards" disabled={!cards.length} onClick={onExport}><Download size={14} /> Export Anki deck</button>
            </>
          )}
        </div>
      )}

      {tab === 'code' && (
        <div className="artifact-panel code-panel" role="tabpanel">
          <h2>Code lab</h2>
          {!paper ? <Empty title="No paper loaded">Runnable snippets are taken from Python blocks in the uploaded PDF.</Empty> : studyKit?.python_code ? (
            <>
              <p className="panel-description">Copied from a Python block in the extracted text. It runs in this browser tab.</p>
              <div className="code-window">
                <div className="code-top"><span>paper-snippet.py</span><button type="button" title="Copy code" onClick={onCopy}><Clipboard size={13} /></button></div>
                <pre className="code-content">{studyKit.python_code.split('\n').map((line, index) => <div className="code-line" key={index}><span className="line-no">{String(index + 1).padStart(2, '0')}</span><code>{highlightCode(line)}</code></div>)}</pre>
              </div>
              <Suspense fallback={<p className="loading-inline">Preparing sandbox…</p>}>
                <PyodideRunner initialCode={studyKit.python_code} key={studyKit.python_code} />
              </Suspense>
            </>
          ) : <Empty title="No code block in this paper">The extracted text has no fenced Python snippet. This app does not invent example code for the paper.</Empty>}
        </div>
      )}
    </aside>
  )
}
