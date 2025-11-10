import yaml
from .tasks import run_step
from .utils import get_logger
logger = get_logger()

def load_pipeline(yaml_path="pipeline.yaml"):
    with open(yaml_path) as f:
        return yaml.safe_load(f)

def run_pipeline(yaml_path="pipeline.yaml"):
    pipeline = load_pipeline(yaml_path)
    results = {}
    for step in pipeline.get("steps", []):
        name = step.get("name")
        module = step.get("module")
        function = step.get("function")
        params = step.get("params", {}) or {}
        try:
            res = run_step(module, function, params)
            results[name] = res
        except Exception as e:
            logger.exception(f"Step {name} failed: {e}")
            raise
    logger.info("Pipeline finished")
    return results

if __name__ == "__main__":
    run_pipeline()
