-- Les agrégats doivent couvrir exactement les ventes de la table de faits.
select 1
from (select count(*) as n from {{ ref('fct_ventes_logements') }}) f,
     (select sum(nb_ventes) as n from {{ ref('agg_prix_m2_commune_annee') }}) c
where f.n <> c.n
