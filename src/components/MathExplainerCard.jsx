import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, CheckCircle2, ChevronDown, Clipboard, Code2, Sparkles, Terminal, AlertCircle, ArrowRight } from 'lucide-react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

function safeKatex(tex, displayMode = true) {
  if (!tex) return ''
  try {
    return katex.renderToString(String(tex).trim(), { displayMode, throwOnError: false })
  } catch {
    return tex
  }
}

export default function MathExplainerCard({ equation, index, isFirst = false, notify = () => {} }) {
  const [derivationOpen, setDerivationOpen] = useState(isFirst)
  const [sympyOpen, setSympyOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const steps = equation.step_by_step_derivation || equation.steps || []
  const symbols = equation.symbol_glossary || []
  const dependencies = equation.dependencies || []
  const sympyScript = equation.sympy_verification_script || ''
  const isVerified = equation.sympy_verified || (equation.verification_note && equation.verification_note.toLowerCase().includes('verified'))

  const copySympy = async () => {
    if (!sympyScript) return
    try {
      await navigator.clipboard.writeText(sympyScript)
      setCopied(true)
      notify('SymPy verification script copied!')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      notify('Could not copy to clipboard')
    }
  }

  const mainMathHtml = safeKatex(equation.official_latex || equation.original_latex || '', true)

  return (
    <div className="math-explainer-card">
      <div className="math-card-header">
        <div className="math-header-left">
          <span className="math-badge">
            <span>ƒ</span> {equation.paper_section || `EQUATION ${String(index + 1).padStart(2, '0')}`}
          </span>
          <span className="equation-id-label">{equation.equation_id || `Eq_${index + 1}`}</span>
        </div>
        {isVerified ? (
          <span className="sympy-verified-badge" title="Symbolic steps verified with SymPy">
            <CheckCircle2 size={13} />
            SYMPY VERIFIED
          </span>
        ) : (
          <span className="math-engine-badge">
            <Sparkles size={12} />
            MATH EXPLAINER
          </span>
        )}
      </div>

      {mainMathHtml ? (
        <div className="math-display-stage" dangerouslySetInnerHTML={{ __html: mainMathHtml }} />
      ) : (
        <code className="math-display-code">{equation.official_latex || equation.original_latex}</code>
      )}

      {equation.conceptual_summary && (
        <div className="math-conceptual-summary">
          <strong>Conceptual Intuition:</strong>
          <p>{equation.conceptual_summary}</p>
        </div>
      )}

      {dependencies.length > 0 && (
        <div className="math-dependencies">
          <span className="dep-title">DEPENDENCY MAPPING</span>
          <div className="dep-chips">
            {dependencies.map((dep, i) => (
              <span key={i} className="dep-chip">
                <ArrowRight size={11} /> {dep}
              </span>
            ))}
          </div>
        </div>
      )}

      {symbols.length > 0 && (
        <div className="math-glossary-section">
          <span className="glossary-header">SYMBOL GLOSSARY & DIMENSIONALITIES</span>
          <div className="glossary-grid">
            {symbols.map((item, i) => (
              <div key={i} className="glossary-card">
                <div className="glossary-card-top">
                  <span
                    className="glossary-symbol"
                    dangerouslySetInnerHTML={{ __html: safeKatex(item.symbol, false) }}
                  />
                  <span className="glossary-dim">{item.dimension || item.dimensions || 'Scalar'}</span>
                </div>
                <div className="glossary-name">{item.name}</div>
                <div className="glossary-def">{item.definition}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {steps.length > 0 && (
        <div className="math-derivation-section">
          <button
            type="button"
            className={`derivation-accordion-toggle ${derivationOpen ? 'open' : ''}`}
            onClick={() => setDerivationOpen(!derivationOpen)}
          >
            <span className="toggle-spark">
              <Sparkles size={13} />
            </span>
            <span>
              {derivationOpen ? 'Hide' : 'Resolve'} Step-by-Step Derivation ({steps.length} micro-steps)
            </span>
            <ChevronDown size={14} className="accordion-chevron" />
          </button>

          <AnimatePresence>
            {derivationOpen && (
              <motion.div
                className="derivation-steps-container"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.22 }}
              >
                {steps.map((step, sIdx) => {
                  const stepLatex = step.latex_expression || step.latex || ''
                  const stepHtml = safeKatex(stepLatex, true)
                  return (
                    <div className="derivation-step-card" key={sIdx}>
                      <div className="step-header">
                        <span className="step-badge">Step {step.step_number || sIdx + 1}</span>
                        {step.axiom_or_rule_applied && (
                          <span className="axiom-badge" title="Rule or axiom applied">
                            {step.axiom_or_rule_applied}
                          </span>
                        )}
                      </div>

                      {stepHtml ? (
                        <div className="step-math" dangerouslySetInnerHTML={{ __html: stepHtml }} />
                      ) : (
                        stepLatex && <code className="step-code">{stepLatex}</code>
                      )}

                      {step.explanation && <p className="step-explanation">{step.explanation}</p>}
                    </div>
                  )
                })}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {sympyScript && (
        <div className="sympy-verification-section">
          <div className="sympy-header">
            <button
              type="button"
              className="sympy-toggle-btn"
              onClick={() => setSympyOpen(!sympyOpen)}
            >
              <Terminal size={13} />
              <span>SymPy Symbolic Verification Script</span>
              <ChevronDown size={13} className={sympyOpen ? 'rotate-180' : ''} />
            </button>
            <button
              type="button"
              className="copy-script-btn"
              onClick={copySympy}
              title="Copy Python SymPy verification script"
            >
              {copied ? <Check size={12} /> : <Clipboard size={12} />}
              <span>{copied ? 'Copied' : 'Copy script'}</span>
            </button>
          </div>

          <AnimatePresence>
            {sympyOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="sympy-code-wrap"
              >
                <pre>
                  <code>{sympyScript}</code>
                </pre>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {equation.notational_notes_or_typos && (
        <div className="notational-notes-box">
          <AlertCircle size={14} />
          <div>
            <strong>Notational Notes & Assumptions:</strong>
            <p>{equation.notational_notes_or_typos}</p>
          </div>
        </div>
      )}
    </div>
  )
}
