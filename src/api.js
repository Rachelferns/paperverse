const API_ROOT = (import.meta.env.VITE_API_BASE || 'http://localhost:8001/api/v1').replace(/\/$/, '')

async function readResponse(response) {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `PaperVerse API returned ${response.status}`)
  return body
}

export function uploadPdf(file, onProgress = () => {}) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', `${API_ROOT}/papers/upload`)
    request.upload.onprogress = event => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100))
    }
    request.onload = () => {
      let body = {}
      try { body = JSON.parse(request.responseText) } catch {}
      if (request.status < 200 || request.status >= 300) reject(new Error(body.detail || `PaperVerse API returned ${request.status}`))
      else resolve(body)
    }
    request.onerror = () => reject(new Error('Upload connection failed. Check that the PaperVerse API is running.'))
    request.onabort = () => reject(new Error('Upload was cancelled.'))
    const form = new FormData()
    form.append('file', file)
    request.send(form)
  })
}

export async function importArxiv(url) {
  return readResponse(await fetch(`${API_ROOT}/papers/arxiv`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url })
  }))
}

export async function getPaper(paperId) {
  return readResponse(await fetch(`${API_ROOT}/papers/${paperId}`))
}

export async function getRecentPaper() {
  return readResponse(await fetch(`${API_ROOT}/papers/recent`))
}

export function watchJob(jobId, onUpdate, onError) {
  const events = new EventSource(`${API_ROOT}/jobs/${jobId}/events`)
  let pollTimer
  let stopped = false
  let finished = false
  events.addEventListener('job', event => {
    const job = JSON.parse(event.data)
    onUpdate(job)
    if (job.status === 'completed' || job.status === 'failed') { finished = true; events.close(); clearInterval(pollTimer) }
  })
  events.onerror = () => {
    events.close()
    if (pollTimer || stopped || finished) return
    pollTimer = window.setInterval(async () => {
      try {
        const job = await readResponse(await fetch(`${API_ROOT}/jobs/${jobId}`))
        onUpdate(job)
        if (job.status === 'completed' || job.status === 'failed') { finished = true; clearInterval(pollTimer); pollTimer = null }
      } catch (error) { onError?.(error) }
    }, 1200)
  }
  return () => { stopped = true; events.close(); clearInterval(pollTimer) }
}
