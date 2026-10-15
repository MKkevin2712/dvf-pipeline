-- Une ligne par commune : nom, département et position (centre des ventes géolocalisées), pour la carte.
select
    code_commune,
    max(nom_commune)                                                  as nom_commune,
    max(code_departement)                                             as code_departement,
    percentile_cont(0.5) within group (order by longitude)            as longitude,
    percentile_cont(0.5) within group (order by latitude)             as latitude,
    count(*)                                                          as nb_ventes_total
from {{ ref('fct_ventes_logements') }}
where longitude is not null and latitude is not null
group by code_commune
