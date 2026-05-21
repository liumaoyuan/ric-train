import request from './request'

export function askQuestion(data) {
  return request.post('/chat/ask', data)
}

export function askQuestionStream(data, onMessage, onError, onDone) {
  const token = localStorage.getItem('access_token')
  const xhr = new XMLHttpRequest()
  xhr.open('POST', '/api/v1/chat/ask')
  xhr.setRequestHeader('Content-Type', 'application/json')
  xhr.setRequestHeader('Authorization', `Bearer ${token}`)
  xhr.responseType = 'text'

  let lastIndex = 0

  xhr.onprogress = () => {
    const newData = xhr.responseText.slice(lastIndex)
    lastIndex = xhr.responseText.length

    const lines = newData.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'error') {
            onError && onError(data.content)
          } else if (data.type === 'done') {
            onDone && onDone(data)
          } else {
            onMessage && onMessage(data)
          }
        } catch {
          // ignore parse errors for incomplete chunks
        }
      }
    }
  }

  xhr.onerror = () => {
    onError && onError('网络连接失败')
  }

  xhr.send(JSON.stringify(data))

  return () => xhr.abort()
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
