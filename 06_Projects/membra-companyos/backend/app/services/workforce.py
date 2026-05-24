"""MEMBRA CompanyOS — Workforce service for 60 LLM employees.
Orchestrates employee registration, task assignment, Ollama execution,
and contribution tracking.
"""
import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.workforce_config import EMPLOYEES, DEPARTMENTS, get_employee_config
from app.services.ollama_connector import OllamaConnector
from app.models.workforce import WorkforceEmployee, WorkforceContribution, WorkforceTask
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkforceService:
    def __init__(self, db: Session):
        self.db = db
        self._connectors: Dict[str, OllamaConnector] = {}

    def ensure_employees(self) -> Dict[str, Any]:
        """Idempotently register all 60 employees from config into DB."""
        created = 0
        skipped = 0
        for emp_cfg in EMPLOYEES:
            existing = self.db.query(WorkforceEmployee).filter(
                WorkforceEmployee.employee_id == emp_cfg["id"]
            ).first()
            if existing:
                skipped += 1
                continue
            emp = WorkforceEmployee(
                id=uuid.uuid4(),
                employee_id=emp_cfg["id"],
                name=emp_cfg["name"],
                department=emp_cfg["department"],
                title=emp_cfg["title"],
                model=emp_cfg.get("model", "llama3.2"),
                system_prompt=emp_cfg["system_prompt"],
                responsibilities=emp_cfg.get("responsibilities", []),
                status="idle",
            )
            self.db.add(emp)
            created += 1
        self.db.commit()
        return {"created": created, "skipped": skipped, "total": len(EMPLOYEES)}

    def get_connector(self, employee_id: str) -> OllamaConnector:
        """Get or create an Ollama connector for an employee."""
        if employee_id not in self._connectors:
            cfg = get_employee_config(employee_id)
            if not cfg:
                raise ValueError(f"Unknown employee: {employee_id}")
            self._connectors[employee_id] = OllamaConnector(
                model=cfg.get("model", "llama3.2"),
                system_prompt=cfg.get("system_prompt", ""),
            )
        return self._connectors[employee_id]

    def list_employees(self, department: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[WorkforceEmployee]:
        q = self.db.query(WorkforceEmployee)
        if department:
            q = q.filter(WorkforceEmployee.department == department)
        if status:
            q = q.filter(WorkforceEmployee.status == status)
        return q.order_by(WorkforceEmployee.department, WorkforceEmployee.name).limit(limit).all()

    def get_employee(self, employee_id: str) -> Optional[WorkforceEmployee]:
        return self.db.query(WorkforceEmployee).filter(
            WorkforceEmployee.employee_id == employee_id
        ).first()

    def get_departments(self) -> List[Dict[str, Any]]:
        from app.core.workforce_config import DEPARTMENTS
        result = []
        for dept in DEPARTMENTS:
            emp_count = self.db.query(WorkforceEmployee).filter(
                WorkforceEmployee.department == dept["id"]
            ).count()
            active_count = self.db.query(WorkforceEmployee).filter(
                WorkforceEmployee.department == dept["id"],
                WorkforceEmployee.status == "idle",
            ).count()
            result.append({
                **dept,
                "employee_count": emp_count,
                "active_count": active_count,
            })
        return result

    async def run_employee(self, employee_id: str, task_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Execute a task via the employee's Ollama connector and record contribution."""
        emp = self.get_employee(employee_id)
        if not emp:
            return {"success": False, "error": "Employee not found"}

        cfg = get_employee_config(employee_id)
        prompt = task_prompt or self._default_prompt_for_role(cfg)

        emp.status = "running"
        emp.last_run_at = datetime.now(timezone.utc)
        emp.total_runs += 1
        self.db.commit()

        connector = self.get_connector(employee_id)
        start_ms = int(time.time() * 1000)

        try:
            result = await connector.generate(prompt)
            duration = int(time.time() * 1000) - start_ms

            if result["success"]:
                emp.status = "idle"
                emp.last_output = result["content"][:2000]
                emp.last_error = None
                emp.total_contributions += 1

                contrib = WorkforceContribution(
                    id=uuid.uuid4(),
                    employee_id=employee_id,
                    department=emp.department,
                    task_type="llm_generation",
                    prompt=prompt[:2000],
                    output=result["content"],
                    output_summary=result["content"][:256],
                    duration_ms=duration,
                    metadata_json={"model": result["model"], "temperature": 0.7},
                )
                self.db.add(contrib)
                self.db.commit()

                return {
                    "success": True,
                    "employee_id": employee_id,
                    "output": result["content"],
                    "duration_ms": duration,
                    "model": result["model"],
                }
            else:
                emp.status = "error"
                emp.last_error = result["content"]
                self.db.commit()
                return {
                    "success": False,
                    "employee_id": employee_id,
                    "error": result["content"],
                    "duration_ms": duration,
                }
        except Exception as e:
            emp.status = "error"
            emp.last_error = str(e)
            self.db.commit()
            return {"success": False, "employee_id": employee_id, "error": str(e)}

    def _default_prompt_for_role(self, cfg: Dict[str, Any]) -> str:
        """Generate a default daily task prompt based on the employee's role."""
        resp = cfg.get("responsibilities", [])
        resp_str = ", ".join(resp) if resp else "general work"
        return (
            f"You are {cfg.get('name', 'an employee')} ({cfg.get('title', '')}). "
            f"Your responsibilities include: {resp_str}. "
            f"Produce a brief status report on what you would accomplish today. "
            f"Keep it under 300 words and be specific."
        )

    def get_contributions(self, employee_id: Optional[str] = None, department: Optional[str] = None, limit: int = 50) -> List[WorkforceContribution]:
        q = self.db.query(WorkforceContribution)
        if employee_id:
            q = q.filter(WorkforceContribution.employee_id == employee_id)
        if department:
            q = q.filter(WorkforceContribution.department == department)
        return q.order_by(WorkforceContribution.created_at.desc()).limit(limit).all()

    def get_stats(self) -> Dict[str, Any]:
        total_employees = self.db.query(WorkforceEmployee).count()
        running = self.db.query(WorkforceEmployee).filter(WorkforceEmployee.status == "running").count()
        idle = self.db.query(WorkforceEmployee).filter(WorkforceEmployee.status == "idle").count()
        errors = self.db.query(WorkforceEmployee).filter(WorkforceEmployee.status == "error").count()
        total_contributions = self.db.query(WorkforceContribution).count()

        dept_stats = {}
        for dept in DEPARTMENTS:
            emp_count = self.db.query(WorkforceEmployee).filter(
                WorkforceEmployee.department == dept["id"]
            ).count()
            contrib_count = self.db.query(WorkforceContribution).filter(
                WorkforceContribution.department == dept["id"]
            ).count()
            dept_stats[dept["id"]] = {
                "name": dept["name"],
                "employees": emp_count,
                "contributions": contrib_count,
            }

        return {
            "total_employees": total_employees,
            "running": running,
            "idle": idle,
            "errors": errors,
            "total_contributions": total_contributions,
            "departments": dept_stats,
        }
