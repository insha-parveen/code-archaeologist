import { useExportPDF } from "../hooks/useExportPDF"

export default function ExportButton({ filename, data }) {
  const { exportPDF, exporting } = useExportPDF()

  const handleExport = () => {
    const pdfName = filename
      ? `code-analysis-${filename.replace(".", "-")}.pdf`
      : "code-analysis.pdf"

    exportPDF(data, pdfName)
  }

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className={`flex items-center gap-2 text-xs font-medium
                  px-3 py-1.5 rounded-lg border transition-all duration-200
                  disabled:opacity-40 disabled:cursor-not-allowed
                  ${exporting
                    ? "bg-green-950 border-green-800 text-green-400"
                    : "bg-gray-900 border-gray-700 text-gray-400 hover:border-green-700 hover:text-green-400"
                  }`}
    >
      {exporting ? (
        <>
          <span className="inline-block w-3 h-3 border-2 border-green-400
                           border-t-transparent rounded-full animate-spin" />
          Generating PDF...
        </>
      ) : (
        <>
          <span>⬇</span>
          Export PDF
        </>
      )}
    </button>
  )
}
