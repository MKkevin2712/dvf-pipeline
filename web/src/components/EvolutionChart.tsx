import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { PointMensuel } from '../api'
import { entier, eurosM2, moisCourt } from '../format'

/** Moyenne glissante sur 3 mois : lisse les variations dues aux mois avec peu de ventes. */
function rolling(points: PointMensuel[], window = 3) {
  return points.map((p, i) => {
    const slice = points.slice(Math.max(0, i - window + 1), i + 1)
    const lisse = slice.reduce((s, x) => s + x.prix_m2_median, 0) / slice.length
    return { ...p, lisse: i >= window - 1 ? lisse : null }
  })
}

export function EvolutionChart({ points, titre }: { points: PointMensuel[]; titre: string }) {
  const data = rolling(points)
  return (
    <div className="card chart-card">
      <h2>{titre}</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="mois" tickFormatter={moisCourt} minTickGap={32} stroke="var(--muted)" fontSize={12} />
          <YAxis
            tickFormatter={(v: number) => entier(v)}
            domain={['auto', 'auto']}
            stroke="var(--muted)"
            fontSize={12}
            width={56}
          />
          <Tooltip
            formatter={(value, name) => [eurosM2(Number(value)), name]}
            labelFormatter={(label) =>
              new Date(String(label)).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
            }
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="prix_m2_median"
            name="Médiane du mois"
            stroke="#fdbb84"
            strokeWidth={1.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="lisse"
            name="Moyenne glissante 3 mois"
            stroke="#d7301f"
            strokeWidth={2.5}
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
