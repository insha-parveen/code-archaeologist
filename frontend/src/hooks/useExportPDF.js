import jsPDF from "jspdf"
import { useState } from "react"

export function useExportPDF() {
  const [exporting, setExporting] = useState(false)

  const exportPDF = async (data, filename = "code-analysis.pdf") => {
    setExporting(true)

    try {
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      })

      const pageWidth  = 210
      const pageHeight = 297
      const margin     = 16
      const contentWidth = pageWidth - margin * 2
      let y = margin  // current Y position on page

      // ── Helpers ──────────────────────────────────────────────

      const newPageIfNeeded = (neededHeight = 10) => {
        if (y + neededHeight > pageHeight - margin) {
          pdf.addPage()
          y = margin
        }
      }

      const drawLine = () => {
        pdf.setDrawColor(55, 55, 65)
        pdf.line(margin, y, pageWidth - margin, y)
        y += 4
      }

      const writeText = (text, size, hex, bold = false, maxWidth = contentWidth) => {
        pdf.setFontSize(size)
        pdf.setTextColor(hex)
        pdf.setFont("helvetica", bold ? "bold" : "normal")
        const lines = pdf.splitTextToSize(String(text), maxWidth)
        newPageIfNeeded(lines.length * (size * 0.4))
        pdf.text(lines, margin, y)
        y += lines.length * (size * 0.4) + 1
      }

      const writeLabel = (label, value, labelHex, valueHex) => {
        pdf.setFontSize(8)
        pdf.setFont("helvetica", "normal")
        pdf.setTextColor(labelHex)
        pdf.text(label, margin, y)
        pdf.setTextColor(valueHex)
        pdf.text(String(value), margin + 40, y)
        y += 5
      }

      const drawScoreBar = (score) => {
        const barX      = margin
        const barY      = y
        const barW      = contentWidth
        const barH      = 3
        const fillW     = (score / 100) * barW

        // Background
        pdf.setFillColor(40, 40, 50)
        pdf.roundedRect(barX, barY, barW, barH, 1, 1, "F")

        // Fill
        if (score >= 70)      pdf.setFillColor(239, 68, 68)
        else if (score >= 40) pdf.setFillColor(245, 158, 11)
        else                  pdf.setFillColor(34, 197, 94)

        if (fillW > 0) pdf.roundedRect(barX, barY, fillW, barH, 1, 1, "F")
        y += barH + 3
      }

      // ── Page 1 — Header ───────────────────────────────────────

      // Dark background
      pdf.setFillColor(3, 7, 18)
      pdf.rect(0, 0, pageWidth, pageHeight, "F")

      // Title
      writeText("Code Archaeologist", 22, "#ffffff", true)
      writeText("Analysis Report", 11, "#6366f1")
      y += 2

      // File info
      writeText(
        `${data.filename}  ·  ${data.line_count} lines`,
        9, "#6b7280"
      )
      y += 4
      drawLine()

      // ── Summary Cards ─────────────────────────────────────────

      writeText("Summary", 13, "#ffffff", true)
      y += 2

      const avg    = data.wtf_analysis.average_wtf
      const avgHex = avg >= 70 ? "#f87171" : avg >= 40 ? "#fbbf24" : "#4ade80"

      writeLabel("Avg WTF Score",       avg,                            "#9ca3af", avgHex)
      writeLabel("Total Fossils",       data.fossils.total_fossils,     "#9ca3af", "#fbbf24")
      writeLabel("Unused Functions",    data.fossils.unused_functions.length, "#9ca3af", "#f87171")
      writeLabel("Total Functions",     data.wtf_analysis.total_functions,   "#9ca3af", "#ffffff")
      y += 2
      drawLine()

      // ── Code Story ────────────────────────────────────────────

      if (data.story?.narrative) {
        writeText("Code Story", 13, "#ffffff", true)
        y += 2

        if (data.story.development_style) {
          writeText(
            `Development style: ${data.story.development_style}`,
            8, "#818cf8"
          )
          y += 1
        }

        writeText(data.story.narrative, 8, "#d1d5db")
        y += 2
        drawLine()
      }

      // ── Top Cursed Functions ──────────────────────────────────

      if (data.wtf_analysis.top_cursed?.length > 0) {
        writeText("Top Cursed Functions", 13, "#ffffff", true)
        y += 2

        data.wtf_analysis.top_cursed.forEach((fn, i) => {
          newPageIfNeeded(20)

          const scoreHex = fn.wtf_score >= 70
            ? "#f87171" : fn.wtf_score >= 40 ? "#fbbf24" : "#4ade80"

          // Rank + name + score
          pdf.setFontSize(9)
          pdf.setFont("helvetica", "bold")
          pdf.setTextColor("#ffffff")
          pdf.text(`${i + 1}.  ${fn.name}()`, margin, y)

          pdf.setTextColor(scoreHex)
          pdf.text(`WTF: ${fn.wtf_score}`, pageWidth - margin - 20, y)
          y += 5

          drawScoreBar(fn.wtf_score)

          // Summary
          if (fn.summary) {
            writeText(`"${fn.summary}"`, 7.5, "#a5b4fc")
          }

          y += 1
        })

        drawLine()
      }

      // ── Fossils ───────────────────────────────────────────────

      const allFossils = [
        ...data.fossils.unused_functions.map(f => ({ ...f, kind: "Unused function" })),
        ...data.fossils.unused_variables.map(f => ({ ...f, kind: "Unused variable" })),
        ...data.fossils.commented_code_blocks.map(f => ({ ...f, kind: "Commented code" })),
      ]

      if (allFossils.length > 0) {
        writeText("Fossils Detected", 13, "#ffffff", true)
        y += 2

        allFossils.forEach(f => {
          newPageIfNeeded(8)
          const label = f.name || f.content || ""
          writeText(
            `· ${f.kind}  —  ${label}  (line ${f.line})`,
            8, "#9ca3af"
          )
        })

        y += 2
        drawLine()
      }

      // ── All Functions ─────────────────────────────────────────

      if (data.wtf_analysis.functions?.length > 0) {
        writeText("All Functions", 13, "#ffffff", true)
        y += 2

        data.wtf_analysis.functions.forEach(fn => {
          newPageIfNeeded(30)

          // Dark background box
          const boxHeight = fn.refactoring ? 28 : 20
          pdf.setFillColor(15, 15, 25)
          pdf.roundedRect(margin, y, contentWidth, boxHeight, 2, 2, "F")

          const innerY = y + 4
          y = innerY

          // Name + score
          const scoreHex = fn.wtf_score >= 70
            ? "#f87171" : fn.wtf_score >= 40 ? "#fbbf24" : "#4ade80"

          pdf.setFontSize(9)
          pdf.setFont("helvetica", "bold")
          pdf.setTextColor("#e5e7eb")
          pdf.text(`${fn.name}()`, margin + 3, y)
          pdf.setTextColor(scoreHex)
          pdf.text(`WTF: ${fn.wtf_score}`, pageWidth - margin - 20, y)
          y += 5

          // Summary
          if (fn.summary) {
            writeText(`"${fn.summary}"`, 7.5, "#a5b4fc")
          }

          // Refactoring
          if (fn.refactoring) {
            writeText(`💡 ${fn.refactoring}`, 7.5, "#fcd34d")
          }

          y += 4
        })
      }

      // ── Footer on every page ──────────────────────────────────

      const totalPages = pdf.getNumberOfPages()
      for (let i = 1; i <= totalPages; i++) {
        pdf.setPage(i)
        pdf.setFillColor(3, 7, 18)
        pdf.rect(0, 0, pageWidth, pageHeight, "F")  // re-apply bg
        pdf.setFontSize(7)
        pdf.setTextColor("#374151")
        pdf.text(
          `Code Archaeologist  ·  Page ${i} of ${totalPages}`,
          margin, pageHeight - 6
        )
      }

      pdf.save(filename)
      console.log("PDF exported:", filename)

    } catch (err) {
      console.error("PDF export failed:", err)
      alert(`PDF export failed: ${err.message}`)
    } finally {
      setExporting(false)
    }
  }

  return { exportPDF, exporting }
}
