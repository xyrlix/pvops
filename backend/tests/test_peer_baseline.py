"""群体基线 / 排名单测.

聚焦 MockDataProvider.get_peer_baseline + get_peer_ranking 的纯逻辑。
"""

from __future__ import annotations

from typing import Any

import pytest

from app.demo.mock_provider import MockDataProvider, _capacity_bucket, _percentile

# ─── helpers ────────────────────────────────────────────────


def _mk_station(sid: int, capacity_kw: float, **metrics: float) -> dict[str, Any]:
    return {
        "station_id": sid,
        "name": f"电站{sid}",
        "capacity_kw": capacity_kw,
        "pr": metrics.get("pr", 0.85),
        "completion_rate": metrics.get("completion_rate", 0.88),
        "health_score": metrics.get("health_score", 90.0),
        "daily_energy_kwh": metrics.get("daily_energy_kwh", 3000.0),
        "loss_kwh": metrics.get("loss_kwh", 100.0),
        "loss_cny": metrics.get("loss_cny", 42.0),
    }


# ─── 容量档位 ──────────────────────────────────────────────


def test_capacity_bucket_boundaries() -> None:
    assert _capacity_bucket(500) == "<1MW"
    assert _capacity_bucket(999) == "<1MW"
    assert _capacity_bucket(1000) == "1-5MW"
    assert _capacity_bucket(4999) == "1-5MW"
    assert _capacity_bucket(5000) == "5-10MW"
    assert _capacity_bucket(9999) == "5-10MW"
    assert _capacity_bucket(10000) == "10-50MW"
    assert _capacity_bucket(49999) == "10-50MW"
    assert _capacity_bucket(50000) == "50MW+"


def test_percentile_single_value() -> None:
    assert _percentile([42.0], 50) == 42.0


def test_percentile_two_values_50() -> None:
    # p=50 在 rank=0.5 处，linear interp = (10 + 20)/2 = 15
    assert _percentile([10.0, 20.0], 50) == 15.0


def test_percentile_25_of_4_values() -> None:
    # p=25 在 rank=0.75 处 → index 0 (val=10) 与 index 1 (val=20) 之间
    # 10 * 0.25 + 20 * 0.75 = 2.5 + 15 = 17.5
    assert _percentile([10.0, 20.0, 30.0, 40.0], 25) == 17.5


def test_percentile_empty() -> None:
    assert _percentile([], 50) == 0.0


# ─── MockDataProvider.get_peer_baseline ─────────────────────


@pytest.mark.asyncio
async def test_peer_baseline_filters_by_capacity_bucket() -> None:
    p = MockDataProvider()
    stations = [
        _mk_station(1, 500, pr=0.9, completion_rate=0.9, health_score=95),  # <1MW
        _mk_station(2, 800, pr=0.85, completion_rate=0.85, health_score=90),  # <1MW
        _mk_station(3, 3000, pr=0.8, completion_rate=0.8, health_score=85),  # 1-5MW
        _mk_station(4, 6000, pr=0.7, completion_rate=0.7, health_score=80),  # 5-10MW
    ]
    baseline = await p.get_peer_baseline(stations, capacity_kw=600)
    assert baseline["capacity_bucket"] == "<1MW"
    assert baseline["sample_size"] == 2
    # median(pr) = (0.85 + 0.9) / 2 = 0.875
    assert abs(baseline["median_pr"] - 0.875) < 0.001


@pytest.mark.asyncio
async def test_peer_baseline_empty_returns_nulls() -> None:
    p = MockDataProvider()
    baseline = await p.get_peer_baseline([], capacity_kw=1000)
    assert baseline["sample_size"] == 0
    assert baseline["median_pr"] is None
    assert baseline["median_health_score"] is None


@pytest.mark.asyncio
async def test_peer_baseline_top_quartile_above_median() -> None:
    """top_quartile (P75) 应当 ≥ median (P50)."""
    p = MockDataProvider()
    stations = [_mk_station(i, 2000, pr=0.7 + i * 0.02) for i in range(1, 6)]
    baseline = await p.get_peer_baseline(stations, capacity_kw=2000)
    assert baseline["top_quartile_pr"] >= baseline["median_pr"]


