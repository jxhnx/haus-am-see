# Getting started

## Start the stack

`docker compose up`

## Migrations

Migrations are handled by flyway in `migrations/`. Run:

`docker compose up flyway`

to apply migrations.

## Create a database (if not done by ipostgres-init/init.sql):

`docker compose exec postgres psql -U postgres -d postgres -c "CREATE DATABASE storefront;"`