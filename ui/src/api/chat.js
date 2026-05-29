import request from './request'

export function askQuestionStream(data, onMessage, onError, onDone) {
  const token = localStorage.getItem('access_token')
  const controller = new AbortController()

  fetch('/api/v1/chat/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      onError && onError(`请求失败: ${response.status}`)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let receivedDoneOrError = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.slice(6))
            if (parsed.type === 'error') {
              receivedDoneOrError = true
              onError && onError(parsed.content)
            } else if (parsed.type === 'done') {
              receivedDoneOrError = true
              onDone && onDone(parsed)
            } else {
              onMessage && onMessage(parsed)
            }
          } catch {
            // ignore parse errors for incomplete chunks
          }
        }
      }
    }

    // 流正常结束但没有 done/error 事件（如人工审核中断）
    if (!receivedDoneOrError) {
      onDone && onDone({})
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      onError && onError('网络连接失败')
    }
  })

  return () => controller.abort()
}

export function resumeQuestionStream(sessionId, decision, onMessage, onError, onDone) {
  const token = localStorage.getItem('access_token')
  const controller = new AbortController()

  fetch('/api/v1/chat/resume', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ session_id: sessionId, decision }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      onError && onError(`恢复失败: ${response.status}`)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let receivedDoneOrError = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.slice(6))
            if (parsed.type === 'error') {
              receivedDoneOrError = true
              onError && onError(parsed.content)
            } else if (parsed.type === 'done') {
              receivedDoneOrError = true
              onDone && onDone(parsed)
            } else {
              onMessage && onMessage(parsed)
            }
          } catch {
            // ignore parse errors for incomplete chunks
          }
        }
      }
    }

    if (!receivedDoneOrError) {
      onDone && onDone({})
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      onError && onError('恢复请求失败')
    }
  })

  return () => controller.abort()
}

export function getSessions() {
  return request.get('/chat/session/list')
}

export function createSession(data) {
  return request.post('/chat/session/create', data)
}

export function deleteSession(sessionId) {
  return request.delete('/chat/session/delete', { params: { session_id: sessionId } })
}

export function getSessionHistory(sessionId) {
  return request.get('/chat/session/history', { params: { session_id: sessionId } })
}
