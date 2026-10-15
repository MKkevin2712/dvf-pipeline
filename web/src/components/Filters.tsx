import type { Filtres, Meta } from '../api'

interface Props {
  meta: Meta
  filtres: Filtres
  onChange: (f: Filtres) => void
}

export function Filters({ meta, filtres, onChange }: Props) {
  return (
    <div className="filters">
      <label>
        Département
        <select value={filtres.departement} onChange={(e) => onChange({ ...filtres, departement: e.target.value })}>
          {meta.departements.map((d) => (
            <option key={d.code} value={d.code}>
              {d.nom} ({d.code})
            </option>
          ))}
        </select>
      </label>

      <div className="segmented" role="radiogroup" aria-label="Type de logement">
        {meta.types_local.map((t) => (
          <button
            key={t}
            role="radio"
            aria-checked={filtres.type_local === t}
            className={filtres.type_local === t ? 'active' : ''}
            onClick={() => onChange({ ...filtres, type_local: t })}
          >
            {t === 'Appartement' ? 'Appartements' : 'Maisons'}
          </button>
        ))}
      </div>

      <label>
        Année
        <select value={filtres.annee} onChange={(e) => onChange({ ...filtres, annee: Number(e.target.value) })}>
          {meta.annees.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
