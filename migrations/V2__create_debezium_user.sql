CREATE USER ${debezium_user} WITH REPLICATION LOGIN ENCRYPTED PASSWORD '${debezium_password}';

-- Allow connecting to the database
GRANT CONNECT ON DATABASE storefront TO ${debezium_user};

-- Allow the user to create publications
GRANT CREATE ON DATABASE storefront TO ${debezium_user};

-- Allow usage and read access on public schema and tables
GRANT USAGE ON SCHEMA public TO ${debezium_user};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${debezium_user};

-- Ensure future tables are also selectable
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO ${debezium_user};

-- Create the publication (needs superuser)
CREATE PUBLICATION ${debezium_storefront_publication_name} FOR ALL TABLES;
