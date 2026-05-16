import WTFLeaderboard from "../components/WTFLeaderboard"
import FossilDetector from "../components/FossilDetector"

export default function Dashboard({ data, onReset }) {
  const { filename, line_count, fossils, wtf_analysis } = data

  const avgScore = wtf_analysis.average_wtf
  const totalFossils = fossils.total_fossils
  const unusedFns = fossils.unused_functions.length
  const cleanFns = wtf_analysis.functions.filter(f => f.wtf_score < 20).length

  const scoreColor = avgScore >= 70
    ? "text-red-400"
    : avgScore >= 40
    ? "text-amber-400"
    : "text-green-400"

  return (
    <div className="min-h-screen bg-gray-950 p-6 flex flex-col gap-5 max-w-4xl mx-auto">

      {/* Top bar */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-0.5">
          <h1 className="text-white font-medium text-lg">🕵️ Code Archaeologist</h1>
          <p className="text-gray-500 text-xs">
            {filename} · {line_count} lines
          </p>
        </div>
        <button
          onClick={onReset}
          className="text-xs text-gray-400 border border-gray-700 hover:border-gray-500
                     px-3 py-1.5 rounded-lg transition-colors"
        >
          Upload another
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-xs text-gray-500">Avg WTF score</span>
          <span className={`text-2xl font-medium ${scoreColor}`}>{avgScore}</span>
          <span className="text-xs text-gray-600">{wtf_analysis.total_functions} functions</span>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-xs text-gray-500">Total fossils</span>
          <span className={`text-2xl font-medium ${totalFossils > 0 ? "text-amber-400" : "text-green-400"}`}>
            {totalFossils}
          </span>
          <span className="text-xs text-gray-600">dead code artifacts</span>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-xs text-gray-500">Unused functions</span>
          <span className={`text-2xl font-medium ${unusedFns > 0 ? "text-red-400" : "text-green-400"}`}>
            {unusedFns}
          </span>
          <span className="text-xs text-gray-600">defined, never called</span>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-xs text-gray-500">Clean functions</span>
          <span className="text-2xl font-medium text-green-400">{cleanFns}</span>
          <span className="text-xs text-gray-600">WTF score under 20</span>
        </div>
      </div>

      {/* Detail panels */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <WTFLeaderboard functions={wtf_analysis.top_cursed} />
        <FossilDetector fossils={fossils} />
      </div>

      {/* Function detail table */}
      {wtf_analysis.functions.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-white pb-2 mb-3 border-b border-gray-800">
      All functions
    </h2>
    <div className="flex flex-col gap-2">
      {wtf_analysis.functions.map(fn => (
        <div key={fn.name} className="flex flex-col gap-2 p-3 bg-gray-950 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-gray-200">{fn.name}()</span>
            <span className={`text-xs font-medium ${
              fn.wtf_score >= 70 ? "text-red-400" :
              fn.wtf_score >= 40 ? "text-amber-400" : "text-green-400"
            }`}>
              WTF: {fn.wtf_score}
            </span>
          </div>

          {/* NLP Summary — the new part */}
          {fn.summary && (
            <p className="text-xs text-indigo-300 bg-indigo-950 border border-indigo-900
                          rounded px-3 py-2 italic">
              "{fn.summary}"
            </p>
          )}

          {fn.reasons.length > 0 && (
            <ul className="flex flex-col gap-0.5">
              {fn.reasons.map((r, i) => (
                <li key={i} className="text-xs text-gray-500">· {r}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  </div>
)}
    
    </div>
  )
}