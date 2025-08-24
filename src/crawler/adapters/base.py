from abc import ABC, abstractmethod
from typing import List
from src.crawler.schemas import Job


class Adapter(ABC):
    @abstractmethod
    async def fetch_jobs(self, company: str,url:str) -> List[Job]:
        ...

