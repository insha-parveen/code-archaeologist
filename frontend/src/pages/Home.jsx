import { useState } from "react"

export default function Home() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setResult(null)
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) return

    setLoading(true)
    setError(null)

    // FormData is the browser's way of packaging a file for multipart/form-data
    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
        // Note: do NOT set Content-Type header manually — browser sets it automatically
        // with the correct boundary for multipart/form-data
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">🕵️ Code Archaeologist</h1>
      <p className="text-gray-400">Upload a Python file to begin excavation</p>

      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-lg flex flex-col gap-4">
        <input
          type="file"
          accept=".py"
          onChange={handleFileChange}
          className="text-sm text-gray-300"
        />

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed
                     text-white font-semibold py-2 px-4 rounded-lg transition"
        >
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        {result && (
          <div className="bg-gray-800 rounded-lg p-4 text-sm flex flex-col gap-2">
            <p><span className="text-gray-400">File:</span> {result.filename}</p>
            <p><span className="text-gray-400">Size:</span> {result.size_bytes} bytes</p>
            <p><span className="text-gray-400">Lines:</span> {result.line_count}</p>
            <pre className="bg-gray-900 rounded p-3 text-xs text-green-400 overflow-auto max-h-40">
              {result.preview}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}