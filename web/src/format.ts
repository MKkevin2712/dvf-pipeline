const nombre = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
const pourcent = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 1, signDisplay: 'exceptZero' })

export const euros = (v: number) => `${nombre.format(v)} €`
export const eurosM2 = (v: number) => `${nombre.format(v)} €/m²`
export const entier = (v: number) => nombre.format(v)
export const variation = (v: number | null) => (v === null ? '—' : pourcent.format(v))
export const moisCourt = (iso: string) =>
  new Date(iso).toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' })
