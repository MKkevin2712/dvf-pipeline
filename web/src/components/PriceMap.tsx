import 'leaflet/dist/leaflet.css'
import { useEffect, useMemo } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet'
import type { Commune } from '../api'
import { entier, eurosM2, variation } from '../format'

// Palette séquentielle, du moins cher au plus cher (lisible par les personnes daltoniennes)
const COLORS = ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000']

/** Seuils des quintiles : chaque couleur regroupe 20 % des communes. */
function quantileBreaks(values: number[]): number[] {
  const sorted = [...values].sort((a, b) => a - b)
  return [0.2, 0.4, 0.6, 0.8].map((q) => sorted[Math.floor(q * (sorted.length - 1))] ?? 0)
}

function FitBounds({ communes }: { communes: Commune[] }) {
  const map = useMap()
  useEffect(() => {
    if (communes.length) {
      map.fitBounds(
        communes.map((c) => [c.latitude, c.longitude] as [number, number]),
        { padding: [24, 24] },
      )
    }
  }, [communes, map])
  return null
}

interface Props {
  communes: Commune[]
  selected: string | null
  onSelect: (code: string) => void
}

export function PriceMap({ communes, selected, onSelect }: Props) {
  const breaks = useMemo(() => quantileBreaks(communes.map((c) => c.prix_m2_median)), [communes])
  const color = (v: number) => COLORS[breaks.filter((b) => v > b).length]
  const maxVentes = Math.max(1, ...communes.map((c) => c.nb_ventes))
  const legend = [
    `< ${entier(breaks[0])}`,
    `${entier(breaks[0])} – ${entier(breaks[1])}`,
    `${entier(breaks[1])} – ${entier(breaks[2])}`,
    `${entier(breaks[2])} – ${entier(breaks[3])}`,
    `> ${entier(breaks[3])}`,
  ]

  return (
    <div className="card map-card">
      <h2>Prix au m² par commune</h2>
      <MapContainer center={[46.6, 2.5]} zoom={6} scrollWheelZoom className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds communes={communes} />
        {communes.map((c) => {
          const isSelected = c.code_commune === selected
          return (
            <CircleMarker
              key={c.code_commune}
              center={[c.latitude, c.longitude]}
              radius={5 + 14 * Math.sqrt(c.nb_ventes / maxVentes)}
              pathOptions={{
                color: isSelected ? '#111827' : '#7a3b2e',
                weight: isSelected ? 3 : 1,
                fillColor: color(c.prix_m2_median),
                fillOpacity: 0.85,
              }}
              eventHandlers={{ click: () => onSelect(c.code_commune) }}
            >
              <Tooltip>
                <strong>{c.nom_commune}</strong>
                <br />
                {eurosM2(c.prix_m2_median)} · {entier(c.nb_ventes)} ventes
                <br />
                Sur un an : {variation(c.evolution_1an)}
              </Tooltip>
            </CircleMarker>
          )
        })}
      </MapContainer>
      <div className="legend" aria-label="Légende des couleurs (€/m²)">
        {COLORS.map((col, i) => (
          <span key={col}>
            <i style={{ background: col }} />
            {legend[i]}
          </span>
        ))}
        <span className="muted">€/m² · taille du cercle = nombre de ventes</span>
      </div>
    </div>
  )
}
