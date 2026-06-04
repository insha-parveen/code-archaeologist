import { useState } from "react"
import GalaxyBackground from "../components/GalaxyBackground"
import API_BASE from "../config"
import Dashboard from "./Dashboard"
import MultiResults from "./MultiResults"

export default function Home() {
  const [file, setFile]               = useState(null)
  const [githubUrl, setGithubUrl]     = useState("")
  const [mode, setMode]               = useState("upload")
  const [result, setResult]           = useState(null)
  const [multiResults, setMultiResults] = useState(null)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState(null)

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
      const res = await fetch(`${API_BASE}/api/upload`, {   // ← FIXED: was /api/github
        method: "POST",
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json()
        const message = typeof err.detail === "string"
          ? err.detail
          : Array.isArray(err.detail)
          ? err.detail.map(e => e.msg).join(", ")
          : "Upload failed. Check the file and try again."
        throw new Error(message)
      }
      setResult(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGithub = async () => {
    if (!githubUrl.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/github`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: githubUrl.trim() }),
      })
      if (!res.ok) {
        const err = await res.json()
        const message = typeof err.detail === "string"
          ? err.detail
          : Array.isArray(err.detail)
          ? err.detail.map(e => e.msg).join(", ")
          : "GitHub fetch failed. Check the URL and try again."
        throw new Error(message)
      }
      const data = await res.json()
      if (data.results.length === 1) {
        setResult(data.results[0])
      } else {
        setMultiResults(data)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setMultiResults(null)
    setFile(null)
    setGithubUrl("")
    setError(null)
  }

  const handleModeSwitch = (m) => {
    setMode(m)
    setError(null)
    setFile(null)
    setGithubUrl("")
  }

  if (result)       return <Dashboard data={result} onReset={handleReset} />
  if (multiResults) return <MultiResults data={multiResults} onReset={handleReset} />

  return (
    <div style={{ position: "relative", minHeight: "100vh",
                  background: "#030712", overflow: "hidden" }}>
      <GalaxyBackground />

      <div style={{ position: "relative", zIndex: 1 }}
           className="min-h-screen flex flex-col items-center
                      justify-center gap-6 p-8">

        {/* Title */}
        <div className="flex flex-col items-center gap-2 anim-fade-down">
          <h1 className="text-5xl font-bold text-white tracking-tight">
            🕵️ Code Archaeologist
          </h1>
          <p className="text-gray-400 text-sm">
            Upload a file or paste a GitHub URL to excavate its secrets
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap justify-center">
            {[".py", ".js", ".jsx", ".ts", ".tsx",
              ".java", ".go", ".rs", ".cpp", ".cs"].map(ext => (
              <span key={ext}
                    className="text-xs px-2 py-0.5 rounded-full
                               bg-gray-800 text-gray-400 border border-gray-700">
                {ext}
              </span>
            ))}
          </div>
        </div>

        {/* Mode toggle */}
        <div className="flex items-center gap-1 bg-gray-900 border
                        border-gray-800 rounded-lg p-1">
          {["upload", "github"].map(m => (
            <button
              key={m}
              onClick={() => handleModeSwitch(m)}
              className={`px-4 py-1.5 text-xs rounded-md transition-all duration-200
                          ${mode === m
                            ? "bg-indigo-600 text-white"
                            : "text-gray-400 hover:text-white"
                          }`}
            >
              {m === "upload" ? "📁 Upload File" : "🐙 GitHub URL"}
            </button>
          ))}
        </div>

        {/* Input card */}
        <div className="bg-gray-900 bg-opacity-80 border border-gray-800
                        rounded-xl p-6 w-full max-w-md flex flex-col gap-4
                        anim-scale-in delay-200"
             style={{ backdropFilter: "blur(12px)" }}>

          {mode === "upload" ? (
            <>
              <label className="flex flex-col gap-2">
                <span className="text-xs text-gray-500 uppercase tracking-widest">
                  Select file
                </span>
                <input
                  type="file"
                  accept=".py,.js,.jsx,.ts,.tsx,.java,.go,.rs,.cpp,.c,.h,.cs,.rb,.php,.kt,.swift"
                  onChange={handleFileChange}
                  className="text-sm text-gray-300
                             file:mr-3 file:py-1 file:px-3
                             file:rounded file:border-0 file:text-xs
                             file:bg-gray-800 file:text-gray-300
                             hover:file:bg-gray-700 cursor-pointer"
                />
              </label>

              {file && (
                <div className="flex flex-col gap-1 anim-fade-in">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      {file.name} · {(file.size / 1024).toFixed(1)} KB
                    </p>
                    <span className="text-xs px-2 py-0.5 rounded-full
                                     bg-indigo-950 text-indigo-400
                                     border border-indigo-800">
                      {file.name.split(".").pop()}
                    </span>
                  </div>
                  {file.size > 50 * 1024 && (
                    <p className="text-xs text-amber-400 bg-amber-950
                                  border border-amber-900 rounded px-2 py-1">
                      ⚠ Large file — analysis may use chunking and take longer
                    </p>
                  )}
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!file || loading}
                className={`text-white text-sm font-medium py-2.5 px-4
                            rounded-lg transition-all duration-200
                            disabled:opacity-40 disabled:cursor-not-allowed
                            ${loading
                              ? "bg-indigo-700 anim-pulse-glow"
                              : "bg-indigo-600 hover:bg-indigo-500"
                            }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-3.5 h-3.5 border-2
                                     border-white border-t-transparent
                                     rounded-full animate-spin" />
                    {file && file.size > 50 * 1024
                      ? "Analyzing large file..."
                      : "Excavating..."}
                  </span>
                ) : "Analyze File"}
              </button>
            </>
          ) : (
            <>
              <label className="flex flex-col gap-2">
                <span className="text-xs text-gray-500 uppercase tracking-widest">
                  GitHub URL
                </span>
                <input
                  type="text"
                  value={githubUrl}
                  onChange={e => setGithubUrl(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && !loading && handleGithub()}
                  placeholder="https://github.com/user/repo/blob/main/file.py"
                  className="text-xs bg-gray-800 border border-gray-700
                             rounded-lg px-3 py-2 text-gray-300
                             placeholder-gray-600 focus:outline-none
                             focus:border-indigo-600 transition-colors"
                />
              </label>

              <div className="flex flex-col gap-1.5 bg-gray-800
                              rounded-lg px-3 py-2">
                <p className="text-xs text-gray-500 font-medium">
                  Supported formats:
                </p>
                <p className="text-xs text-gray-600 font-mono">
                  github.com/user/repo/blob/main/file.py
                </p>
                <p className="text-xs text-gray-600 font-mono">
                  github.com/user/repo
                </p>
              </div>

              <button
                onClick={handleGithub}
                disabled={!githubUrl.trim() || loading}
                className={`text-white text-sm font-medium py-2.5 px-4
                            rounded-lg transition-all duration-200
                            disabled:opacity-40 disabled:cursor-not-allowed
                            ${loading
                              ? "bg-indigo-700 anim-pulse-glow"
                              : "bg-indigo-600 hover:bg-indigo-500"
                            }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-3.5 h-3.5 border-2
                                     border-white border-t-transparent
                                     rounded-full animate-spin" />
                    Fetching from GitHub...
                  </span>
                ) : "Analyze from GitHub"}
              </button>
            </>
          )}

          {error && (
            <div className="text-red-400 text-xs bg-red-950 border
                            border-red-900 rounded p-2 anim-fade-up">
              <p className="font-medium mb-0.5">Error</p>
              <p>{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
