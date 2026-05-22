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
      const res = await fetch("http://127.0.0.1:8000/api/upload", {
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

  if (result) {
    return <Dashboard data={result} onReset={() => setResult(null)} />
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center gap-6 p-8">

      {/* Title — slides down */}
      <div className="flex flex-col items-center gap-2 anim-fade-down">
        <h1 className="text-5xl font-bold text-white tracking-tight">
          🕵️ Code Archaeologist
        </h1>
        <p className="text-gray-400 text-sm">
          Upload a Python file to excavate its secrets
        </p>
      </div>

      {/* Upload card — scales in with delay */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6
                      w-full max-w-md flex flex-col gap-4
                      anim-scale-in delay-200">

        <label className="flex flex-col gap-2">
          <span className="text-xs text-gray-500 uppercase tracking-widest">
            Select file
          </span>
          <input
            type="file"
            accept=".py"
            onChange={handleFileChange}
            className="text-sm text-gray-300
                       file:mr-3 file:py-1 file:px-3
                       file:rounded file:border-0 file:text-xs
                       file:bg-gray-800 file:text-gray-300
                       hover:file:bg-gray-700 cursor-pointer
                       transition-all duration-200"
          />
        </label>

        {/* File info — fades in when file selected */}
        {file && (
          <p className="text-xs text-gray-500 anim-fade-in">
            {file.name} · {(file.size / 1024).toFixed(1)} KB
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className={`text-white text-sm font-medium py-2.5 px-4 rounded-lg
                      transition-all duration-200
                      disabled:opacity-40 disabled:cursor-not-allowed
                      ${loading
                        ? "bg-indigo-700 anim-pulse-glow"
                        : "bg-indigo-600 hover:bg-indigo-500 hover:scale-[1.02] active:scale-[0.98]"
                      }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="inline-block w-3.5 h-3.5 border-2 border-white
                               border-t-transparent rounded-full animate-spin" />
              Excavating...
            </span>
          ) : (
            "Analyze File"
          )}
        </button>

        {error && (
          <p className="text-red-400 text-xs bg-red-950 border border-red-900
                        rounded p-2 anim-fade-up">
            {error}
          </p>
        )}
      </div>
    </div>
  )
}
