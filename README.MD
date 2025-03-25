# Getting started

Run the full stack with:

`docker compose -f docker-compose.source.yaml -f docker-compose.streaming.yaml up`

Or layer by layer:

- OLTP Source and Seeder: `docker compose -f docker-compose.source.yaml`
- Streaming: `docker compose -f docker-compose.streaming.yaml`

## OLTP Source

Postgres is used as OLTP source. You can connect to it with localhost:4444 and postgres:postgres as root user:password. To create a new database, use:

`docker compose -f docker-compose.source.yaml exec postgres psql -U postgres -d postgres -c "CREATE DATABASE storefront;"`

Make sure to add the created database to `postgres-init/init.sql`, if meant to be permanent.

Hint: for a multi-database setup, you will need to adjust the flyway urls; for now, it is set up with the defualt `storefront` db.

### Migrations

Migrations are handled by flyway in `migrations/`. To apply migrations, run:

`docker compose -f docker-compose.source.yaml up flyway`

### Seeder

FastAPI is used to seed the database with a full load and ongoing deltas. Check the Swagger UI at [localhost:8000/docs](http://localhost:8000/docs).

## Kafka Streaming

# Development

Pre-commit is used for linting. Run `pre-commit install` once to initialize it for this repo.
