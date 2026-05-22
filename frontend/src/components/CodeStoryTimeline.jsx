export default function CodeStoryTimeline({ story }) {
  if (!story) return null

  const severityStyles = {
    high:     "border-red-800 bg-red-950",
    medium:   "border-amber-800 bg-amber-950",
    low:      "border-gray-700 bg-gray-900",
    positive: "border-green-800 bg-green-950",
  }

  const severityDot = {
    high:     "bg-red-500",
    medium:   "bg-amber-500",
    low:      "bg-gray-500",
    positive: "bg-green-500",
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5
                    flex flex-col gap-4">

      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-gray-800">
        <h2 className="text-sm font-medium text-white">Code Story</h2>
        <span className="text-xs px-2 py-0.5 rounded bg-indigo-950
                         border border-indigo-800 text-indigo-300
                         anim-fade-in delay-200">
          {story.development_style}
        </span>
      </div>

      {/* Narrative */}
      <p className="text-xs text-gray-400 leading-relaxed italic anim-fade-in delay-300">
        {story.narrative}
      </p>

      {/* Timeline */}
      <div className="flex flex-col gap-3 relative">
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gray-800" />

        {story.chapters.map((chapter, i) => (
          <div key={i}
               className="flex gap-4 items-start pl-1 anim-fade-left"
               style={{ animationDelay: `${500 + i * 150}ms` }}>

            {/* Animated dot */}
            <div className={`w-3.5 h-3.5 rounded-full shrink-0 mt-0.5 z-10
                            border-2 border-gray-950 ${severityDot[chapter.severity]}
                            transition-transform duration-200 hover:scale-125`}
            />

            {/* Chapter card */}
            <div className={`flex-1 rounded-lg border p-3 flex flex-col gap-2
                            ${severityStyles[chapter.severity]}
                            hover:brightness-110 transition-all duration-200`}>
              <div className="flex items-center gap-2">
                <span className="text-base">{chapter.icon}</span>
                <span className="text-xs font-medium text-white">
                  {chapter.title}
                </span>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed">
                {chapter.description}
              </p>

              {chapter.evidence.length > 0 && (
                <ul className="flex flex-col gap-1">
                  {chapter.evidence.map((e, j) => (
                    <li key={j} className="text-xs text-gray-500 flex gap-1.5">
                      <span className="text-gray-600 shrink-0">·</span>
                      {e}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
