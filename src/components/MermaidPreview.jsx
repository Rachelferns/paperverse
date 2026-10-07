import React, { useEffect, useRef, useState } from 'react'

export default function MermaidPreview({ source }) {
  const target = useRef(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    const render = async () => {
      try {
        const { default: mermaid } = await import('mermaid')
        mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'strict', flowchart: { curve: 'basis', htmlLabels: false } })
        const id = `paperverse-mermaid-${Math.random().toString(36).slice(2)}`
        const { svg } = await mermaid.render(id, source || 'flowchart TD\nA[Upload a paper] --> B[Build a study kit]')
        if (alive && target.current) { target.current.innerHTML = svg; setError('') }
      } catch (reason) { if (alive) setError(reason.message || 'Could not render the Mermaid diagram.') }
    }
    render()
    return () => { alive = false }
  }, [source])
  return <div className="mermaid-preview">{error ? <p className="mermaid-error">Diagram syntax issue: {error}</p> : <div ref={target}/>}</div>
}
