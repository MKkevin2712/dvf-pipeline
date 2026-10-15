-- Typage et renommage des données brutes. Aucune règle métier ici : une ligne par ligne source.
select
    id_mutation,
    cast(date_mutation as date)                         as date_mutation,
    nature_mutation,
    cast(valeur_fonciere as double precision)           as valeur_fonciere,
    code_postal,
    code_commune,
    nom_commune,
    code_departement,
    id_parcelle,
    type_local,
    cast(surface_reelle_bati as double precision)       as surface_reelle_bati,
    cast(nombre_pieces_principales as integer)          as nombre_pieces,
    cast(surface_terrain as double precision)           as surface_terrain,
    cast(longitude as double precision)                 as longitude,
    cast(latitude as double precision)                  as latitude,
    _source_file
from {{ source('raw', 'dvf_mutations') }}
