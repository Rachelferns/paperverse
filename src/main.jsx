import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BookOpen, Check, ChevronDown, ChevronLeft, ChevronRight, FileText, Menu, PanelLeftClose, PanelRightClose, Plus, Search, Upload, X } from 'lucide-react'
import './styles.css'
import './overrides.css'
import { API_ROOT, getPaper, getRecentPaper, importArxiv, uploadPdf, watchJob } from './api'
import LearningPanel from './components/LearningPanel'
import { presentSymbol } from './viewModel'

function statusLabel(job) {
  if (!job) return ''
  if (job.status === 'queued') return 'Queued'
  if (job.status === 'processing') return 'Analyzing'
  if (job.status === 'failed') return 'Failed'
  if (job.status === 'partially_completed') return 'Partial'
  if (job.status === 'completed') return 'Ready'
  return job.status
}

function App() {
  const [activeSection, setActiveSection] = useState(0)
  const [tab, setTab] = useState('map')
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(false)
  const [outlineQuery, setOutlineQuery] = useState('')
  const [glossary, setGlossary] = useState('')
  const [selectedSymbol, setSelectedSymbol] = useState('')
  const [focusedEquation, setFocusedEquation] = useState('')
  const [toast, setToast] = useState('')
  const [activeJob, setActiveJob] = useState(null)
  const [paperId, setPaperId] = useState(null)
  const [studyKit, setStudyKit] = useState(null)
  const [paperDocument, setPaperDocument] = useState(null)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [search, setSearch] = useState('')
  const fileRef = useRef(null)

  const paperSections = paperDocument?.sections || []
  const sectionIndex = paperSections.length ? Math.min(activeSection, paperSections.length - 1) : 0
  const active = paperSections[sectionIndex]
  const symbols = studyKit?.symbols || []
  const visibleSymbols = symbols.filter(item => `${item.symbol} ${item.definition || ''} ${item.name || ''}`.toLowerCase().includes(glossary.trim().toLowerCase()))
  const outline = paperSections.map((section, index) => ({ index, name: section.title || `Section ${index + 1}`, page: section.page }))
  const visibleOutline = outline.filter(item => item.name.toLowerCase().includes(outlineQuery.trim().toLowerCase()))
  const sectionEquations = (studyKit?.equations || []).filter(equation => equation.section_name === active?.title)
  const busy = ['queued', 'processing'].includes(activeJob?.status)
  const failed = activeJob?.status === 'failed' && !paperDocument

  const notify = message => {
    setToast(message)
    window.setTimeout(() => setToast(''), 2400)
  }

  const openTools = (nextTab, equationId) => {
    setTab(nextTab)
    setRightOpen(true)
    if (equationId) setFocusedEquation(equationId)
  }

  const acceptFile = async file => {
    if (!file) return
    setUploadBusy(true)
    setUploadProgress(0)
    try {
      const result = await uploadPdf(file, setUploadProgress)
      setPaperId(result.paper_id)
      setPaperDocument(null)
      setStudyKit(null)
      setActiveSection(0)
      setFocusedEquation('')
      setActiveJob({ job_id: result.job_id, status: 'queued', progress: 0, stage: 'queued' })
      setUploadOpen(false)
      notify('Paper queued for analysis')
    } catch (error) {
      notify(error.message || 'Could not upload paper')
    } finally {
      setUploadBusy(false)
    }
  }

  const exportCards = () => {
    if (!paperId || !studyKit?.flashcards?.length) return
    window.open(`${API_ROOT}/papers/${paperId}/download-anki`, '_blank', 'noopener')
  }

  const copyCode = async () => {
    const text = studyKit?.python_code
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      notify('Code copied')
    } catch {
      notify('Could not copy code')
    }
  }

  useEffect(() => {
    const onKey = event => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setLeftOpen(true)
        window.setTimeout(() => document.getElementById('outline-filter')?.focus(), 30)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    const media = window.matchMedia('(max-width: 900px)')
    const apply = () => { if (media.matches) setLeftOpen(false) }
    apply()
    media.addEventListener?.('change', apply)
    return () => media.removeEventListener?.('change', apply)
  }, [])

  useEffect(() => {
    let cancelled = false
    getRecentPaper().then(result => {
      if (cancelled || !result.job) return
      setPaperId(result.job.paper_id)
      setActiveJob(result.job)
      if (result.paper) {
        setActiveSection(0)
        setPaperDocument(result.paper)
        setStudyKit({ ...(result.artifacts || {}), equations: result.equations || [], symbols: result.symbols || [] })
      }
    }).catch(() => {})
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!activeJob?.job_id || !busy && !['completed', 'partially_completed', 'failed'].includes(activeJob.status)) return undefined
    if (['completed', 'partially_completed', 'failed'].includes(activeJob.status) && paperDocument) return undefined
    return watchJob(activeJob.job_id, async job => {
      setActiveJob(job)
      if (job.status === 'completed' || job.status === 'partially_completed') {
        try {
          const result = await getPaper(job.paper_id)
          setActiveSection(0)
          setPaperDocument(result.paper)
          setStudyKit({ ...(result.artifacts || {}), equations: result.equations || [], symbols: result.symbols || [] })
          notify(job.status === 'partially_completed' ? 'Analysis finished with some stage errors' : 'Paper analysis complete')
        } catch (error) {
          notify(error.message)
        }
      } else if (job.status === 'failed') notify(job.error || 'Paper analysis failed')
    }, () => {})
  }, [activeJob?.job_id])

  const title = paperDocument?.title || (activeJob ? 'Uploaded paper' : 'PaperVerse')
  const meta = [statusLabel(activeJob), paperDocument?.source_filename].filter(Boolean).join(' · ')

  return (
    <main className={`app-shell ${leftOpen ? 'outline-open' : ''}`}>
      <header className="topbar">
        <a className="brand" href="#reading" aria-label="PaperVerse home"><span className="brand-mark"><BookOpen size={17} strokeWidth={1.8} /></span><span>paper<span>verse</span></span></a>
        <div className="topbar-middle header-paper">
          <strong title={title}>{title}</strong>
          <span>{meta || 'Upload a PDF to start reading'}</span>
        </div>
        <div className="topbar-actions">
          <button type="button" className="upload-button" onClick={() => setUploadOpen(true)}><Plus size={15} /> <span>New paper</span></button>
        </div>
      </header>

      <div className={`workspace ${leftOpen ? '' : 'outline-collapsed'} ${rightOpen ? '' : 'tools-collapsed'}`}>
        {leftOpen && <button type="button" className="outline-scrim" aria-label="Close outline" onClick={() => setLeftOpen(false)} />}
        {leftOpen && (
          <aside className="left-sidebar">
            <div className="sidebar-heading">
              <div className="eyebrow">DOCUMENT OUTLINE</div>
              <button type="button" className="quiet-icon" aria-label="Collapse outline" onClick={() => setLeftOpen(false)}><PanelLeftClose size={15} /></button>
            </div>
            <label className="symbol-search sidebar-search">
              <Search size={13} />
              <input id="outline-filter" value={outlineQuery} onChange={event => setOutlineQuery(event.target.value)} placeholder="Filter sections" aria-label="Filter sections" />
            </label>
            {paperDocument ? (
              <nav className="outline-nav" aria-label="Paper sections">
                {visibleOutline.length ? visibleOutline.map(section => (
                  <button type="button" key={`${section.index}-${section.name}`} className={`outline-item ${sectionIndex === section.index ? 'selected' : ''}`} aria-current={sectionIndex === section.index ? 'true' : undefined} onClick={() => setActiveSection(section.index)}>
                    <span className="section-number">{String(section.index + 1).padStart(2, '0')}</span>
                    <span className="outline-copy"><span>{section.name}</span><small>{section.page ? `Page ${section.page}` : 'Section'}</small></span>
                  </button>
                )) : <p className="sidebar-note">No section titles match that filter.</p>}
              </nav>
            ) : <p className="sidebar-note">Upload a paper to see its sections. This list is the document outline, not a model diagram.</p>}
            <p className="sidebar-note">{paperSections.length ? `${paperSections.length} sections` : 'No sections yet'}</p>
            <details className="symbol-block">
              <summary>Symbol index <span className="count-pill">{symbols.length}</span><ChevronDown size={14} /></summary>
              <p className="sidebar-note">A symbol is an occurrence in an extracted equation. It is marked defined only when the surrounding text states what it means.</p>
              <label className="symbol-search">
                <Search size={13} />
                <input value={glossary} onChange={event => setGlossary(event.target.value)} placeholder="Find a symbol" aria-label="Find a symbol" />
              </label>
              {paperDocument && symbols.length === 0 ? <p className="sidebar-note">No symbols were indexed because no equations were extracted.</p> : null}
              <div className="symbol-list">
                {visibleSymbols.map(item => {
                  const view = presentSymbol(item)
                  const open = selectedSymbol === item.symbol
                  return (
                    <div key={item.symbol}>
                      <button type="button" className={`symbol-row ${open ? 'active' : ''}`} onClick={() => setSelectedSymbol(open ? '' : item.symbol)}>
                        <span className="symbol-chip violet">{item.symbol}</span>
                        <span className="symbol-description">{view.label}</span>
                      </button>
                      {open && <div className="symbol-detail"><span className="symbol-status">{view.label}</span><p>{view.definition}</p></div>}
                    </div>
                  )
                })}
              </div>
            </details>
          </aside>
        )}

        <section className="center-column" id="reading">
          <div className="reading-toolbar">
            <div className="reading-label">
              <button type="button" className="icon-button" aria-label={leftOpen ? 'Hide outline' : 'Show outline'} onClick={() => setLeftOpen(!leftOpen)}>{leftOpen ? <PanelLeftClose size={15} /> : <Menu size={15} />}</button>
              <span>{paperSections.length ? `Section ${sectionIndex + 1} of ${paperSections.length}` : 'Reading'}</span>
            </div>
            <button type="button" className="tool-toggle" aria-pressed={rightOpen} onClick={() => setRightOpen(!rightOpen)}>
              {rightOpen ? <PanelRightClose size={14} /> : <FileText size={14} />} Tools
            </button>
          </div>

          {busy ? (
            <article className="article-content reading-room">
              <h1>{activeJob.status === 'queued' ? 'Your paper is queued.' : 'Reading the PDF.'}</h1>
              <p className="article-lead">Text, sections, and equations are extracted on this machine. Study tools appear when that finishes.</p>
              <div className="pipeline-card">
                <div className="pipeline-card-top"><span>{activeJob.stage || 'queued'}</span><strong>{activeJob.progress || 0}%</strong></div>
                <div className="pipeline-track"><span style={{ width: `${activeJob.progress || 0}%` }} /></div>
              </div>
            </article>
          ) : failed ? (
            <article className="article-content reading-room">
              <h1>This PDF could not be read.</h1>
              <p className="article-lead">{activeJob.error || 'The parser found no selectable text. OCR is not enabled.'}</p>
              <button type="button" className="secondary-action inline-action" onClick={() => setUploadOpen(true)}><Plus size={14} /> Try another paper</button>
            </article>
          ) : !paperDocument ? (
            <article className="article-content reading-room empty-read">
              <h1>Read a paper here.</h1>
              <p>Upload a PDF to extract its sections. Architecture, equations, and study cards are built from that file. Nothing is shown from a sample paper.</p>
              <button type="button" className="upload-button" onClick={() => setUploadOpen(true)}><Upload size={15} /> Upload PDF</button>
            </article>
          ) : (
            <article className="article-content reading-room">
              {activeJob?.status === 'partially_completed' && <p className="partial-note">Partial result. {activeJob.error || 'Some study tools failed. Extracted text was kept.'}</p>}
              <div className="section-kicker"><span className="kicker-rule" /> {active?.page ? `Page ${active.page}` : 'Extracted text'}</div>
              <h1>{active?.title || paperDocument.title}</h1>
              <p className="field-label">Extracted text</p>
              <div className="section-read">{active?.content?.trim() || active?.explanation || paperDocument.markdown_content || 'This section heading was found, but no body text was extracted.'}</div>
              {sectionEquations.length > 0 && (
                <div className="section-links">
                  <span>Equations in this section</span>
                  {sectionEquations.map((equation, index) => (
                    <button type="button" key={equation.equation_id || index} onClick={() => openTools('equations', equation.equation_id)}>
                      {equation.equation_number ? `Equation ${equation.equation_number}` : `Equation ${index + 1}`}
                    </button>
                  ))}
                </div>
              )}
              <div className="section-step-nav">
                <button type="button" disabled={sectionIndex === 0} onClick={() => setActiveSection(sectionIndex - 1)}><ChevronLeft size={14} /> {outline[sectionIndex - 1]?.name || 'Previous'}</button>
                <span>{sectionIndex + 1} / {paperSections.length}</span>
                <button type="button" disabled={sectionIndex >= paperSections.length - 1} onClick={() => setActiveSection(sectionIndex + 1)}>{outline[sectionIndex + 1]?.name || 'Next'} <ChevronRight size={14} /></button>
              </div>
            </article>
          )}
        </section>

        {rightOpen && (
          <LearningPanel
            tab={tab}
            setTab={setTab}
            paper={paperDocument}
            studyKit={studyKit}
            focusedEquation={focusedEquation}
            onExport={exportCards}
            onCopy={copyCode}
          />
        )}
      </div>

      {uploadOpen && (
        <div className="modal-scrim" onClick={() => setUploadOpen(false)}>
          <div className="upload-modal" onClick={event => event.stopPropagation()} role="dialog" aria-labelledby="upload-title">
            <div className="modal-heading">
              <span className="modal-mark"><BookOpen size={17} /></span>
              <div><h2 id="upload-title">Add a paper</h2><p>Upload a PDF or import one from arXiv. Processing stays on this machine.</p></div>
              <button type="button" className="quiet-icon" aria-label="Close" onClick={() => setUploadOpen(false)}><X size={17} /></button>
            </div>
            <div className={`dropzone ${dragging ? 'is-dragging' : ''} ${uploadBusy ? 'uploading' : ''}`} onDragEnter={event => { event.preventDefault(); setDragging(true) }} onDragOver={event => event.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files?.[0]) }} onClick={() => !uploadBusy && fileRef.current?.click()}>
              <input ref={fileRef} type="file" accept=".pdf,application/pdf" hidden onChange={event => acceptFile(event.target.files?.[0])} />
              <span className="upload-icon"><Upload size={19} /></span>
              <strong>{uploadBusy ? 'Uploading your PDF…' : <>Drop a PDF here, or <i>browse files</i></>}</strong>
              <span>{uploadBusy ? `Sending PDF · ${uploadProgress}%` : 'PDF up to 50 MB'}</span>
              {uploadBusy && <div className="upload-track"><span style={{ width: `${uploadProgress}%` }} /></div>}
            </div>
            <div className="or-divider"><span>OR IMPORT FROM ARXIV</span></div>
            <div className="arxiv-field">
              <span className="arxiv-icon">arχiv</span>
              <input id="paper-search" value={search} onChange={event => setSearch(event.target.value)} placeholder="arXiv URL or paper ID" aria-label="arXiv URL or paper ID" />
              <button type="button" aria-label="Import arXiv paper" disabled={!search.trim() || uploadBusy} onClick={async () => {
                setUploadBusy(true)
                try {
                  const result = await importArxiv(search)
                  setPaperId(result.paper_id)
                  setPaperDocument(null)
                  setStudyKit(null)
                  setActiveSection(0)
                  setFocusedEquation('')
                  setActiveJob({ job_id: result.job_id, status: 'queued', progress: 0, stage: 'queued' })
                  setSearch('')
                  setUploadOpen(false)
                  notify('arXiv paper queued for analysis')
                } catch (error) {
                  notify(error.message || 'Could not import arXiv paper')
                } finally {
                  setUploadBusy(false)
                }
              }}><ChevronRight size={15} /></button>
            </div>
          </div>
        </div>
      )}
      {toast && <div className="toast" role="status"><Check size={15} />{toast}</div>}
    </main>
  )
}

createRoot(document.getElementById('root')).render(<App />)
