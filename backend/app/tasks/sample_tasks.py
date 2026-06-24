"""示例异步任务."""

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True)
def add(self, x: int, y: int) -> int:
    """示例加法任务."""
    return x + y


@celery_app.task
def process_inverter_data(station_id: int, inverter_id: str, data: dict) -> dict:
    """处理逆变器数据任务."""
    # TODO: 实现数据清洗、指标计算、告警检测
    return {"station_id": station_id, "inverter_id": inverter_id, "processed": True}
