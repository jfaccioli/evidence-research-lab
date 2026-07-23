"""Database schema versioning utilities (temporary DBs; explicit migrate only).

Importing this package does **not** open databases or run migrations.
"""

from crl.db.schema import (
    CURRENT_P1_SCHEMA_VERSION,
    SCHEMA_COMPONENT_P1,
    MalformedSchemaMetaError,
    SchemaError,
    SchemaMigrationError,
    UnsupportedSchemaVersionError,
    connect_p1,
    derive_completeness,
    get_schema_version,
    legacy_epoch_status_for_null,
    migrate_database,
    never_auto_complete,
    open_legacy_compatibility,
    read_schema_version_from_path,
    verify_p1_v1_schema,
    verify_p1_v2_schema,
    verify_schema_for_version,
)

__all__ = [
    "CURRENT_P1_SCHEMA_VERSION",
    "SCHEMA_COMPONENT_P1",
    "MalformedSchemaMetaError",
    "SchemaError",
    "SchemaMigrationError",
    "UnsupportedSchemaVersionError",
    "connect_p1",
    "derive_completeness",
    "get_schema_version",
    "legacy_epoch_status_for_null",
    "migrate_database",
    "never_auto_complete",
    "open_legacy_compatibility",
    "read_schema_version_from_path",
    "verify_p1_v1_schema",
    "verify_p1_v2_schema",
    "verify_schema_for_version",
]
