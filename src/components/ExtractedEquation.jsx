import React from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { equationStatus } from '../viewModel'

function renderLatex(latex) {
  const source = String(latex || '').trim()
  if (!source) return ''
  try {
    return katex.renderToString(source, { throwOnError: false, displayMode: true })
  } catch {
    return ''
  }
}

const STATUS_COPY = {
  extracted: 'Extracted from paper · not verified',
  partial: 'Extracted from paper · partial check only',
  verified: 'Symbolically verified',
}

export default function ExtractedEquation({ equation, index, current }) {
  const latex = equation?.official_latex || ''
  const html = renderLatex(latex)
  const page = equation?.page
  const section = equation?.section_name
  const number = equation?.equation_number || String(index + 1).padStart(2, '0')
  const status = equationStatus(equation)
  const symbols = equation?.explained_symbols || []
  const derived = (equation?.steps || []).filter(step => step.is_intermediate_derived)
  const location = [section, page ? `page ${page}` : ''].filter(Boolean).join(' · ')
  return (
    <article className={`extracted-equation ${current ? 'is-current' : ''}`} id={equation?.equation_id || undefined}>
      <div className="extracted-equation-meta">
        <span className="extracted-index">Equation {number}</span>
        {location ? <span className="extracted-location">{location}</span> : null}
      </div>
      <p className="field-label">Extracted from paper</p>
      {html ? <div className="extracted-math" dangerouslySetInnerHTML={{ __html: html }} /> : <code>{latex}</code>}
      <p className="field-label">Explanation</p>
      <p>{equation?.plain_explanation || 'Source equation extracted. A plain-English reading is not available for this expression.'}</p>
      <p className="field-label">Symbols</p>
      {symbols.length ? (
        <ul className="equation-symbols">
          {symbols.map(item => (
            <li key={item.symbol}>
              <code>{item.symbol}</code>
              <span>{item.status === 'defined' ? 'Defined in source' : 'Occurrence'}</span>
              <p>{item.definition}</p>
            </li>
          ))}
        </ul>
      ) : <p>No symbols were identified in this expression.</p>}
      {equation?.intuition ? (
        <>
          <p className="field-label">Intuition</p>
          <p>{equation.intuition}</p>
        </>
      ) : null}
      <p className="field-label">Derivation steps</p>
      {derived.length ? derived.map(step => (
        <div className="derivation-block" key={step.step_number}>
          <span>{step.sympy_verified ? 'SymPy checked this step' : 'Not verified'}</span>
          {renderLatex(step.latex) ? <div className="extracted-math" dangerouslySetInnerHTML={{ __html: renderLatex(step.latex) }} /> : <code>{step.latex}</code>}
          <p>{step.explanation}</p>
        </div>
      )) : <p>Source equation extracted; derivation not available.</p>}
      <p className="field-label">Verification status</p>
      <p className={`verify-line verify-${status}`}>{STATUS_COPY[status]}</p>
      {equation?.verification_note ? <p className="verify-note">{equation.verification_note}</p> : null}
    </article>
  )
}
