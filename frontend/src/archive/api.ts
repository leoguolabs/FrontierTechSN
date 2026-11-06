export type Topic = {
  id: string
  title: string
  document_name: string
  created_at: string
}

export type TopicDetail = Topic & { preview_html: string }

export type Result = {
  id: string
  title: string
  created_at: string
  topic_id: string
  topic_title: string
  video_name: string
  cover_name: string
}

export const archiveApi = '/api/frontier-archive'
export const sessionExpired = 'archive-session-expired'

export function assetUrl(result: Result, asset: 'video' | 'cover') {
  return `${archiveApi}/topics/${result.topic_id}/results/${result.id}/${asset}`
}

function apiError(status: number, detail: unknown, expireSession: boolean) {
  if (status === 401 && expireSession) window.dispatchEvent(new Event(sessionExpired))
  return new Error(typeof detail === 'string' ? detail : `请求失败（${status}）`)
}

export async function requestJson<T>(path: string, options?: RequestInit, expireSession = true): Promise<T> {
  const response = await fetch(path, options)
  if (response.status === 204) return undefined as T
  const data = await response.json().catch(() => null)
  if (!response.ok) throw apiError(response.status, data?.detail, expireSession)
  return data as T
}

export function upload<T>(path: string, data: FormData, onProgress: (value: number) => void, signal: AbortSignal) {
  return new Promise<T>((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', path)
    request.responseType = 'json'
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.round(event.loaded / event.total * 100))
    }
    request.onload = () => {
      if (request.status === 201) resolve(request.response as T)
      else reject(apiError(request.status, request.response?.detail, true))
    }
    request.onerror = () => reject(new Error('连接中断，请检查网络后再试'))
    request.onabort = () => reject(new Error('上传已取消'))
    const abort = () => request.abort()
    signal.addEventListener('abort', abort, { once: true })
    request.onloadend = () => signal.removeEventListener('abort', abort)
    request.send(data)
  })
}
