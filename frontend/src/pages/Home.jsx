import { useState } from "react"
import Dashboard from "./Dashboard"

export default function Home() {
  const [file, setFile]       = useState(null)
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setResult(null)
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail)
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Once we have results, show the dashboard
  if (result) {
    return <Dashboard data={result} onReset={() => setResult(null)} />
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center gap-6 p-8">
      <div className="flex flex-col items-center gap-2">
        <h1 className="text-4xl font-bold text-white">🕵️ Code Archaeologist</h1>
        <p className="text-gray-400 text-sm">Upload a Python file to excavate its secrets</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 w-full max-w-md flex flex-col gap-4">
        <label className="flex flex-col gap-2">
          <span className="text-xs text-gray-500 uppercase tracking-widest">Select file</span>
          <input
            type="file"
            accept=".py"
            onChange={handleFileChange}
            className="text-sm text-gray-300 file:mr-3 file:py-1 file:px-3
                       file:rounded file:border-0 file:text-xs
                       file:bg-gray-800 file:text-gray-300
                       hover:file:bg-gray-700 cursor-pointer"
          />
        </label>

        {file && (
          <p className="text-xs text-gray-500">
            {file.name} · {(file.size / 1024).toFixed(1)} KB
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40
                     disabled:cursor-not-allowed text-white text-sm font-medium
                     py-2 px-4 rounded-lg transition-colors"
        >
          {loading ? "Excavating..." : "Analyze File"}
        </button>

        {error && (
          <p className="text-red-400 text-xs bg-red-950 border border-red-900 rounded p-2">
            {error}
          </p>
        )}
      </div>
    </div>
  )
}