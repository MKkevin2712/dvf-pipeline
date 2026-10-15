-- Ventes de logements retenues pour l'analyse des prix : prix au m² plausible uniquement.
select *
from {{ ref('int_ventes_logements') }}
where prix_m2 between {{ var('prix_m2_min') }} and {{ var('prix_m2_max') }}
