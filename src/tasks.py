import importlib
from .utils import get_logger
logger = get_logger()

def run_step(module_name, function_name, params):
    # import from package src.<module_name>
    mod = importlib.import_module(f"src.{module_name}")
    func = getattr(mod, function_name)
    logger.info(f"Running {module_name}.{function_name} with params {params}")
    return func(**params)
