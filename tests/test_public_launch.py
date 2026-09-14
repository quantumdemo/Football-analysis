"""Unit tests for Stage 20 Public Launch Manager."""

import pytest
from src.data.launch import PublicLaunchManager, ReleaseMetadata, PublicLaunchReport


def test_public_launch_manager_smoke_tests():
    manager = PublicLaunchManager()
    report = manager.run_post_deployment_smoke_tests()

    assert isinstance(report, PublicLaunchReport)
    assert report.release_tag == "v1.0.0"
    assert report.launch_status == "SUCCESS"
    assert report.all_smoke_tests_passed is True
    assert len(report.smoke_test_results) == 4

    for test_res in report.smoke_test_results:
        assert test_res.passed is True

    assert "PROBABILISTIC FORECAST ESTIMATES ONLY" in report.public_limitations
