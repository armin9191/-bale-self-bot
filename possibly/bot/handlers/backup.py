"""
Backup service.

A PostgreSQL backup must be generated through pg_dump/compatible
PostgreSQL tooling available in the deployment environment.

The bot should never send DATABASE_URL or database credentials to a user.
Only the resulting backup file may be sent, and only to the configured
POSSIBLY admin (1967315238).
"""
