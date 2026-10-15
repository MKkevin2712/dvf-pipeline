-- Une ligne par vente d'UN logement (maison ou appartement), avec son prix au m².
--
-- Pièges des données DVF traités ici :
--   1. Une mutation compte plusieurs lignes (logement, caves, parkings, parcelles) et le prix est
--      RÉPÉTÉ sur chacune : on regroupe par mutation et on prend le prix une seule fois (max).
--   2. Quand une vente porte sur plusieurs logements, le prix de chacun est inconnu : ces ventes
--      sont exclues (un prix au m² calculé sur le total serait faux).
with lignes as (
    select *
    from {{ ref('stg_dvf__mutations') }}
    where nature_mutation in ('Vente', 'Vente en l''état futur d''achèvement')
),

par_mutation as (
    select
        id_mutation,
        min(date_mutation)                                                       as date_mutation,
        max(nature_mutation)                                                     as nature_mutation,
        max(valeur_fonciere)                                                     as prix,
        -- localisation prise sur la ligne du logement : une vente peut inclure des parcelles
        -- situées dans une autre commune (terrain en limite communale)
        max(code_departement) filter (where type_local in ('Maison', 'Appartement')) as code_departement,
        max(code_commune) filter (where type_local in ('Maison', 'Appartement'))  as code_commune,
        max(nom_commune) filter (where type_local in ('Maison', 'Appartement'))   as nom_commune,
        max(code_postal) filter (where type_local in ('Maison', 'Appartement'))   as code_postal,
        count(*) filter (where type_local in ('Maison', 'Appartement'))          as nb_lignes_logement,
        count(distinct type_local) filter (where type_local in ('Maison', 'Appartement')) as nb_types_logement,
        max(type_local) filter (where type_local in ('Maison', 'Appartement'))   as type_local,
        max(surface_reelle_bati) filter (where type_local in ('Maison', 'Appartement')) as surface,
        max(nombre_pieces) filter (where type_local in ('Maison', 'Appartement')) as nombre_pieces,
        count(*) filter (where type_local = 'Dépendance')                        as nb_dependances,
        max(surface_terrain)                                                     as surface_terrain,
        avg(longitude) filter (where type_local in ('Maison', 'Appartement'))    as longitude,
        avg(latitude) filter (where type_local in ('Maison', 'Appartement'))     as latitude
    from lignes
    group by id_mutation
)

select
    id_mutation,
    date_mutation,
    cast(extract(year from date_mutation) as integer)                as annee,
    cast(date_trunc('month', date_mutation) as date)                 as mois,
    nature_mutation = 'Vente en l''état futur d''achèvement'         as est_neuf,
    code_departement,
    code_commune,
    nom_commune,
    code_postal,
    type_local,
    surface,
    nombre_pieces,
    nb_dependances,
    surface_terrain,
    prix,
    prix / surface                                                    as prix_m2,
    longitude,
    latitude
from par_mutation
where nb_lignes_logement = 1                                          -- un seul logement vendu
  and prix > 0
  and surface >= {{ var('surface_min') }}
