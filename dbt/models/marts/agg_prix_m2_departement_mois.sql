-- Évolution mensuelle du prix au m² par département et type de logement.
select
    mois,
    code_departement,
    type_local,
    count(*)                                                          as nb_ventes,
    percentile_cont(0.5) within group (order by prix_m2)              as prix_m2_median
from {{ ref('fct_ventes_logements') }}
group by mois, code_departement, type_local
