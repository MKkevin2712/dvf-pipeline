// Accès à l'API FastAPI (dvf_pipeline.api) et types des données renvoyées.

export type TypeLocal = 'Appartement' | 'Maison'

export interface Meta {
  annees: number[]
  departements: { code: string; nom: string }[]
  types_local: TypeLocal[]
}

export interface Kpis {
  annee: number
  nb_ventes: number
  prix_m2_median: number
  prix_median: number
  surface_mediane: number
  evolution_prix_m2_1an: number | null
}

export interface Commune {
  code_commune: string
  nom_commune: string
  latitude: number
  longitude: number
  nb_ventes: number
  prix_m2_median: number
  prix_m2_q1: number
  prix_m2_q3: number
  prix_median: number
  surface_mediane: number
  evolution_1an: number | null
}

export interface PointMensuel {
  mois: string
  nb_ventes: number
  prix_m2_median: number
}

export interface CommuneDetail {
  code_commune: string
  nom_commune: string
  code_departement: string
  historique: { annee: number; type_local: TypeLocal; nb_ventes: number; prix_m2_median: number }[]
}

export interface Filtres {
  departement: string
  type_local: TypeLocal
  annee: number
}

const BASE = import.meta.env.VITE_API_URL ?? ''
// Version publiée en ligne (GitHub Pages) : pas de serveur, l'interface lit des fichiers JSON
// exportés par dvf_pipeline.export_static (mêmes réponses que l'API).
const STATIC = import.meta.env.VITE_STATIC === '1'

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Erreur ${response.status} sur ${url}`)
  return response.json() as Promise<T>
}

function get<T>(path: string, params: Record<string, string | number> = {}): Promise<T> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  return fetchJson<T>(`${BASE}/api${path}${query.size ? `?${query}` : ''}`)
}

const file = <T>(name: string) => fetchJson<T>(`${import.meta.env.BASE_URL}data/${name}.json`)

export const api = STATIC
  ? {
      meta: () => file<Meta>('meta'),
      kpis: (f: Filtres) => file<Kpis>(`kpis_${f.departement}_${f.type_local}_${f.annee}`),
      communes: (f: Filtres) => file<Commune[]>(`communes_${f.departement}_${f.type_local}_${f.annee}`),
      evolution: (f: Filtres) => file<PointMensuel[]>(`evolution_${f.departement}_${f.type_local}`),
      commune: (code: string) => file<CommuneDetail>(`commune_${code}`),
    }
  : {
      meta: () => get<Meta>('/meta'),
      kpis: (f: Filtres) => get<Kpis>('/kpis', { ...f }),
      communes: (f: Filtres) => get<Commune[]>('/communes', { ...f }),
      evolution: (f: Filtres) =>
        get<PointMensuel[]>('/evolution', { departement: f.departement, type_local: f.type_local }),
      commune: (code: string) => get<CommuneDetail>(`/communes/${code}`),
    }
