-- Aucune vente retenue ne doit avoir un prix au m² hors des bornes de plausibilité.
select *
from {{ ref('fct_ventes_logements') }}
where prix_m2 < {{ var('prix_m2_min') }} or prix_m2 > {{ var('prix_m2_max') }}
