import { useState } from 'react'
import type { Commune } from '../api'
import { entier, eurosM2, variation } from '../format'

interface Props {
  communes: Commune[]
  selected: string | null
  onSelect: (code: string) => void
}

export function CommuneRanking({ communes, selected, onSelect }: Props) {
  const [ordre, setOrdre] = useState<'cher' | 'abordable'>('cher')
  const rows = [...communes].sort((a, b) =>
    ordre === 'cher' ? b.prix_m2_median - a.prix_m2_median : a.prix_m2_median - b.prix_m2_median,
  )

  return (
    <div className="card ranking">
      <div className="card-header">
        <h2>Classement des communes</h2>
        <div className="segmented small">
          <button className={ordre === 'cher' ? 'active' : ''} onClick={() => setOrdre('cher')}>
            Plus chères
          </button>
          <button className={ordre === 'abordable' ? 'active' : ''} onClick={() => setOrdre('abordable')}>
            Plus abordables
          </button>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Commune</th>
              <th className="num">Prix au m²</th>
              <th className="num">1 an</th>
              <th className="num">Ventes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => {
              const evo = c.evolution_1an
              return (
                <tr
                  key={c.code_commune}
                  className={c.code_commune === selected ? 'selected' : ''}
                  onClick={() => onSelect(c.code_commune)}
                >
                  <td>{c.nom_commune}</td>
                  <td className="num">{eurosM2(c.prix_m2_median)}</td>
                  <td className={`num ${evo === null ? '' : evo >= 0 ? 'up' : 'down'}`}>{variation(evo)}</td>
                  <td className="num">{entier(c.nb_ventes)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="muted small">
        Communes avec au moins 10 ventes dans l’année. Cliquez sur une ligne ou un cercle pour voir l’historique.
      </p>
    </div>
  )
}
