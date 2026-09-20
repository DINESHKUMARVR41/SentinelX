import { useState, useEffect, useRef, useCallback } from 'react'

// Single WebSocket with capped exponential backoff. Dashboard works without it (polling + local demo).
export function useWebSocket(url) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const ws = useRef(null)

  useEffect(() => {
    let closed = false
    let attempt = 0
    let timer = null

    const connect = () => {
      if (closed) return
      try {
        const sock = new WebSocket(url)
        ws.current = sock
        sock.onopen = () => { attempt = 0; setConnected(true) }
        sock.onclose = () => {
          setConnected(false)
          if (closed) return
          attempt = Math.min(attempt + 1, 5)
          timer = setTimeout(connect, Math.min(3000 * 2 ** (attempt - 1), 30000))
        }
        sock.onerror = () => {}
        sock.onmessage = (event) => {
          try { setLastMessage(JSON.parse(event.data)) } catch { /* ignore malformed */ }
        }
      } catch {
        setConnected(false)
        timer = setTimeout(connect, 30000)
      }
    }
    connect()

    return () => {
      closed = true
      clearTimeout(timer)
      if (ws.current) { ws.current.onclose = null; ws.current.close() }
    }
  }, [url])

  const send = useCallback((data) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify(data))
  }, [])

  return { connected, lastMessage, send }
}
