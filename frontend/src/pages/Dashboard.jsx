import { useEffect, useState } from "react"
import CodeStoryTimeline from "../components/CodeStoryTimeline"
import ExportButton from "../components/ExportButton"
import FossilDetector from "../components/FossilDetector"
import GalaxyBackground from "../components/GalaxyBackground"
import WTFLeaderboard from "../components/WTFLeaderboard"

// Animated number that counts up from 0
function CountUp({ value }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    let start = 0
    const end = parseFloat(value)
    if (start === end) return
    const duration = 800
    const stepTime = 16
    const steps = duration / stepTime
    const increment = end / steps
    const timer = setInterval(() => {
      start += increment
      if (start >= end) {
        setDisplay(end)
        clearInterval(timer)
      } else {
        setDisplay(Math.floor(start))
      }
    }, stepTime)
    return () => clearInterval(timer)
  }, [value])

  return <span>{display}</span>
}

export default function Dashboard({ data, onReset }) {
  const { filename, line_count, fossils, wtf_analysis } = data

  const avgScore     = wtf_analysis.average_wtf
  const totalFossils = fossils.total_fossils
  const unusedFns    = fossils.unused_functions.length
  const cleanFns     = wtf_analysis.functions.filter(f => f.wtf_score < 20).length

  const scoreColor = avgScore >= 70
    ? "text-red-400"
    : avgScore >= 40
    ? "text-amber-400"
    : "text-green-400"

  return (
    <div style={{ position: "relative", minHeight: "100vh",
                  background: "#030712", overflow: "hidden" }}>

      <GalaxyBackground />

      {/* ← id added here so html2canvas knows what to capture */}
      <div id="dashboard-content"
           style={{ position: "relative", zIndex: 1 }}
           className="min-h-screen p-6 flex flex-col gap-5 max-w-4xl mx-auto">

        {/* Top bar */}
        <div className="flex items-center justify-between anim-fade-down">
          <div className="flex flex-col gap-0.5">
            <h1 className="text-white font-medium text-lg">
              🕵️ Code Archaeologist
            </h1>
            <p className="text-gray-500 text-xs">
              {filename} · {line_count} lines
            </p>
          </div>

          {/* ← Action buttons — ExportButton added here */}
          <div className="flex items-center gap-2">
            <ExportButton filename={filename} data={data} />
            <button
              onClick={onReset}
              className="text-xs text-gray-400 border border-gray-700
                         hover:border-gray-500 hover:text-white
                         px-3 py-1.5 rounded-lg transition-all duration-200
                         hover:scale-[1.03] active:scale-[0.97]"
            >
              Upload another
            </button>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: "Avg WTF score",
              value: avgScore,
              color: scoreColor,
              sub: `${wtf_analysis.total_functions} functions`,
              delay: "delay-100"
            },
            {
              label: "Total fossils",
              value: totalFossils,
              color: totalFossils > 0 ? "text-amber-400" : "text-green-400",
              sub: "dead code artifacts",
              delay: "delay-200"
            },
            {
              label: "Unused functions",
              value: unusedFns,
              color: unusedFns > 0 ? "text-red-400" : "text-green-400",
              sub: "defined, never called",
              delay: "delay-300"
            },
            {
              label: "Clean functions",
              value: cleanFns,
              color: "text-green-400",
              sub: "WTF score under 20",
              delay: "delay-400"
            },
          ].map((card) => (
            <div key={card.label}
                 className={`bg-gray-900 bg-opacity-80 rounded-xl p-4
                             flex flex-col gap-1 anim-fade-up ${card.delay}
                             hover:border hover:border-gray-700
                             transition-all duration-200`}
                 style={{ backdropFilter: "blur(10px)" }}>
              <span className="text-xs text-gray-500">{card.label}</span>
              <span className={`text-2xl font-medium ${card.color}`}>
                <CountUp value={card.value} />
              </span>
              <span className="text-xs text-gray-600">{card.sub}</span>
            </div>
          ))}
        </div>

        {/* Detail panels */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="anim-fade-up delay-300">
            <WTFLeaderboard functions={wtf_analysis.top_cursed} />
          </div>
          <div className="anim-fade-up delay-400">
            <FossilDetector fossils={fossils} />
          </div>
        </div>

        {/* Code Story Timeline */}
        {data.story && (
          <div className="anim-fade-up delay-500">
            <CodeStoryTimeline story={data.story} />
          </div>
        )}

        {/* All functions — with LLM summaries and refactoring suggestions */}
        {wtf_analysis.functions.length > 0 && (
          <div className="bg-gray-900 bg-opacity-80 border border-gray-800
                          rounded-xl p-5 anim-fade-up delay-600"
               style={{ backdropFilter: "blur(10px)" }}>
            <h2 className="text-sm font-medium text-white pb-2 mb-3
                           border-b border-gray-800">
              All functions
            </h2>
            <div className="flex flex-col gap-2">
              {wtf_analysis.functions.map((fn, i) => (
                <div key={fn.name}
                     className="flex flex-col gap-2 p-3 bg-gray-950 rounded-lg
                                anim-fade-left hover:bg-gray-900
                                transition-colors duration-200"
                     style={{ animationDelay: `${600 + i * 80}ms` }}>

                  {/* Function name + WTF score */}
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-gray-200">
                      {fn.name}()
                    </span>
                    <span className={`text-xs font-medium ${
                      fn.wtf_score >= 70 ? "text-red-400" :
                      fn.wtf_score >= 40 ? "text-amber-400" : "text-green-400"
                    }`}>
                      WTF: {fn.wtf_score}
                    </span>
                  </div>

                  {/* LLM Intent Summary */}
                  {fn.summary && (
                    <p className="text-xs text-indigo-300 bg-indigo-950
                                  border border-indigo-900 rounded px-3 py-2 italic">
                      "{fn.summary}"
                    </p>
                  )}

                  {/* LLM Refactoring Suggestion — only appears for high WTF */}
                  {fn.refactoring && (
                    <div className="flex gap-2 bg-amber-950 border border-amber-900
                                    rounded px-3 py-2">
                      <span className="text-amber-400 shrink-0 text-sm">💡</span>
                      <p className="text-xs text-amber-300 leading-relaxed">
                        {fn.refactoring}
                      </p>
                    </div>
                  )}

                  {/* WTF reasons */}
                  {fn.reasons.length > 0 && (
                    <ul className="flex flex-col gap-0.5">
                      {fn.reasons.map((r, j) => (
                        <li key={j} className="text-xs text-gray-500">· {r}</li>
                      ))}
                    </ul>
                  )}

                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
