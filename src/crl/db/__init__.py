"""Database schema versioning utilities (temporary DBs; explicit migrate only).

Importing this package does **not** open databases or run migrations.
"""

from crl.db.schema import (
    CURRENT_P1_SCHEMA_VERSION,
    SCHEMA_COMPONENT_P1,
    SchemaError,
    SchemaMigrationError,
    UnsupportedSchemaVersionError,
    get_schema_version,
    migrate_database,
    open_legacy_compatibility,
    read_schema_version_from_path,
)

__all__ = [
    "CURRENT_P1_SCHEMA_VERSION",
    "SCHEMA_COMPONENT_P1",
    "SchemaError",
    "SchemaMigrationError",
    "UnsupportedSchemaVersionError",
    "get_schema_version",
    "migrate_database",
    "open_legacy_compatibility",
    "read_schema_version_from_path",
]
