import { useEffect, useState } from 'react'

/** Charge une donnée de l'API et la recharge quand les dépendances changent. */
export function useApi<T>(load: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // oxlint-disable-next-line react-hooks/exhaustive-deps -- dépendances fournies par l'appelant
  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    load()
      .then((d) => active && setData(d))
      .catch((e: Error) => active && setError(e.message))
      .finally(() => active && setLoading(false))
    return () => {
      active = false // ignore une réponse arrivée après un changement de filtre
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps -- dépendances fournies par l'appelant

  return { data, error, loading }
}
