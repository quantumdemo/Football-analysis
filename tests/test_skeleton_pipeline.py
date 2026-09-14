"""Tests for pipeline skeleton orchestrator."""

import pytest
from datetime import datetime, timezone
from src.match.identifier import MatchIdentifier
from src.pipeline import PipelineSkeleton


def test_pipeline_skeleton_run():
    skeleton = PipelineSkeleton()
    now = datetime.now(timezone.utc)
    match = MatchIdentifier("M100", "TEAM_HOME", "TEAM_AWAY", now, "Champions League")

    report = skeleton.run_skeleton(match, [])

    assert report.match_id == "M100"
    assert report.decision == "NO_BET"
    assert report.report_data["stage"] == "Stage 1 Architecture Skeleton"
