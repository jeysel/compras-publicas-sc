# docker-compose.yml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: compras_publicas
      POSTGRES_USER: cp_user
      POSTGRES_PASSWORD: cp_pass
    volumes:
      - ./postgres/init:/docker-entrypoint-initdb.d
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  dbt:
    build: ./dbt
    depends_on:
      - postgres
    volumes:
      - ./dbt:/usr/app/dbt
    environment:
      DBT_PROFILES_DIR: /usr/app/dbt

volumes:
  pgdata: