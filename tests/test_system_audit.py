"""Unit tests for Stage 15 Full System Audit."""

import pytest
from src.audit.system_audit import SystemAuditor, SystemAuditReport


def test_system_audit_execution():
    auditor = SystemAuditor()
    report = auditor.run_full_audit()

    assert isinstance(report, SystemAuditReport)
    assert report.overall_passed is True
    assert report.critical_findings_count == 0
    assert len(report.findings) >= 4

    for finding in report.findings:
        assert finding.passed is True, f"Audit finding failed: {finding.check_name} - {finding.details}"
