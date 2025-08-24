from typing import Dict, Type
from src.crawler.adapters.base import Adapter
from src.crawler.adapters.greenhouse import GreenhouseAdapter
from src.crawler.adapters.ashby import AshbyAdapter
from src.crawler.adapters.lever import LeverAdapter
from src.crawler.adapters.workday import WorkdayAdapter

ADAPTER_REGISTRY:Dict[str, Type[Adapter]] = {
    "Greenhouse":GreenhouseAdapter,
    "Ashby":AshbyAdapter,
    "Lever":LeverAdapter,
    # "Workday":WorkdayAdapter
}