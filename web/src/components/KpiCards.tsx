import type { Kpis } from '../api'
import { entier, euros, eurosM2, variation } from '../format'

export function KpiCards({ kpis }: { kpis: Kpis | null }) {
  const evo = kpis?.evolution_prix_m2_1an ?? null
  const cards = [
    { label: 'Prix médian au m²', value: kpis ? eurosM2(kpis.prix_m2_median) : '…', tone: '' },
    {
      label: 'Évolution sur un an',
      value: kpis ? variation(evo) : '…',
      tone: evo === null ? '' : evo >= 0 ? 'up' : 'down',
    },
    { label: 'Ventes analysées', value: kpis ? entier(kpis.nb_ventes) : '…', tone: '' },
    { label: 'Prix médian', value: kpis ? euros(kpis.prix_median) : '…', tone: '' },
    { label: 'Surface médiane', value: kpis ? `${entier(kpis.surface_mediane)} m²` : '…', tone: '' },
  ]
  return (
    <div className="kpis">
      {cards.map((c) => (
        <div key={c.label} className="card kpi">
          <span className="kpi-label">{c.label}</span>
          <span className={`kpi-value ${c.tone}`}>{c.value}</span>
        </div>
      ))}
    </div>
  )
}