# ─── MockDataProvider.get_peer_ranking ──────────────────────


@pytest.mark.asyncio
async def test_peer_ranking_groups_by_bucket_and_assigns_rank() -> None:
    p = MockDataProvider()
    stations = [
        _mk_station(1, 2000, health_score=95),  # 1-5MW
        _mk_station(2, 3000, health_score=85),  # 1-5MW
        _mk_station(3, 8000, health_score=92),  # 5-10MW
        _mk_station(4, 9000, health_score=88),  # 5-10MW
    ]
    ranking = await p.get_peer_ranking(stations, metric="health_score")
    # 验证每个档位内按 health_score 倒序
    bucket_1_5 = [r for r in ranking if r["capacity_bucket"] == "1-5MW"]
    assert [r["station_id"] for r in bucket_1_5] == [1, 2]
    assert [r["rank_in_bucket"] for r in bucket_1_5] == [1, 2]

    bucket_5_10 = [r for r in ranking if r["capacity_bucket"] == "5-10MW"]
    assert [r["station_id"] for r in bucket_5_10] == [3, 4]


@pytest.mark.asyncio
async def test_peer_ranking_loss_metric_ascending() -> None:
    """对 loss_kwh/loss_cny，rank 应升序（越低越好）."""
    p = MockDataProvider()
    stations = [
        _mk_station(1, 2000, loss_kwh=100),
        _mk_station(2, 2000, loss_kwh=50),
        _mk_station(3, 2000, loss_kwh=200),
    ]
    ranking = await p.get_peer_ranking(stations, metric="loss_kwh")
    # 损失越低排名越前
    assert ranking[0]["station_id"] == 2  # loss=50
    assert ranking[1]["station_id"] == 1  # loss=100
    assert ranking[2]["station_id"] == 3  # loss=200


@pytest.mark.asyncio
async def test_peer_ranking_empty() -> None:
    p = MockDataProvider()
    assert await p.get_peer_ranking([], metric="health_score") == []


# ─── metrics_service facade（不依赖 DB） ─────────────────────


@pytest.mark.asyncio
async def test_metrics_service_peer_baseline_calls_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """验证 facade 正确调用 provider，并把 self 字段注入."""
    from app.services import metrics_service

    async def fake_overview() -> list[dict[str, Any]]:
        return [
            _mk_station(1, 800, pr=0.9, completion_rate=0.9, health_score=95),
            _mk_station(2, 1200, pr=0.85, completion_rate=0.85, health_score=90),
        ]

    monkeypatch.setattr(metrics_service, "get_stations_overview", fake_overview)

    class FakeProvider:
        async def get_peer_baseline(self, stations, capacity_kw):
            return {
                "capacity_bucket": "<1MW",
                "sample_size": 1,
                "median_pr": 0.9,
                "median_completion_rate": 0.9,
                "median_health_score": 95.0,
                "median_daily_energy_per_kw": 3.75,
                "top_quartile_pr": 0.9,
            }

    monkeypatch.setattr(metrics_service, "get_data_provider", lambda: FakeProvider())

    result = await metrics_service.get_station_peer_baseline(1)
    assert result["capacity_bucket"] == "<1MW"
    assert result["self"]["station_id"] == 1
    assert result["self"]["name"] == "电站1"


@pytest.mark.asyncio
async def test_metrics_service_peer_baseline_handles_missing_station(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """overview 中找不到 station_id 时返回空基线."""
    from app.services import metrics_service

    async def fake_overview() -> list[dict[str, Any]]:
        return [_mk_station(999, 1000)]

    monkeypatch.setattr(metrics_service, "get_stations_overview", fake_overview)

    result = await metrics_service.get_station_peer_baseline(42)
    assert result["sample_size"] == 0
    assert result["median_pr"] is None
