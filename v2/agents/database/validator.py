"""
AIForge V2 – Database Report Validator Gate
===========================================
Validates structural completeness and schema integrity of generated DatabaseReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.database.models import DatabaseReport

_logger = logging.getLogger("aiforge.v2.database.validator")


class DatabaseValidator:

    def validate_report(self, report: DatabaseReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name:
            issues.append("Project name is missing.")

        if len(report.tables) < 2:
            issues.append("Fewer than 2 database tables generated.")

        if not report.ddl_schema_sql:
            issues.append("PostgreSQL DDL SQL schema is empty.")

        if not report.sqlalchemy_models_code:
            issues.append("SQLAlchemy ORM models code is empty.")

        if len(report.indexes) < 1:
            issues.append("No SQL indexes configured.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"DatabaseValidator: Persistence layer for '{report.project_name}' PASSED validation gate.")
        else:
            _logger.warning(f"DatabaseValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_database_validator = DatabaseValidator()
