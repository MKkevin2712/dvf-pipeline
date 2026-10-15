# Interface web (React + TypeScript)

Tableau de bord des prix immobiliers, alimenté par l'API FastAPI du pipeline (`src/dvf_pipeline/api.py`).

```bash
npm install
npm run dev      # http://localhost:5173 (les appels /api sont redirigés vers http://127.0.0.1:8000)
npm run build    # version de production dans dist/
```

Bibliothèques : React 19, Vite, Leaflet / react-leaflet (carte), Recharts (graphiques).
