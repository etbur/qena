"""
Custom MySQL/MariaDB backend for Django 5 + MariaDB 10.4 (XAMPP).
Patches two incompatibilities:
  1. Skips minimum version check (Django 5 needs 10.5+, XAMPP has 10.4)
  2. Removes RETURNING clause from INSERT (MariaDB 10.4 doesn't support it)
"""
import django.db.backends.mysql.compiler as _mysql_compiler
from django.db.backends.mysql.base import DatabaseWrapper as _Base


# ── Monkey-patch SQLInsertCompiler to never use RETURNING ─────────────────────

_orig_execute_sql = _mysql_compiler.SQLInsertCompiler.execute_sql


def _patched_execute_sql(self, returning_fields=None):
    """
    Execute INSERT without RETURNING clause, then fetch the last inserted id
    using SELECT LAST_INSERT_ID() — works on MariaDB 10.4+.
    """
    if not returning_fields:
        return _orig_execute_sql(self, returning_fields=None)

    # Run without RETURNING
    _orig_execute_sql(self, returning_fields=None)

    # Return last insert id in the format Django expects
    with self.connection.cursor() as cursor:
        cursor.execute('SELECT LAST_INSERT_ID()')
        last_id = cursor.fetchone()[0]

    return [(last_id,)]


_mysql_compiler.SQLInsertCompiler.execute_sql = _patched_execute_sql


# ── DatabaseWrapper ────────────────────────────────────────────────────────────

class DatabaseWrapper(_Base):
    def check_database_version_supported(self):
        """Skip the MariaDB >= 10.5 requirement."""
        pass
