import { useEffect, useState } from 'react'

// Transición de entrada: un planeta (océano azul + continentes verdes + nubes que giran)
// que hace zoom y funde, revelando el mapa de Cali. Se reproduce 1 vez por sesión.
export default function PlanetIntro({ onDone }: { onDone: () => void }) {
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setLeaving(true), 1900)
    return () => clearTimeout(t)
  }, [])

  return (
    <div
      className={`planet-intro ${leaving ? 'is-leaving' : ''}`}
      onAnimationEnd={(e) => { if (e.animationName === 'intro-fade') onDone() }}
    >
      <div className="planet-stage">
        <svg viewBox="0 0 200 200" width="260" height="260" role="img" aria-label="Planeta Tierra">
          <defs>
            <radialGradient id="ocean" cx="38%" cy="32%" r="78%">
              <stop offset="0%" stopColor="#7dd3fc" />
              <stop offset="42%" stopColor="#0ea5e9" />
              <stop offset="80%" stopColor="#0369a1" />
              <stop offset="100%" stopColor="#0b3b66" />
            </radialGradient>
            <clipPath id="globe"><circle cx="100" cy="100" r="92" /></clipPath>
          </defs>

          <circle cx="100" cy="100" r="92" fill="url(#ocean)" />

          {/* Continentes (verde) */}
          <g clipPath="url(#globe)" fill="#22c55e">
            <path d="M52 58 q22 -14 40 -2 q14 9 3 24 q-15 17 -36 8 q-17 -9 -7 -30Z" opacity="0.92" />
            <path d="M118 92 q24 -7 32 11 q7 19 -15 28 q-23 6 -30 -13 q-4 -19 13 -26Z" opacity="0.9" />
            <path d="M68 122 q17 -5 26 11 q5 17 -13 23 q-19 5 -23 -13 q-3 -15 10 -21Z" opacity="0.85" />
            <ellipse cx="152" cy="58" rx="14" ry="9" opacity="0.8" />
          </g>

          {/* Nubes que giran */}
          <g clipPath="url(#globe)" className="planet-clouds" fill="#ffffff">
            <ellipse cx="58" cy="48" rx="26" ry="9" opacity="0.45" />
            <ellipse cx="132" cy="74" rx="30" ry="10" opacity="0.4" />
            <ellipse cx="95" cy="136" rx="34" ry="11" opacity="0.38" />
            <ellipse cx="40" cy="110" rx="20" ry="8" opacity="0.35" />
          </g>

          {/* Brillo y borde */}
          <ellipse cx="72" cy="62" rx="30" ry="20" fill="#ffffff" opacity="0.12" />
          <circle cx="100" cy="100" r="92" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="1.5" />
        </svg>
        <p className="planet-title">GeoVision-CLIP</p>
        <p className="planet-sub">Enfocando Cali…</p>
      </div>
      <button className="planet-skip" onClick={onDone}>Saltar</button>
    </div>
  )
}
