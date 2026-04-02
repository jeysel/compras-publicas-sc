{#
  Macro: generate_schema_name

  Sobrescreve o comportamento padrão do dbt para geração de nomes de schema.

  Por padrão o dbt prefixaria o schema com o nome do target (ex: dbt_user_staging).
  Esta macro garante que o schema customizado seja usado exatamente como definido
  no dbt_project.yml — sem prefixo adicional.

  Exemplo:
    - Sem esta macro: dbt_cp_user_staging, dbt_cp_user_marts
    - Com esta macro: staging, intermediate, marts

  Referência: https://docs.getdbt.com/docs/build/custom-schemas
#}
{% macro generate_schema_name(custom_schema_name, node) %}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{% endmacro %}