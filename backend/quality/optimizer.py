import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.quality.optimizer")


class PerformanceOptimizer:
    """
    PerformanceOptimizer analyzes generated code for performance bottlenecks
    and suggests concrete optimizations for Frontend & Backend.
    """

    def analyze_performance(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        recommendations = []

        # 1. Database Indexing Analysis
        sql_content = next((c for path, c in project_files.items() if "schema.sql" in path), "")
        if sql_content and "CREATE INDEX" not in sql_content and "FOREIGN KEY" in sql_content:
            recommendations.append({
                "component": "Database",
                "issue": "Missing Indexes on Foreign Key Columns",
                "recommendation": "Add CREATE INDEX statements for foreign key columns to improve JOIN speeds."
            })

        # 2. React Lazy Loading Analysis
        fe_content = next((c for path, c in project_files.items() if "App.jsx" in path), "")
        if fe_content and "React.lazy" not in fe_content and fe_content.count("import ") > 5:
            recommendations.append({
                "component": "Frontend",
                "issue": "Monolithic Frontend Bundle",
                "recommendation": "Use React.lazy() and Suspense for route-based code splitting."
            })

        # 3. FastAPI Async Handlers Analysis
        be_content = next((c for path, c in project_files.items() if "main.py" in path), "")
        if be_content and "def " in be_content and "async def " not in be_content:
            recommendations.append({
                "component": "Backend",
                "issue": "Synchronous API Route Handlers",
                "recommendation": "Convert synchronous endpoint functions to 'async def' for non-blocking I/O."
            })

        perf_score = max(70, 100 - (len(recommendations) * 10))
        return {
            "performance_score": perf_score,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }


# Global PerformanceOptimizer Instance
global_performance_optimizer = PerformanceOptimizer()
