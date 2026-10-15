{# Utilise directement le nom de schéma configuré (staging, intermediate, marts),
   sans le préfixe par défaut de dbt (« public_staging »). #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}
