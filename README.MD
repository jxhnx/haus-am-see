# Getting started

Start the stack with `docker compose up`

## OLTP Source

Postgres is used as OLTP source. You can connect to it with localhost:4444 and postgres:postgres as root user:password. To create a new database, use:

`docker compose exec postgres psql -U postgres -d postgres -c "CREATE DATABASE storefront;"`

Make sure to add the created database to `postgres-init/init.sql`, if meant to be permanent.

Hint: for a multi-database setup, you will need to adjust the flyway urls; for now, it is set up with the defualt `storefront` db.

### Migrations

Migrations are handled by flyway in `migrations/`. To apply migrations, run:

`docker compose up flyway`

### Seeder

FastAPI is used to seed the database with a full load and ongoing deltas. Check the Swagger UI at [localhost:8000/docs](http://localhost:8000/docs).

# Development

Pre-commit is used for linting. Run `pre-commit install` once to initialize it for this repo.
