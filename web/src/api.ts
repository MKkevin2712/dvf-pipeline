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

async function get<T>(path: string, params: Record<string, string | number> = {}): Promise<T> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const response = await fetch(`${BASE}/api${path}${query.size ? `?${query}` : ''}`)
  if (!response.ok) throw new Error(`Erreur ${response.status} sur ${path}`)
  return response.json() as Promise<T>
}

export const api = {
  meta: () => get<Meta>('/meta'),
  kpis: (f: Filtres) => get<Kpis>('/kpis', { ...f }),
  communes: (f: Filtres) => get<Commune[]>('/communes', { ...f }),
  evolution: (f: Filtres) => get<PointMensuel[]>('/evolution', { departement: f.departement, type_local: f.type_local }),
  commune: (code: string) => get<CommuneDetail>(`/communes/${code}`),
}
