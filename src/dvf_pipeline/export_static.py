"""Export des indicateurs en fichiers JSON statiques, pour publier l'interface web sans serveur.

L'interface React lit ces fichiers à la place de l'API quand elle est construite avec VITE_STATIC=1
(hébergement gratuit sur GitHub Pages). Les réponses sont exactement celles de l'API.

Usage :
    uv run python -m dvf_pipeline.export_static            # écrit web/public/data/*.json
"""
import json
from pathlib import Path

from fastapi import HTTPException

from dvf_pipeline import api, config

OUT = config.ROOT / "web" / "public" / "data"


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")


def export(out: Path = OUT) -> int:
    meta = api.meta()
    _write(out / "meta.json", meta)
    n = 1
    for dep in (d["code"] for d in meta["departements"]):
        for type_local in meta["types_local"]:
            _write(out / f"evolution_{dep}_{type_local}.json", api.evolution(dep, type_local))
            n += 1
            for annee in meta["annees"]:
                try:
                    kpis = api.kpis(dep, type_local, annee)
                except HTTPException as e:
                    if e.status_code != 404:   # 404 = aucune vente pour ces filtres : rien à exporter
                        raise
                    continue
                _write(out / f"kpis_{dep}_{type_local}_{annee}.json", kpis)
                _write(out / f"communes_{dep}_{type_local}_{annee}.json", api.communes(dep, type_local, annee, 10))
                n += 2
            for c in api.query("select code_commune from marts.dim_communes where code_departement = :dep",
                               {"dep": dep}):
                code = c["code_commune"]
                if not (out / f"commune_{code}.json").exists() or type_local == meta["types_local"][0]:
                    _write(out / f"commune_{code}.json", api.commune(code))
                    n += 1
    print(f"{n} fichiers écrits dans {out}")
    return n


if __name__ == "__main__":
    export()
