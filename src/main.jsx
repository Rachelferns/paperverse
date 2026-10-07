import React, { Suspense, lazy, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AnimatePresence, motion } from 'framer-motion'
import { BookOpen, BrainCircuit, Check, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight, ChevronsUpDown, CircleHelp, Clipboard, Code2, Download, ExternalLink, FileText, GitBranch, Layers3, Lightbulb, Menu, MoreHorizontal, PanelLeftClose, PanelRightClose, Play, Plus, Search, Settings2, Sparkles, Upload, X, Zap } from 'lucide-react'
import './styles.css'
import './overrides.css'
import { getPaper, getRecentPaper, importArxiv, uploadPdf, watchJob } from './api'
const MathMotionPlayer = lazy(() => import('./components/MathMotionPlayer'))
const MermaidPreview = lazy(() => import('./components/MermaidPreview'))
const PyodideRunner = lazy(() => import('./components/PyodideRunner'))

const sections = [
  { number: '00', name: 'Abstract', sub: 'The gist in 30 seconds' },
  { number: '01', name: 'Introduction', sub: 'Why attention matters' },
  { number: '02', name: 'Background', sub: 'The sequence problem' },
  { number: '03', name: 'Model Architecture', sub: 'The Transformer' },
  { number: '04', name: 'Attention', sub: 'Mapping relationships' },
  { number: '05', name: 'Training', sub: 'Optimization details' },
  { number: '06', name: 'Experiments', sub: 'Results & ablations' },
]
const symbols = [
  { symbol: 'Q, K, V', label: 'Queries, keys & values', kind: 'Matrices', color: 'violet' },
  { symbol: 'dₖ', label: 'Key vector dimension', kind: 'Scalar', color: 'amber' },
  { symbol: 'h', label: 'Number of attention heads', kind: 'Integer', color: 'blue' },
  { symbol: 'Wₒ', label: 'Output projection matrix', kind: 'Weights', color: 'green' },
]
const artifactTabs = [
  { id: 'map', label: 'Architecture', icon: GitBranch },
  { id: 'code', label: 'Code lab', icon: Code2 },
  { id: 'motion', label: 'Motion', icon: Play },
  { id: 'learn', label: 'Study cards', icon: BrainCircuit },
]
const code = `import torch\nimport torch.nn.functional as F\n\ndef scaled_dot_product(q, k, v):\n    d_k = q.size(-1)\n    scores = q @ k.transpose(-2, -1)\n    weights = F.softmax(scores / d_k**0.5, dim=-1)\n    return weights @ v`
const cards = [
  { q: 'What problem does self-attention solve?', a: 'It lets each position in a sequence weigh the relevance of every other position, capturing long-range relationships directly.' },
  { q: 'Why scale by √dₖ?', a: 'As vector dimensions grow, dot products grow in variance. Scaling keeps softmax from saturating, preserving useful gradients.' },
  { q: 'What makes attention “multi-head”?', a: 'The model runs several attention operations in parallel, each learning to focus on different types of relationships.' },
]

function conciseAnswer(value, limit = 150) {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (text.length <= limit) return text
  const firstSentence = text.split(/(?<=[.!?])\s+(?=[A-Z0-9])/)[0] || text
  if (firstSentence.length <= limit) return firstSentence
  return `${firstSentence.slice(0, limit - 1).replace(/\s+\S*$/, '').replace(/[ ,;:]$/, '')}…`
}

