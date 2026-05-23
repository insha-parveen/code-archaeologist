import { useEffect, useRef } from "react"

export default function GalaxyBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    let animationId

    const resize = () => {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener("resize", resize)

    // --- Star field ---
    const STAR_COUNT = 180
    const stars = Array.from({ length: STAR_COUNT }, () => ({
      x:       Math.random() * window.innerWidth,
      y:       Math.random() * window.innerHeight,
      r:       Math.random() * 1.4 + 0.2,
      speed:   Math.random() * 0.15 + 0.02,
      opacity: Math.random() * 0.7 + 0.2,
      twinkle: Math.random() * Math.PI * 2,
      twinkleSpeed: Math.random() * 0.02 + 0.005,
    }))

    // --- Nebula particles (larger, drifting blobs) ---
    const NEBULA_COUNT = 28
    const nebula = Array.from({ length: NEBULA_COUNT }, () => ({
      x:     Math.random() * window.innerWidth,
      y:     Math.random() * window.innerHeight,
      r:     Math.random() * 120 + 40,
      dx:    (Math.random() - 0.5) * 0.12,
      dy:    (Math.random() - 0.5) * 0.12,
      hue:   Math.random() < 0.5
               ? Math.floor(Math.random() * 40 + 240)  // purple/blue
               : Math.floor(Math.random() * 30 + 280), // violet/indigo
      alpha: Math.random() * 0.045 + 0.01,
    }))

    // --- Shooting stars ---
    const shooters = []
    const spawnShooter = () => {
      shooters.push({
        x:       Math.random() * window.innerWidth,
        y:       Math.random() * window.innerHeight * 0.5,
        len:     Math.random() * 120 + 60,
        speed:   Math.random() * 6 + 4,
        angle:   Math.PI / 5,
        opacity: 1,
        life:    0,
        maxLife: Math.random() * 40 + 30,
      })
    }
    let shooterTimer = 0

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Nebula blobs
      nebula.forEach(n => {
        n.x += n.dx
        n.y += n.dy
        if (n.x < -n.r) n.x = canvas.width + n.r
        if (n.x > canvas.width + n.r) n.x = -n.r
        if (n.y < -n.r) n.y = canvas.height + n.r
        if (n.y > canvas.height + n.r) n.y = -n.r

        const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r)
        g.addColorStop(0, `hsla(${n.hue}, 80%, 60%, ${n.alpha})`)
        g.addColorStop(1, `hsla(${n.hue}, 80%, 60%, 0)`)
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fillStyle = g
        ctx.fill()
      })

      // Stars
      stars.forEach(s => {
        s.y += s.speed
        s.twinkle += s.twinkleSpeed
        if (s.y > canvas.height) {
          s.y = 0
          s.x = Math.random() * canvas.width
        }
        const alpha = s.opacity * (0.6 + 0.4 * Math.sin(s.twinkle))
        ctx.beginPath()
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`
        ctx.fill()
      })

      // Shooting stars
      shooterTimer++
      if (shooterTimer > 90) {
        spawnShooter()
        shooterTimer = 0
      }

      for (let i = shooters.length - 1; i >= 0; i--) {
        const s = shooters[i]
        s.life++
        s.x += Math.cos(s.angle) * s.speed
        s.y += Math.sin(s.angle) * s.speed
        s.opacity = 1 - s.life / s.maxLife

        if (s.life >= s.maxLife) {
          shooters.splice(i, 1)
          continue
        }

        const tail = {
          x: s.x - Math.cos(s.angle) * s.len,
          y: s.y - Math.sin(s.angle) * s.len,
        }
        const grad = ctx.createLinearGradient(tail.x, tail.y, s.x, s.y)
        grad.addColorStop(0, `rgba(255,255,255,0)`)
        grad.addColorStop(1, `rgba(255,255,255,${s.opacity * 0.9})`)

        ctx.beginPath()
        ctx.moveTo(tail.x, tail.y)
        ctx.lineTo(s.x, s.y)
        ctx.strokeStyle = grad
        ctx.lineWidth   = 1.5
        ctx.stroke()
      }

      animationId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener("resize", resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 0,
        pointerEvents: "none",
      }}
    />
  )
}
