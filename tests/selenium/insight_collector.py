"""
Coleta métricas e insights de qualidade durante a execução da suite Selenium.

Hard asserts (assert) → falham o teste se algo crítico quebrar.
Soft insights (collector.warn) → registram oportunidade de melhoria sem falhar.

Ao fim da sessão, gera insights_report.json com métricas e insights por categoria:
  PERF    — tempos acima de thresholds
  UX      — friction points e gaps de usabilidade
  SEO     — meta tags, H1, canonical, structured data
  A11Y    — imagens sem alt, botões sem label
  CONTENT — dados faltando em páginas que deveriam tê-los
"""

import json
import datetime
from pathlib import Path
from typing import Literal

Category = Literal["PERF", "UX", "SEO", "A11Y", "CONTENT"]

_instance: "InsightCollector | None" = None


class InsightCollector:
    def __init__(self):
        global _instance
        _instance = self
        self.metrics: dict[str, float | str] = {}
        self.insights: list[dict] = []
        self._current_test: str = ""

    def set_test(self, test_name: str):
        self._current_test = test_name

    def metric(self, key: str, value: float | str):
        """Registra métrica numérica ou textual."""
        self.metrics[key] = value

    def warn(self, category: Category, message: str):
        """Registra insight de melhoria (não falha o teste)."""
        self.insights.append({
            "category": category,
            "test": self._current_test,
            "message": message,
        })

    def save(self, path: str = "insights_report.json") -> dict:
        summary = {
            cat: sum(1 for i in self.insights if i["category"] == cat)
            for cat in ("PERF", "UX", "SEO", "A11Y", "CONTENT")
        }
        report = {
            "run_at": datetime.datetime.utcnow().isoformat() + "Z",
            "base_url": self.metrics.get("base_url", "https://smartlic.tech"),
            "total_insights": len(self.insights),
            "summary": summary,
            "metrics": {k: v for k, v in self.metrics.items() if k != "base_url"},
            "insights": self.insights,
        }
        Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False))
        return report

    def print_summary(self):
        print("\n" + "=" * 60)
        print("INSIGHTS DE QUALIDADE — SmartLic Selenium Audit")
        print("=" * 60)
        categories = {"PERF": [], "UX": [], "SEO": [], "A11Y": [], "CONTENT": []}
        for ins in self.insights:
            categories[ins["category"]].append(ins)
        for cat, items in categories.items():
            if items:
                print(f"\n[{cat}] {len(items)} insight(s):")
                for item in items:
                    print(f"  • [{item['test']}] {item['message']}")
        print("\nMÉTRICAS:")
        for k, v in self.metrics.items():
            if k != "base_url":
                unit = "s" if "seconds" in k else ""
                print(f"  {k}: {v}{unit}")
        print("=" * 60)


def get_collector() -> "InsightCollector | None":
    return _instance
