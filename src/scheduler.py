from apscheduler.schedulers.blocking import BlockingScheduler
from .pipeline_runner import run_pipeline
from .utils import get_logger

logger = get_logger()

def start_scheduler(yaml_path="pipeline.yaml", hour=2, minute=0):
    sched = BlockingScheduler()
    # run once immediately
    run_pipeline(yaml_path)
    # schedule daily at given hour
    sched.add_job(lambda: run_pipeline(yaml_path), 'cron', hour=hour, minute=minute)
    logger.info(f"Scheduler started — pipeline scheduled daily at {hour:02d}:{minute:02d}")
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    start_scheduler()
