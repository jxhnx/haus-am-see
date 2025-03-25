# Getting started

Start the stack with `docker compose up`

## OLTP Source

As OLTP source, we use Postgres. You can connect to it with localhost:4444 and postgres:postgres as root user:password.

`docker compose exec postgres psql -U postgres -d postgres -c "CREATE DATABASE storefront;"`

### Seeder

FastAPI is used to seed the database with a full load and ongoing deltas. Check the Swagger UI at [localhost:8000/docs](http://localhost:8000/docs).

### Migrations

Migrations are handled by flyway in `migrations/`. To apply migrations, run:

`docker compose up flyway`
