import { useState } from "react"
import GalaxyBackground from "../components/GalaxyBackground"
import Dashboard from "./Dashboard"

export default function MultiResults({ data, onReset }) {
  const [selected, setSelected] = useState(null)

  if (selected !== null) {
    return (
      <Dashboard
        data={data.results[selected]}
        onReset={() => setSelected(null)}
      />
    )
  }

  return (
    <div style={{ position: "relative", minHeight: "100vh",
                  background: "#030712", overflow: "hidden" }}>
      <GalaxyBackground />

      <div style={{ position: "relative", zIndex: 1 }}
           className="min-h-screen p-6 flex flex-col gap-5
                      max-w-4xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between anim-fade-down">
          <div className="flex flex-col gap-0.5">
            <h1 className="text-white font-medium text-lg">
              🕵️ Code Archaeologist
            </h1>
            <p className="text-gray-500 text-xs">
              {data.total_files} files analyzed from GitHub
            </p>
          </div>
          <button
            onClick={onReset}
            className="text-xs text-gray-400 border border-gray-700
                       hover:border-gray-500 hover:text-white
                       px-3 py-1.5 rounded-lg transition-all duration-200"
          >
            Analyze another
          </button>
        </div>

        {/* URL badge */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg
                        px-4 py-2 anim-fade-up delay-100">
          <p className="text-xs text-gray-500">Source</p>
          <p className="text-xs text-indigo-400 font-mono truncate">
            {data.url}
          </p>
        </div>

        {/* File list */}
        <div className="flex flex-col gap-3">
          {data.results.map((result, i) => {
            const avg     = result.wtf_analysis.average_wtf
            const fossils = result.fossils.total_fossils
            const scoreColor = avg >= 70
              ? "text-red-400" : avg >= 40
              ? "text-amber-400" : "text-green-400"

            return (
              <div key={i}
                   onClick={() => setSelected(i)}
                   className="bg-gray-900 bg-opacity-80 border border-gray-800
                              rounded-xl p-4 cursor-pointer
                              hover:border-indigo-700 transition-all duration-200
                              anim-fade-up"
                   style={{
                     backdropFilter: "blur(10px)",
                     animationDelay: `${i * 80}ms`
                   }}>

                <div className="flex items-center justify-between mb-2">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium text-white">
                      {result.filename}
                    </span>
                    <span className="text-xs text-gray-500 font-mono">
                      {result.github_path}
                    </span>
                  </div>
                  <span className="text-xs text-indigo-400 border
                                   border-indigo-800 px-2 py-0.5 rounded-full">
                    View →
                  </span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-gray-500">Avg WTF</span>
                    <span className={`text-lg font-medium ${scoreColor}`}>
                      {avg}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-gray-500">Fossils</span>
                    <span className={`text-lg font-medium
                                     ${fossils > 0
                                       ? "text-amber-400"
                                       : "text-green-400"}`}>
                      {fossils}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-gray-500">Functions</span>
                    <span className="text-lg font-medium text-white">
                      {result.wtf_analysis.total_functions}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs text-gray-500">Lines</span>
                    <span className="text-lg font-medium text-white">
                      {result.line_count}
                    </span>
                  </div>
                </div>

              </div>
            )
          })}
        </div>

        {/* Errors if any files failed */}
        {data.errors?.length > 0 && (
          <div className="bg-red-950 border border-red-900
                          rounded-xl p-4 anim-fade-up">
            <p className="text-xs text-red-400 font-medium mb-2">
              {data.errors.length} file(s) could not be analyzed:
            </p>
            {data.errors.map((e, i) => (
              <p key={i} className="text-xs text-red-500 font-mono">
                · {e.file}: {e.error}
              </p>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
