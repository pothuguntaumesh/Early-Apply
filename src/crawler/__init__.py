# import asyncio
# import importlib.resources
# import logging
# import yaml
# from typing import List
# from src.crawler.models import Job
# from src.crawler.adapters import ADAPTER_REGISTRY

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("crawler")

# async def crawl_all()->List[Job]:   
#     companies = _load_yaml()
#     tasks=[]
#     for company in companies:
#         name=company["name"]
#         for feed in company.get("feeds",[]):
#             adapter_cls=ADAPTER_REGISTRY.get(feed["ats"])
#             if not adapter_cls:
#                 logger.warning(f"No adapter found for {feed['ats']}")
#                 continue
#             adapter=adapter_cls()
#             tasks.append(adapter.fetch_jobs(name,feed["url"]))
    
#     results= await asyncio.gather(*tasks,return_exceptions=True)
#     jobs:List[Job]=[]
#     for result in results:
#         if isinstance(result,Exception):
#             logger.error(f"Error fetching jobs: {result}")
#             continue
#         jobs.extend(result)
#     return jobs




# def _load_yaml():
#     yaml_path=importlib.resources.files(__package__)/"companies.yaml"
#     with open(yaml_path, "r") as f:
#         return yaml.safe_load(f)





