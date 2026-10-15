-- Prix au m² par commune, année et type de logement.
-- La médiane (et non la moyenne) résiste aux ventes atypiques restantes.
select
    annee,
    code_departement,
    code_commune,
    nom_commune,
    type_local,
    count(*)                                                          as nb_ventes,
    percentile_cont(0.5)  within group (order by prix_m2)             as prix_m2_median,
    percentile_cont(0.25) within group (order by prix_m2)             as prix_m2_q1,
    percentile_cont(0.75) within group (order by prix_m2)             as prix_m2_q3,
    percentile_cont(0.5)  within group (order by prix)                as prix_median,
    percentile_cont(0.5)  within group (order by surface)             as surface_mediane
from {{ ref('fct_ventes_logements') }}
group by annee, code_departement, code_commune, nom_commune, type_local
