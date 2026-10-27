import React, { useState } from 'react'
import { Play } from 'lucide-react'

const starter = `print("Paste a Python snippet to run it in this browser tab.")`
const pyodideCdn = 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/'
let runtimePromise

function loadRuntime() {
  if (runtimePromise) return runtimePromise
  if (window.loadPyodide) return runtimePromise = window.loadPyodide({ indexURL: pyodideCdn })
  runtimePromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `${pyodideCdn}pyodide.js`
    script.onload = () => window.loadPyodide({ indexURL: pyodideCdn }).then(resolve, reject)
    script.onerror = () => reject(new Error('Could not load Pyodide from jsDelivr. Check your connection and try again.'))
    document.head.appendChild(script)
  })
  return runtimePromise
}

export default function PyodideRunner({ initialCode }) {
  const [source, setSource] = useState(initialCode || starter)
  const [output, setOutput] = useState('')
  const [busy, setBusy] = useState(false)
  const run = async () => {
    setBusy(true); setOutput('Starting Python runtime…')
    try {
      const pyodide = await loadRuntime()
      await pyodide.loadPackage('numpy')
      let captured = ''
      pyodide.setStdout({ batched: text => { captured += `${text}\n` } })
      await pyodide.runPythonAsync(source)
      setOutput(captured || 'Code completed with no printed output.')
    } catch (error) { setOutput(`Python error: ${error.message}`) }
    finally { setBusy(false) }
  }
  return <div className="pyodide-runner"><div className="pyodide-title"><span>PYODIDE QUICK RUN</span><span>Python · NumPy</span></div><textarea aria-label="Python sandbox code" value={source} spellCheck="false" onChange={event => setSource(event.target.value)} /><button className="run-button" onClick={run} disabled={busy}><Play size={13} fill="currentColor"/>{busy ? 'Starting Python…' : 'Run in browser'}</button>{output && <pre className="pyodide-output">{output}</pre>}<p>Runs in this tab with WebAssembly. PyTorch isn't preloaded in Pyodide.</p></div>
}
