interface UploadSignature {
  signature: string
  timestamp: number
  api_key: string
  cloud_name: string
  public_id: string
}

/**
 * Uploads a project cover image directly from the browser to Cloudinary.
 * Flow: get signed params from FastAPI → POST file straight to Cloudinary CDN.
 * This bypasses the Nitro proxy entirely, which fixes multipart upload issues.
 */
export function useCloudinaryUpload() {
  const { api } = useAuth()

  async function uploadProjectImage(projectId: number, file: File): Promise<string> {
    // 1. Get a signed upload token from the backend (valid for ~1 minute).
    const sig = await api<UploadSignature>(`/api/v1/projects/${projectId}/upload-signature`)

    // 2. POST the file directly to Cloudinary — browser handles multipart boundary.
    const form = new FormData()
    form.append('file', file)
    form.append('api_key', sig.api_key)
    form.append('timestamp', String(sig.timestamp))
    form.append('signature', sig.signature)
    form.append('public_id', sig.public_id)

    const result = await $fetch<{ secure_url: string; public_id: string }>(
      `https://api.cloudinary.com/v1_1/${sig.cloud_name}/image/upload`,
      { method: 'POST', body: form },
    )

    return result.secure_url
  }

  return { uploadProjectImage }
}