function App() {
  const [activeSection, setActiveSection] = useState(4)
  const [tab, setTab] = useState('map')
  const [mode, setMode] = useState('explainer')
  const [sectionFocus, setSectionFocus] = useState(false)
  const [derivation, setDerivation] = useState(false)
  const [gradient, setGradient] = useState(false)
  const [glossary, setGlossary] = useState('')
  const [search, setSearch] = useState('')
  const [flipped, setFlipped] = useState(false)
  const [card, setCard] = useState(0)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [leftOpen, setLeftOpen] = useState(true)
  const [rightOpen, setRightOpen] = useState(true)
  const [toast, setToast] = useState('')
  const [activeJob, setActiveJob] = useState(null)
  const [paperId, setPaperId] = useState(null)
  const [studyKit, setStudyKit] = useState(null)
  const [paperDocument, setPaperDocument] = useState(null)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileRef = useRef(null)
  const activeCards = studyKit?.flashcards?.length ? studyKit.flashcards.map(item => ({ q: item.question, a: conciseAnswer(item.answer) })) : cards.map(item => ({ ...item, a: conciseAnswer(item.a) }))
  const displaySymbols = studyKit ? studyKit.symbols : symbols
  const paperSections = paperDocument?.sections?.length ? paperDocument.sections : []
  const outlineSections = paperSections.length
    ? paperSections.map((section, index) => ({ number: String(index).padStart(2, '0'), name: section.title, sub: `Page ${section.page || 1}` }))
    : sections
  const activePaperSection = paperSections[activeSection]
  const paperPageCount = (paperDocument?.markdown_content?.match(/<!-- page:/g) || []).length
  const demoSectionCopy = [
    'The paper introduces a sequence transduction model based entirely on attention, replacing recurrent and convolutional sequence modeling with direct relationships between positions.',
    'Recurrent models process tokens sequentially, limiting parallelization and making long-range dependencies harder to learn. Attention offers a shorter path between positions.',
    'An attention function maps a query and key–value pairs to an output. Dot-product attention is efficient and can be implemented with highly optimized matrix multiplication.',
    'The Transformer stacks self-attention and position-wise feed-forward layers with residual connections and normalization in both encoder and decoder.',
    'Scaled dot-product attention divides query–key scores by the square root of the key dimension before applying softmax, then uses the weights to combine values.',
    'Multiple attention heads project queries, keys, and values into separate learned subspaces, allowing the model to attend to different relationships in parallel.',
    'The experiments compare translation and parsing quality, training cost, and ablations of attention heads, dimensions, and positional encodings.'
  ]

  const notify = (message) => { setToast(message); window.setTimeout(() => setToast(''), 2400) }
  const acceptFile = async (file) => {
    if (!file) return
    setUploadBusy(true)
    setUploadProgress(0)
    try {
      const result = await uploadPdf(file, setUploadProgress)
      setPaperId(result.paper_id)
      setPaperDocument(null)
      setStudyKit(null)
      setActiveSection(0)
      setSectionFocus(false)
      setActiveJob({ job_id: result.job_id, status: 'queued', progress: 0, stage: 'queued' })
      setUploadOpen(false)
      notify('Paper queued for analysis')
    } catch (error) { notify(error.message || 'Could not upload paper') }
    finally { setUploadBusy(false) }
  }
  const copyCode = async () => { await navigator.clipboard?.writeText(studyKit?.python_code || code); notify('Code copied to clipboard') }
  const exportCards = () => { if (!paperId) return notify('Upload a paper to export its Anki deck'); window.open(`http://localhost:8001/api/v1/papers/${paperId}/download-anki`, '_blank', 'noopener') }

  useEffect(() => {
    let cancelled = false
    getRecentPaper().then(result => {
      if (cancelled || !result.job) return
      setPaperId(result.job.paper_id)
      setActiveJob(result.job)
      if (result.paper) {
        setActiveSection(0)
        setSectionFocus(false)
        setPaperDocument(result.paper)
        setStudyKit({ ...(result.artifacts || {}), equations: result.equations || [], symbols: result.symbols || [] })
      }
    }).catch(() => {})
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!activeJob?.job_id) return
    return watchJob(activeJob.job_id, async job => {
      setActiveJob(job)
      if (job.status === 'completed') {
        try {
          const result = await getPaper(job.paper_id)
          setActiveSection(0)
          setSectionFocus(false)
          setPaperDocument(result.paper)
          setStudyKit({ ...(result.artifacts || {}), equations: result.equations || [], symbols: result.symbols || [] })
          notify('Paper analysis complete')
        } catch (error) { notify(error.message) }
      } else if (job.status === 'failed') notify(job.error || 'Paper analysis failed')
    }, () => {})
  }, [activeJob?.job_id])

  useEffect(() => {
    if (uploadOpen) window.setTimeout(() => document.getElementById('paper-search')?.focus(), 30)
  }, [uploadOpen])

  return <main className="app-shell" onDragOver={e => e.preventDefault()}>
    <header className="topbar">
      <a className="brand" href="#" aria-label="PaperVerse home"><span className="brand-mark"><BookOpen size={17} strokeWidth={1.8} /></span><span>paper<span>verse</span></span><span className="brand-beta">BETA</span></a>
      <div className="topbar-middle">
        <div className="breadcrumb"><span>My library</span><ChevronRight size={13} /><span className="crumb-current">{paperDocument?.title || (activeJob ? 'New paper' : 'Attention Is All You Need')}</span><ChevronDown size={13} /></div>
      </div>
      <div className="topbar-actions">
        <button className="search-trigger" onClick={() => setUploadOpen(true)}><Search size={15} /><span>Search papers...</span><kbd>⌘ K</kbd></button>
        <button className="upload-button" onClick={() => setUploadOpen(true)}><Plus size={15} /> <span>New paper</span></button>
        <div className="top-divider" />
        <button className="workspace-switcher"><span className="avatar">S</span><span>Studio</span><ChevronsUpDown size={13} /></button>
      </div>
    </header>

    <div className="paper-strip">
        <div className="paper-identity"><span className="pdf-icon"><FileText size={16} /></span><div><div className="paper-title">{paperDocument?.title || (activeJob ? activeJob.status === 'completed' ? 'Paper analysis ready' : 'Your uploaded paper' : 'Attention Is All You Need')} <span className="paper-year">{activeJob ? activeJob.status.toUpperCase() : '2017'}</span></div><div className="paper-authors">{paperDocument ? paperDocument.source_filename : activeJob ? `${activeJob.stage || 'queued'} · ${activeJob.progress || 0}% processed` : 'Vaswani et al. · NeurIPS · 15 min read'}</div></div></div>
        <div className="strip-center"><span className="read-progress"><span /></span><span>Section {String(activeSection + 1).padStart(2, '0')} <i>of</i> {outlineSections.length}</span><span className="strip-dot">·</span><span>{paperDocument ? `${paperPageCount} pages indexed` : '68% understood'}</span></div>
      <div className="paper-actions"><button className="icon-button" title="Paper settings"><Settings2 size={16} /></button><button className="icon-button" title="More options"><MoreHorizontal size={18} /></button><button className="share-button" onClick={() => notify('Study link copied')}><ExternalLink size={14} /> Share</button></div>
    </div>

    <div className="workspace">
      {leftOpen && <aside className="left-sidebar">
        <div className="sidebar-heading"><div className="eyebrow">YOUR STUDY SPACE</div><button className="quiet-icon" aria-label="Collapse outline" onClick={() => setLeftOpen(false)}><PanelLeftClose size={15} /></button></div>
        <div className="outline-label"><span>DOCUMENT OUTLINE</span><button className="quiet-icon"><MoreHorizontal size={15} /></button></div>
        <nav className="outline-nav" aria-label="Paper sections">{outlineSections.map((section, i) => <button key={`${section.number}-${section.name}`} onClick={() => { setActiveSection(i); setFlipped(false); if (paperSections.length) { setSectionFocus(true); setMode('explainer') } else { setMode('original') } }} className={`outline-item ${activeSection === i ? 'selected' : ''}`}><span className="section-number">{section.number}</span><span className="outline-copy"><span>{section.name}</span><small>{section.sub}</small></span>{activeSection === i && <span className="selected-dot" />}</button>)}</nav>
        <div className="outline-foot"><span className="tiny-check"><Check size={10} /></span><span>{paperSections.length ? `${outlineSections.length} sections · full text indexed` : '3 of 7 sections reviewed'}</span><div className="foot-progress"><span /></div></div>
        <div className="sidebar-divider" />
        <div className="symbol-heading"><div><div className="outline-label compact"><span>SYMBOL INDEX</span><span className="count-pill">{displaySymbols.length}</span></div><p>Variables used across this paper</p></div><button className="quiet-icon"><MoreHorizontal size={15} /></button></div>
        <div className="symbol-search"><Search size={13} /><input value={glossary} onChange={e => setGlossary(e.target.value)} placeholder="Find a symbol..." /></div>
        <div className="symbol-list">{displaySymbols.filter(s => `${s.symbol} ${s.label || s.definition || ""}`.toLowerCase().includes(glossary.toLowerCase())).map(s => <button className="symbol-row" key={s.symbol} onClick={() => notify(`${s.symbol}: ${s.label || s.definition}`)}><span className={`symbol-chip ${s.color}`}>{s.symbol}</span><span className="symbol-description">{s.label || s.definition}</span><span className="symbol-type">{s.kind || s.dimensions || ""}</span></button>)}</div>
        <button className="all-symbols" onClick={() => notify(`Showing ${displaySymbols.length} extracted symbols`)}><Plus size={13} /> Explore symbols</button>
        <div className="sidebar-bottom"><button className="bottom-link"><CircleHelp size={15} /> How PaperVerse works</button><div className="user-row"><span className="avatar large">S</span><div><span className="user-name">Sam Rivera</span><small>Personal workspace</small></div><MoreHorizontal size={17} /></div></div>
      </aside>}

      <section className="center-column">
        <div className="reading-toolbar"><div className="reading-label"><span className="live-indicator" /> READING ROOM <span className="toolbar-slash">/</span> SECTION {String(activeSection + 1).padStart(2, '0')}</div><div className="toolbar-actions"><button className="icon-button mobile-outline-toggle" title={leftOpen ? 'Hide outline' : 'Show outline'} onClick={() => setLeftOpen(!leftOpen)}><Menu size={15} /></button><div className="mode-toggle"><button onClick={() => setMode('original')} className={mode === 'original' ? 'mode-active' : ''}>Original</button><button onClick={() => setMode('explainer')} className={mode === 'explainer' ? 'mode-active' : ''}><Sparkles size={12} /> Explainer</button></div>{!rightOpen && <button className="icon-button" title="Show artifacts" onClick={() => setRightOpen(true)}><PanelRightClose size={15} /></button>}<button className="icon-button"><MoreHorizontal size={17} /></button></div></div>

        {activeJob && ['queued', 'processing'].includes(activeJob.status) ? <motion.article className="article-content upload-progress-view" key="upload-progress" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }}><div className="section-kicker"><span className="kicker-rule" /> PAPER PIPELINE <span className="kicker-separator">·</span> {activeJob.status === 'queued' ? 'QUEUED' : 'ANALYZING'}</div><h1>{activeJob.status === 'queued' ? 'Your paper is in the queue.' : 'Building your study kit.'}</h1><p className="article-lead">We extract selectable PDF text, identify sections and equations, then assemble the learning artifacts.</p><div className="pipeline-card"><div className="pipeline-card-top"><span>{activeJob.stage || 'queued'}</span><strong>{activeJob.progress || 0}%</strong></div><div className="pipeline-track"><span style={{ width: `${activeJob.progress || 0}%` }} /></div><p>{activeJob.status === 'queued' ? 'Analysis starts as soon as the upload is accepted.' : 'This runs locally. Larger PDFs may take a little longer to parse.'}</p></div></motion.article> : activeJob?.status === 'failed' ? <motion.article className="article-content upload-progress-view" key="upload-failed"><div className="section-kicker"><span className="kicker-rule" /> PAPER PIPELINE <span className="kicker-separator">·</span> FAILED</div><h1>We couldn’t analyze this PDF.</h1><p className="article-lead">{activeJob.error || 'The local parser could not read this document. Try a text-based PDF.'}</p><button className="secondary-action" onClick={() => setUploadOpen(true)}><Plus size={14} /> Try another paper</button></motion.article> : sectionFocus && paperDocument && activePaperSection ? <motion.article className="article-content section-explanation" key={`section-explanation-${activeSection}`} initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }}><div className="section-kicker"><span className="kicker-rule" /> SECTION EXPLANATION <span className="kicker-separator">·</span> PAGE {activePaperSection.page || 1}</div><h1>{activePaperSection.title}</h1><p className="article-lead">A concise explanation grounded in this section’s extracted text.</p><div className="section-brief"><span className="insight-icon"><Lightbulb size={15} /></span><div><span className="eyebrow">WHAT THIS SECTION SAYS</span><p>{activePaperSection.explanation || activePaperSection.content?.replace(activePaperSection.title, '').trim() || 'The parser found the section heading but could not extract readable body text.'}</p></div></div><details className="section-source"><summary><FileText size={13} /> Read the full extracted section <ChevronDown size={14} /></summary><pre>{activePaperSection.content}</pre></details><div className="section-step-nav"><button disabled={activeSection === 0} onClick={() => setActiveSection(Math.max(0, activeSection - 1))}><ChevronLeft size={14} /> Previous section</button><span>{activeSection + 1} / {paperSections.length}</span><button disabled={activeSection >= paperSections.length - 1} onClick={() => setActiveSection(Math.min(paperSections.length - 1, activeSection + 1))}>Next section <ChevronRight size={14} /></button></div><button className="return-explainer" onClick={() => { setSectionFocus(false); setMode('explainer') }}><BookOpen size={14} /> Back to paper overview</button></motion.article> : mode === 'explainer' ? <motion.article className="article-content" key="explainer" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .24 }}>
          <div className="section-kicker"><span className="kicker-rule" /> {paperDocument ? 'LOCAL EXTRACTION' : 'SECTION 3.2'} <span className="kicker-separator">·</span> {paperDocument ? 'PAPER OVERVIEW' : 'THE TRANSFORMER'}</div>
          <h1>{paperDocument ? paperDocument.title : <>Attention is all<br className="title-break" /> you need.</>}</h1>
          <p className="article-lead">{paperDocument ? paperDocument.summary || 'The PDF was processed, but the local parser could not identify an abstract. Review the original text for the paper’s claims.' : <>The core idea is beautifully simple: let every token <em>look at</em> every other token, and learn which relationships matter.</>}</p>
          <div className="insight-callout"><span className="insight-icon"><Lightbulb size={15} /></span><p><strong>{paperDocument ? 'Local analysis is ready.' : 'Think of it like a room full of conversations.'}</strong> {paperDocument ? 'This study kit uses selectable PDF text and extracted section headings.' : <>Each word asks “who should I listen to?” <span>Attention computes the answer.</span></>}</p><span className="callout-label">{paperDocument ? 'SOURCE' : 'INTUITION'}</span></div>
          <div className="explainer-copy"><p>{paperDocument ? `${studyKit?.equations?.length || 0} display equations detected · ${studyKit?.symbols?.length || 0} symbols indexed. The local parser does not infer missing derivations.` : 'Scaled dot-product attention is the mechanism that makes this possible. For a given query, we calculate how compatible it is with each key, then use those scores to blend the values.'}</p></div>
          {!paperDocument ? <div className="equation-card">
            <div className="equation-card-head"><div><span className="math-badge"><span>ƒ</span> MATH, UNPACKED</span><span className="equation-name">Scaled dot-product attention</span></div><span className="verified" title="The local SymPy check covers the scalar scaling identity, not the full tensor equation."><CheckCircle2 size={13} /> SCALAR CHECK VERIFIED</span></div>
            <div className="equation"><span className="eq-attention">Attention</span><span className="eq-paren">(</span><span className="tip-token" title="Query matrix: what each token is looking for">Q</span><span className="eq-comma">,</span> <span className="tip-token" title="Key matrix: what each token offers">K</span><span className="eq-comma">,</span> <span className="tip-token" title="Value matrix: the information carried by each token">V</span><span className="eq-paren">)</span><span className="eq-equals">=</span><span className="eq-softmax">softmax</span><span className="eq-paren">(</span><span className="fraction"><span><span className="tip-token" title="Query–key similarity scores">QK</span><sup>T</sup></span><i><span className="eq-root">√</span><span className="tip-token" title="Dimension of the key vectors">d<sub>k</sub></span></i></span><span className="eq-paren">)</span><span className="tip-token value-v">V</span></div>
            <div className="equation-legend"><span><i className="legend-dot violet-dot" /> Similarity scores</span><span><i className="legend-dot amber-dot" /> Stabilizing scale</span><span><i className="legend-dot green-dot" /> Weighted values</span></div>
            <button className={`derivation-toggle ${derivation ? 'expanded' : ''}`} onClick={() => setDerivation(!derivation)}><span className="toggle-spark"><Sparkles size={13} /></span><span>{derivation ? 'Hide' : 'Show'} the intuition behind <span className="math-inline">√d<sub>k</sub></span></span><ChevronDown size={15} className="derivation-chevron" /></button>
            <AnimatePresence>{derivation && <motion.div className="derivation-content" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}><div className="derivation-step"><span className="step-count">01</span><div><strong>Dot products grow with dimension</strong><p>If query and key components have unit variance, their dot product has variance <span className="math-inline">d<sub>k</sub></span>.</p><code>Var(Q · K) = d<sub>k</sub></code></div></div><div className="derivation-step"><span className="step-count">02</span><div><strong>Large scores saturate softmax</strong><p>Extreme logits push softmax toward 0 or 1, where its gradient nearly disappears.</p><code>σ′(x) = σ(x)(1 − σ(x)) → 0</code></div></div><div className="derivation-step"><span className="step-count">03</span><div><strong>Scaling brings variance back to one</strong><p>Dividing by <span className="math-inline">√d<sub>k</sub></span> rescales variance by <span className="math-inline">d<sub>k</sub></span> — keeping gradients in a learnable range.</p><code>Var((Q · K) / √d<sub>k</sub>) ≈ 1</code></div></div></motion.div>}</AnimatePresence>
          </div> : <div className="equation-card extracted-equations"><div className="equation-card-head"><div><span className="math-badge"><span>ƒ</span> SOURCE MATH</span><span className="equation-name">Equations extracted from this PDF</span></div><span className="verified"><FileText size={12}/>{studyKit?.equations?.length || 0} FOUND</span></div>{studyKit?.equations?.length ? studyKit.equations.map((equation, index) => <div className="extracted-equation" key={equation.equation_id}><span className="extracted-index">EQ {String(index + 1).padStart(2, '0')}</span><code>{equation.official_latex}</code><small>{equation.verification_note}</small></div>) : <p className="no-equations">No display equations were detected in selectable PDF text. Scanned-page OCR and equation vision are not enabled.</p>}</div>}
          {!paperDocument && <div className="gradient-card"><span className="gradient-icon"><Zap size={15} /></span><div className="gradient-body"><strong>Why the square root?</strong><span>A small scaling choice that keeps learning alive.</span></div><button className="text-action" onClick={() => setGradient(!gradient)}>{gradient ? 'Close' : 'Go deeper'} <ChevronRight size={13} /></button>{gradient && <div className="gradient-detail">Without scaling, the softmax distribution gets extremely peaked as <span className="math-inline">d<sub>k</sub></span> grows. The resulting near-zero gradients make it hard for the model to learn. The square root exactly counteracts the growth in standard deviation.</div>}</div>}
          <div className="article-nav"><button onClick={() => setActiveSection(Math.max(activeSection - 1, 0))}><ChevronLeft size={14} /><span><small>PREVIOUS</small>Encoder & Decoder Stacks</span></button><span className="nav-progress"><i className="current" /><i /><i /><i /><i /><i /><i /></span><button className="next-nav" onClick={() => setActiveSection(Math.min(activeSection + 1, 6))}><span><small>NEXT UP</small>Multi-Head Attention</span><ChevronRight size={14} /></button></div>
        </motion.article> : <motion.article className="article-content original-view" key={`original-${activeSection}`} initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }}><div className="section-kicker"><span className="kicker-rule" /> {paperDocument ? 'EXTRACTED TEXT' : 'PAPER SECTION'} <span className="kicker-separator">·</span> {paperDocument ? `PAGE ${activePaperSection?.page || 1}` : `SECTION ${String(activeSection + 1).padStart(2, '0')}`}</div><h1>{activePaperSection?.title || (!paperDocument ? sections[activeSection].name : paperDocument.title)}</h1><p className="article-lead">{paperDocument ? `${paperDocument.source_filename} · full extracted section` : sections[activeSection].sub}</p>{paperDocument ? <div className="original-paper"><pre>{activePaperSection?.content || paperDocument.markdown_content || 'No extracted text is available for this section.'}</pre></div> : <div className="original-paper"><div className="paper-serif-title">{sections[activeSection].name}</div><p>{demoSectionCopy[activeSection]}</p>{activeSection === 4 && <div className="original-equation">Attention(Q, K, V) = softmax(QK<sup>T</sup> / √d<sub>k</sub>)V <span>(1)</span></div>}</div>}<button className="return-explainer" onClick={() => setMode('explainer')}><Sparkles size={14} /> Return to paper overview</button></motion.article>}
      </section>

      {rightOpen && <aside className="right-sidebar">
        <div className="artifact-heading"><div><span className="eyebrow">BUILT FROM THIS PAPER</span><div className="artifact-title">Your study kit <span className="sparkle-small"><Sparkles size={12} /></span></div></div><button className="quiet-icon" aria-label="Collapse artifacts" onClick={() => setRightOpen(false)}><PanelRightClose size={15} /></button></div>
        <div className="artifact-tabs" role="tablist">{artifactTabs.map(item => { const Icon = item.icon; return <button key={item.id} role="tab" aria-selected={tab === item.id} onClick={() => setTab(item.id)} className={tab === item.id ? 'tab-selected' : ''}><Icon size={14} /><span>{item.label}</span></button> })}</div>
        {activeJob && ['queued', 'processing'].includes(activeJob.status) ? <div className="artifact-empty"><Cpu size={17} /><strong>Study kit is building</strong><span>Architecture, code and recall cards will appear here when analysis finishes.</span></div> : <AnimatePresence mode="wait">{tab === 'map' && <motion.div className="artifact-panel" key="map" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -5 }} transition={{ duration: .16 }}>
          <div className="panel-meta"><span className="panel-eyebrow">{paperDocument ? 'EXTRACTED OUTLINE' : 'THE BIG PICTURE'}</span><button className="quiet-icon"><MoreHorizontal size={15} /></button></div><h2>{paperDocument ? 'Paper structure' : 'Transformer encoder'}</h2><p className="panel-description">{paperDocument ? `${paperSections.length} sections mapped across ${paperPageCount} pages of the source PDF.` : 'Follow how information flows through one encoder layer.'}</p>
          {studyKit ? <div className="diagram-stage paper-diagram"><Suspense fallback={<p className="loading-inline">Preparing paper map…</p>}><MermaidPreview source={studyKit.diagram_mermaid}/></Suspense></div> : <div className="diagram-stage"><div className="diagram-grid" /><div className="flow-node input-node"><span className="flow-icon input-icon"><FileText size={13} /></span><span><strong>Input</strong><small>Token embeddings</small></span><span className="node-index">01</span></div><div className="connector"><span /></div><button className="flow-node attention-node" onClick={() => notify('Multi-head attention: attends across all input positions')}><span className="flow-icon attention-icon"><GitBranch size={13} /></span><span><strong>Multi-head attention</strong><small>Attend to all positions</small></span><span className="node-index">02</span></button><div className="connector"><span /></div><div className="merge-line"><span /><span /></div><div className="split-nodes"><div className="mini-node">Add & norm</div><div className="mini-node residual"><span>＋</span> Residual</div></div><div className="connector"><span /></div><div className="flow-node feedforward"><span className="flow-icon feed-icon"><Layers3 size={13} /></span><span><strong>Feed-forward</strong><small>Transform each position</small></span><span className="node-index">03</span></div><div className="connector"><span /></div><div className="flow-node output-node"><span className="flow-icon output-icon"><Check size={13} /></span><span><strong>Output</strong><small>Contextual representations</small></span></div></div>}
          <div className="diagram-foot"><span><i className="legend-line" /> reading order</span><span>{paperDocument ? `${paperSections.length} sections · ${paperPageCount} pages` : '6 operations · 1 layer'}</span><button onClick={() => notify('Diagram expanded')}>Expand <ExternalLink size={11} /></button></div>
          {!studyKit && <details className="mermaid-details"><summary>View generated Mermaid source</summary><Suspense fallback={<p className="loading-inline">Loading diagram renderer…</p>}><MermaidPreview source={studyKit?.diagram_mermaid} /></Suspense></details>}
          {!studyKit && <div className="panel-tip"><span className="tip-star"><Sparkles size={12} /></span><p><strong>Notice the residual connection?</strong><span>It helps gradients flow through the whole network.</span></p></div>}
          <button className="secondary-action" onClick={() => notify('Architecture diagram exported')}><Download size={14} /> Export diagram</button>
        </motion.div>}
        {tab === 'code' && <motion.div className="artifact-panel code-panel" key="code" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -5 }} transition={{ duration: .16 }}>
          {!studyKit ? <><div className="panel-meta"><span className="panel-eyebrow">TRY IT YOURSELF</span><span className="runtime-pill"><i /> PYTHON</span></div><h2>Scaled dot-product</h2><p className="panel-description">A minimal PyTorch implementation of the equation.</p><div className="code-window"><div className="code-top"><span className="code-dots"><i /><i /><i /></span><span>attention.py</span><button title="Copy code" onClick={copyCode}><Clipboard size={13} /></button></div><pre className="code-content">{code.split('\n').map((line, i) => <div key={i} className="code-line"><span className="line-no">{String(i + 1).padStart(2, '0')}</span><code>{highlightCode(line)}</code></div>)}</pre></div><Suspense fallback={<p className="loading-inline">Preparing sandbox…</p>}><PyodideRunner/></Suspense><div className="code-caption"><span><CheckCircle2 size={13} /> Example code · PyTorch needs a native runtime</span><button onClick={() => notify('Code copied to clipboard')}>Copy snippet <Plus size={12} /></button></div></> : <><div className="panel-meta"><span className="panel-eyebrow">EXTRACTED CODE</span><span className="runtime-pill"><i /> LOCAL PDF</span></div><h2>Runnable examples</h2>{studyKit.python_code ? <><div className="code-window"><div className="code-top"><span className="code-dots"><i/><i/><i/></span><span>paper-snippet.py</span><button title="Copy code" onClick={copyCode}><Clipboard size={13}/></button></div><pre className="code-content">{studyKit.python_code.split('\n').map((line, i) => <div key={i} className="code-line"><span className="line-no">{String(i + 1).padStart(2, '0')}</span><code>{highlightCode(line)}</code></div>)}</pre></div><Suspense fallback={<p className="loading-inline">Preparing sandbox…</p>}><PyodideRunner initialCode={studyKit.python_code} key={studyKit.python_code}/></Suspense></> : <div className="artifact-empty"><Code2 size={17}/><strong>No code block detected</strong><span>The PDF text did not contain a fenced Python snippet. Code generation needs an AI provider, which is not configured.</span></div>}</>}
        </motion.div>}
        {tab === 'motion' && <motion.div className="artifact-panel motion-panel" key="motion" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -5 }} transition={{ duration: .16 }}><div className="panel-meta"><span className="panel-eyebrow">MATH MOTION STUDIO</span><span className="runtime-pill"><i/> REMOTION</span></div><h2>Derivation, in motion.</h2><p className="panel-description">Scrub through the attention equation one idea at a time.</p><Suspense fallback={<p className="loading-inline">Loading motion studio…</p>}><MathMotionPlayer composition={studyKit?.video_composition_props}/></Suspense><div className="panel-tip"><span className="tip-star"><Sparkles size={12}/></span><p><strong>Step narration is ready to record.</strong><span>Timeline props are generated by the analysis pipeline.</span></p></div></motion.div>}
        {tab === 'learn' && <motion.div className="artifact-panel learn-panel" key="learn" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -5 }} transition={{ duration: .16 }}>
          <div className="panel-meta"><span className="panel-eyebrow">ACTIVE RECALL</span><span className="streak-pill">✦ 3 DAY STREAK</span></div><h2>Lock it in.</h2><p className="panel-description">A little retrieval practice goes a long way.</p><div className="flashcard-wrap" onClick={() => setFlipped(!flipped)} role="button" tabIndex="0" onKeyDown={e => e.key === 'Enter' && setFlipped(!flipped)}><motion.div className="flashcard" animate={{ rotateY: flipped ? 180 : 0 }} transition={{ duration: .46 }}><div className="card-face card-front"><div className="card-topline"><span>QUESTION {String(card + 1).padStart(2, '0')} <i>/ {String(activeCards.length).padStart(2, '0')}</i></span><span className="card-mark"><BrainCircuit size={15} /></span></div><span className="card-question">{activeCards[card % activeCards.length].q}</span><span className="flip-hint"><span>Click to reveal</span><span className="flip-key">↻</span></span></div><div className="card-face card-back"><div className="card-topline"><span>THE ANSWER</span><span className="card-mark answer-mark"><Check size={14} /></span></div><span className="card-answer">{activeCards[card % activeCards.length].a}</span><span className="flip-hint"><span>Click to flip back</span><span className="flip-key">↻</span></span></div></motion.div></div><div className="card-controls"><button onClick={() => { setCard((card + activeCards.length - 1) % activeCards.length); setFlipped(false) }} aria-label="Previous card"><ChevronLeft size={15} /></button><span className="card-dots">{activeCards.map((_, i) => <button aria-label={`Go to card ${i + 1}`} key={i} className={i === card ? 'dot-active' : ''} onClick={() => { setCard(i); setFlipped(false) }} />)}</span><button onClick={() => { setCard((card + 1) % activeCards.length); setFlipped(false) }} aria-label="Next card"><ChevronRight size={15} /></button></div><div className="viva-divider"><span>GO ONE LEVEL DEEPER</span><span>✳</span></div>{studyKit ? studyKit.viva_questions?.map((item, index) => <details className="viva-item" key={index}><summary><span><CircleHelp size={14} /> {item.question}</span><ChevronDown size={14} /></summary><p>{item.answer_hint}</p></details>) : <><details className="viva-item"><summary><span><CircleHelp size={14} /> Why can attention model long-range dependencies better than recurrence?</span><ChevronDown size={14} /></summary><p>Self-attention connects every position directly, so the path between distant tokens stays short—regardless of sequence length.</p></details><details className="viva-item"><summary><span><CircleHelp size={14} /> What is the role of positional encodings?</span><ChevronDown size={14} /></summary><p>They inject token order into the input, since self-attention on its own treats a sequence as a set.</p></details></>}<button className="secondary-action export-cards" onClick={exportCards}><Download size={14} /> Export flashcards <span>.apkg</span></button>
        </motion.div>}
        </AnimatePresence>}
        <div className="artifact-footer"><span><span className="footer-spark">✳</span> Generated from this paper</span><button onClick={() => notify('Regenerating study kit...')}><Sparkles size={12} /> Regenerate</button></div>
      </aside>}
    </div>

    <footer className="statusbar"><div><span className="status-brand">P</span><span>PaperVerse</span><span className="status-sep">/</span><span>{paperDocument?.title || 'Attention Is All You Need'}</span></div><div><span className="status-ready"><i /> {activeJob?.status === 'processing' ? `${activeJob.stage || 'PROCESSING'} · ${activeJob.progress}%` : activeJob?.status === 'queued' ? 'ANALYSIS QUEUED' : 'ALL SYSTEMS READY'}</span><span className="status-sep">·</span><span>{studyKit ? 'Study kit generated' : 'Local workspace'}</span><button className="status-help" onClick={() => notify('Shortcuts: ⌘K search · ← → navigate sections')}>⌘ K <span>shortcuts</span></button></div></footer>

    <AnimatePresence>{uploadOpen && <motion.div className="modal-scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setUploadOpen(false)}><motion.div className="upload-modal" initial={{ y: 13, opacity: 0, scale: .985 }} animate={{ y: 0, opacity: 1, scale: 1 }} exit={{ y: 8, opacity: 0 }} onClick={e => e.stopPropagation()}><div className="modal-heading"><span className="modal-mark"><BookOpen size={17} /></span><div><h2>Bring a paper to life.</h2><p>Drop in a research paper and we'll build your study kit.</p></div><button className="quiet-icon" onClick={() => setUploadOpen(false)}><X size={17} /></button></div><div className={`dropzone ${dragging ? 'is-dragging' : ''} ${uploadBusy ? 'uploading' : ''}`} onDragEnter={e => { e.preventDefault(); setDragging(true) }} onDragOver={e => e.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); acceptFile(e.dataTransfer.files?.[0]) }} onClick={() => !uploadBusy && fileRef.current?.click()}><input ref={fileRef} type="file" accept=".pdf,application/pdf" hidden onChange={e => acceptFile(e.target.files?.[0])} /><span className="upload-icon"><Upload size={19} /></span><strong>{uploadBusy ? 'Uploading your PDF…' : <>Drop your PDF here, or <i>browse files</i></>}</strong><span>{uploadBusy ? `Sending PDF · ${uploadProgress}%` : 'PDF up to 50 MB'}</span>{uploadBusy && <div className="upload-track"><span style={{ width: `${uploadProgress}%` }} /></div>}</div><div className="or-divider"><span>OR ADD FROM ARXIV</span></div><div className="arxiv-field"><span className="arxiv-icon">arχiv</span><input id="paper-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Paste an arXiv URL or paper ID…" /><button disabled={!search.trim()} onClick={async () => { setUploadBusy(true); try { const result = await importArxiv(search); setPaperId(result.paper_id); setPaperDocument(null); setStudyKit(null); setActiveSection(0); setSectionFocus(false); setActiveJob({ job_id: result.job_id, status: 'queued', progress: 0, stage: 'queued' }); setSearch(''); setUploadOpen(false); notify('arXiv paper queued for analysis') } catch (error) { notify(error.message || 'Could not import arXiv paper') } finally { setUploadBusy(false) } }}><ChevronRight size={15} /></button></div><div className="modal-foot"><span><span className="privacy-icon"><Check size={10} /></span> Your papers stay private</span><span>PDF · arXiv</span></div></motion.div></motion.div>}</AnimatePresence>
    <AnimatePresence>{toast && <motion.div className="toast" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 7 }}><CheckCircle2 size={15} />{toast}</motion.div>}</AnimatePresence>
  </main>
}

function highlightCode(line) {
  const escaped = line.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  return <span dangerouslySetInnerHTML={{ __html: escaped.replace(/(#.*)$/g, '<span class="syn-comment">$1</span>').replace(/\b(import|from|def|return)\b/g, '<span class="syn-keyword">$1</span>').replace(/\b(torch|F)\b/g, '<span class="syn-module">$1</span>').replace(/(scaled_dot_product)/g, '<span class="syn-function">$1</span>').replace(/(\d+(?:\.\d+)?)/g, '<span class="syn-number">$1</span>') }} />
}

createRoot(document.getElementById('root')).render(<App />)
