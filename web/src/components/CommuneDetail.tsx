import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { entier, eurosM2 } from '../format'
import { useApi } from '../useApi'

export function CommuneDetail({ code, onClose }: { code: string; onClose: () => void }) {
  const { data, loading, error } = useApi(() => api.commune(code), [code])

  // Une ligne par année, avec une colonne par type de logement
  const annees = [...new Set(data?.historique.map((h) => h.annee) ?? [])].sort()
  const rows = annees.map((annee) => {
    const ligne: Record<string, number> = { annee }
    for (const h of data?.historique.filter((x) => x.annee === annee) ?? []) {
      if (h.nb_ventes >= 10) ligne[h.type_local] = h.prix_m2_median
    }
    return ligne
  })

  return (
    <div className="card chart-card">
      <div className="card-header">
        <h2>{data ? `Historique : ${data.nom_commune}` : 'Historique de la commune'}</h2>
        <button className="link" onClick={onClose} aria-label="Fermer l’historique">
          Fermer ✕
        </button>
      </div>
      {loading && <p className="muted">Chargement…</p>}
      {error && <p className="error">{error}</p>}
      {data && (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="annee" stroke="var(--muted)" fontSize={12} />
            <YAxis tickFormatter={(v: number) => entier(v)} stroke="var(--muted)" fontSize={12} width={56} />
            <Tooltip formatter={(value, name) => [eurosM2(Number(value)), name]} />
            <Legend />
            <Bar dataKey="Appartement" fill="#e34a33" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Maison" fill="#2b8cbe" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
