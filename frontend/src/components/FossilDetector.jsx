export default function FossilDetector({ fossils }) {
  const all = [
    ...fossils.unused_functions.map(f => ({ ...f, kind: "unused_fn" })),
    ...fossils.unused_variables.map(f => ({ ...f, kind: "unused_var" })),
    ...fossils.commented_code_blocks.map(f => ({ ...f, kind: "comment" })),
  ].sort((a, b) => a.line - b.line)

  const tagStyle = {
    unused_fn:  "bg-red-950 text-red-400 border border-red-900",
    unused_var: "bg-amber-950 text-amber-400 border border-amber-900",
    comment:    "bg-gray-800 text-gray-400 border border-gray-700",
  }

  const tagLabel = {
    unused_fn:  "unused fn",
    unused_var: "unused var",
    comment:    "dead comment",
  }

  const icon = {
    unused_fn:  "👻",
    unused_var: "📦",
    comment:    "💬",
  }

  if (all.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-medium text-white mb-3">
          Fossils detected
        </h2>
        <p className="text-green-400 text-xs">No dead code found. Clean file!</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5
                    flex flex-col gap-3">
      <h2 className="text-sm font-medium text-white pb-2 border-b border-gray-800">
        Fossils detected
      </h2>

      {all.map((item, i) => (
        <div key={i}
             className="flex items-start gap-3 pb-2 border-b border-gray-800
                        last:border-0 last:pb-0 anim-fade-left
                        hover:bg-gray-800 rounded-lg px-1
                        transition-colors duration-200"
             style={{ animationDelay: `${400 + i * 100}ms` }}>

          <span className="text-base shrink-0 mt-0.5">{icon[item.kind]}</span>

          <div className="flex flex-col gap-0.5 flex-1 min-w-0">
            <span className="font-mono text-xs text-gray-200 truncate">
              {item.name || item.content}
            </span>
            <span className="text-xs text-gray-500">line {item.line}</span>
          </div>

          <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${tagStyle[item.kind]}`}>
            {tagLabel[item.kind]}
          </span>
        </div>
      ))}
    </div>
  )
}
