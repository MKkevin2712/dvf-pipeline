import { useState } from 'react'
import { api, type Filtres } from './api'
import { CommuneDetail } from './components/CommuneDetail'
import { CommuneRanking } from './components/CommuneRanking'
import { EvolutionChart } from './components/EvolutionChart'
import { Filters } from './components/Filters'
import { KpiCards } from './components/KpiCards'
import { PriceMap } from './components/PriceMap'
import { useApi } from './useApi'

// Par défaut : Hérault, appartements, dernière année complète des données
const DEFAUT: Filtres = { departement: '34', type_local: 'Appartement', annee: 2025 }

export default function App() {
  const meta = useApi(api.meta, [])
  const [filtres, setFiltres] = useState<Filtres>(DEFAUT)
  const [selected, setSelected] = useState<string | null>(null)

  const kpis = useApi(() => api.kpis(filtres), [filtres])
  const communes = useApi(() => api.communes(filtres), [filtres])
  const evolution = useApi(() => api.evolution(filtres), [filtres.departement, filtres.type_local])

  const departement = meta.data?.departements.find((d) => d.code === filtres.departement)?.nom ?? ''
  const typeLabel = filtres.type_local === 'Appartement' ? 'appartements' : 'maisons'

  const changeFiltres = (f: Filtres) => {
    if (f.departement !== filtres.departement) setSelected(null)
    setFiltres(f)
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>Prix de l’immobilier en France</h1>
          <p className="muted">
            Ventes de logements 2021–2025 · données publiques DVF, nettoyées par un pipeline Airflow + dbt
          </p>
        </div>
        {meta.data && <Filters meta={meta.data} filtres={filtres} onChange={changeFiltres} />}
      </header>

      {meta.error && (
        <p className="error">
          Impossible de joindre l’API ({meta.error}). Lancez-la avec : <code>uv run uvicorn dvf_pipeline.api:app</code>
        </p>
      )}

      <KpiCards kpis={kpis.data} />

      <section className="grid">
        <PriceMap communes={communes.data ?? []} selected={selected} onSelect={setSelected} />
        <CommuneRanking communes={communes.data ?? []} selected={selected} onSelect={setSelected} />
      </section>

      <section className="grid">
        <EvolutionChart
          points={evolution.data ?? []}
          titre={`Évolution mensuelle du prix au m² : ${typeLabel}, ${departement}`}
        />
        {selected ? (
          <CommuneDetail code={selected} onClose={() => setSelected(null)} />
        ) : (
          <div className="card chart-card placeholder">
            <p className="muted">Sélectionnez une commune sur la carte ou dans le classement pour voir son historique.</p>
          </div>
        )}
      </section>

      <footer className="footer muted">
        <p>
          Méthode : une vente n’est retenue que si elle porte sur un seul logement (le prix d’une vente groupée ne peut
          pas être réparti), avec un prix au m² entre 500 et 30 000 €. Les prix sont des médianes, plus robustes que
          les moyennes aux ventes atypiques.
        </p>
        <p>
          Source : Demandes de valeurs foncières géolocalisées (Etalab, data.gouv.fr) ·{' '}
          <a href="https://github.com/MKkevin2712/dvf-pipeline">Code source</a> · Kevin Moukam Nkameni
        </p>
      </footer>
    </div>
  )
}
