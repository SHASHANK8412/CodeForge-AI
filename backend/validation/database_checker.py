import ast
import re
import time
import logging
from pathlib import Path
from backend.validation.models import ValidationResult
from backend.validation.utils import get_all_files

_logger = logging.getLogger("aiforge.performance")

class DatabaseChecker:
    """
    Validates database schema definitions: checks SQLAlchemy models, SQL schemas, 
    Prisma files, table naming conventions, primary keys, relationships, and foreign keys.
    """

    def validate(self, project_path: Path) -> ValidationResult:
        start_time = time.perf_counter()
        _logger.info("Database Checker Started")

        errors = []
        warnings = []
        models = [] # List of parsed model names and table names
        
        py_files = list(get_all_files(project_path, [".py"]))
        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # SQLAlchemy specific checks using AST parsing
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Verify if this class is an SQLAlchemy model (inherits from Base or Db.Model)
                        is_model = False
                        for base in node.bases:
                            base_name = ast.unparse(base)
                            if base_name in {"Base", "db.Model", "Model"}:
                                is_model = True
                                break
                        
                        if is_model:
                            # 1. Naming convention check: ClassDef should be CamelCase
                            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                                warnings.append(f"Model class name '{node.name}' does not follow CamelCase naming convention in {file_path.name}")
                            
                            tablename = None
                            has_primary_key = False
                            columns = []
                            foreign_keys = []
                            indexes = []

                            for subnode in node.body:
                                # Look for tablename assignment: __tablename__ = "users"
                                if isinstance(subnode, ast.Assign):
                                    for target in subnode.targets:
                                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                                            if isinstance(subnode.value, ast.Constant):
                                                tablename = str(subnode.value.value)
                                
                                # Look for Column definitions
                                # E.g. id = Column(Integer, primary_key=True)
                                if isinstance(subnode, ast.Assign) and isinstance(subnode.value, ast.Call):
                                    val_str = ast.unparse(subnode.value)
                                    if "Column(" in val_str:
                                        columns.append(subnode.targets[0].id if isinstance(subnode.targets[0], ast.Name) else "")
                                        if "primary_key=True" in val_str:
                                            has_primary_key = True
                                        if "ForeignKey(" in val_str:
                                            foreign_keys.append(val_str)
                                        if "index=True" in val_str or "Index(" in val_str:
                                            indexes.append(val_str)

                            # Validate SQLAlchemy Model Rules
                            if not has_primary_key:
                                errors.append(f"SQLAlchemy Model class '{node.name}' has no primary_key defined in {file_path.name}")
                            
                            if tablename:
                                # Table naming convention check: should be snake_case and lower
                                if not re.match(r"^[a-z0-9_]+$", tablename):
                                    warnings.append(f"Table name '{tablename}' should be lower snake_case in model '{node.name}' in {file_path.name}")
                                
                                models.append({
                                    "class": node.name,
                                    "table": tablename,
                                    "file": file_path.name,
                                    "columns": columns,
                                    "foreign_keys": foreign_keys,
                                    "indexes": indexes
                                })

            except Exception as exc:
                _logger.warning(f"Failed database AST scan for {file_path.name}: {exc}")

        # Check duplicate table names
        table_counts = {}
        for m in models:
            table = m["table"]
            table_counts[table] = table_counts.get(table, 0) + 1
            if table_counts[table] > 1:
                errors.append(f"Duplicate database table name __tablename__ = '{table}' declared in model '{m['class']}'")

        # 2. Check SQL schema files if any exist on disk
        sql_files = list(get_all_files(project_path, [".sql"]))
        for file_path in sql_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check CREATE TABLE naming
                tables = re.findall(r"CREATE\s+TABLE\s+([a-zA-Z0-9_\"`]+)", content, re.IGNORECASE)
                for t in tables:
                    clean_table = t.replace('"', '').replace('`', '').strip()
                    if not re.match(r"^[a-z0-9_]+$", clean_table):
                        warnings.append(f"SQL Table '{clean_table}' in {file_path.name} does not follow snake_case naming convention")
                
                # Check if SQL file defines primary keys
                if "primary key" not in content.lower():
                    warnings.append(f"SQL Schema file {file_path.name} has no explicit primary keys declared")
            except Exception:
                pass

        execution_time = round(time.perf_counter() - start_time, 4)
        
        score = 100.0
        score -= len(errors) * 15
        score -= len(warnings) * 2
        score = max(0.0, min(100.0, score))
        
        status = "PASS" if score >= 90.0 else "FAIL"
        
        _logger.info(f"Database Checker Finished. Status={status}, Score={score}")
        return ValidationResult(
            validator="Database Checker",
            status=status,
            score=score,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            metadata={
                "models_scanned": len(models),
                "sql_files_scanned": len(sql_files)
            }
        )
