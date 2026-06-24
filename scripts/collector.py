#!/usr/bin/env python3
"""独立运行的采集器脚本.

示例:
    PYTHONPATH=backend:.:backend/.apt-libs/usr/lib/python3/dist-packages \
        python3 scripts/collector.py --station-id 1 --interval 5
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 把 backend 加入路径，方便独立运行
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.collector.runner import CollectorRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="PVOps 边缘采集器")
    parser.add_argument("--station-id", type=int, required=True, help="电站 ID")
    parser.add_argument("--interval", type=int, default=5, help="采集间隔(秒)")
    args = parser.parse_args()

    runner = CollectorRunner(station_id=args.station_id, interval=args.interval)

    try:
        asyncio.run(runner.run_forever())
    except KeyboardInterrupt:
        logging.info("采集器已停止")


if __name__ == "__main__":
    main()
