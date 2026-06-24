"""指标计算测试."""

import pytest


def test_pr_calculation() -> None:
    """测试 PR 计算."""
    actual_energy = 1000.0
    theoretical_energy = 1200.0
    pr = actual_energy / theoretical_energy
    assert abs(pr - 0.8333) < 0.01


def test_string_discrete_rate() -> None:
    """测试组串离散率检测."""
    currents = [5.0, 5.1, 4.9, 3.2]
    avg = sum(currents) / len(currents)
    max_deviation = max(abs(c - avg) for c in currents) / avg
    assert max_deviation > 0.1
