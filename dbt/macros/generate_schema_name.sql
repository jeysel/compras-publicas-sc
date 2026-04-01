{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

Isso faz o DBT usar **exatamente** o schema configurado no `dbt_project.yml`, sem prefixo:
```
+schema: raw         → raw
+schema: staging     → staging
+schema: intermediate → intermediate
+schema: marts       → marts