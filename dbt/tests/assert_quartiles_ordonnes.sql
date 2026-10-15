-- Cohérence statistique : premier quartile ≤ médiane ≤ troisième quartile.
select *
from {{ ref('agg_prix_m2_commune_annee') }}
where not (prix_m2_q1 <= prix_m2_median and prix_m2_median <= prix_m2_q3)
