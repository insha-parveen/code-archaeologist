export default function WTFLeaderboard({ functions }) {
  if (!functions || functions.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-medium text-white mb-3">
          Top cursed functions
        </h2>
        <p className="text-gray-500 text-xs">No functions found.</p>
      </div>
    )
  }

  const getColor = (score) => {
    if (score >= 70) return { bar: "bg-red-500",   text: "text-red-400" }
    if (score >= 40) return { bar: "bg-amber-500", text: "text-amber-400" }
    return               { bar: "bg-green-500",  text: "text-green-400" }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5
                    flex flex-col gap-3">
      <h2 className="text-sm font-medium text-white pb-2 border-b border-gray-800">
        Top cursed functions
      </h2>

      {functions.map((fn, i) => {
        const colors = getColor(fn.wtf_score)
        return (
          <div key={fn.name}
               className="flex items-center gap-3 anim-fade-left"
               style={{ animationDelay: `${400 + i * 100}ms` }}>

            <span className="text-xs text-gray-600 w-4 shrink-0">{i + 1}</span>

            <span className="font-mono text-xs text-gray-200 flex-1 truncate">
              {fn.name}
            </span>

            {/* Animated score bar */}
            <div className="w-20 h-1.5 bg-gray-800 rounded-full shrink-0">
              <div
                className={`h-1.5 rounded-full ${colors.bar}`}
                style={{
                  width: `${fn.wtf_score}%`,
                  animation: `barGrow 0.8s ease both`,
                  animationDelay: `${500 + i * 100}ms`,
                }}
              />
            </div>

            <span className={`text-xs font-medium w-7 text-right
                              shrink-0 ${colors.text}`}>
              {fn.wtf_score}
            </span>
          </div>
        )
      })}
    </div>
  )
}
