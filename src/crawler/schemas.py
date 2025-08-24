from dataclasses import asdict, dataclass,field
from datetime import datetime,timezone
from typing import Any, Dict,Optional,List

@dataclass(frozen=True, slots=True)
class Job:

    company: str
    external_id: str               
    source_feed: str

    title: str
    job_updated_at: datetime
    department: Optional[str] = None
    team: Optional[str] = None
    employment_type: Optional[str] = None

    countries: List[str]  =field(default_factory=list)
    cities:    List[str]  =field(default_factory=list)
    is_remote: bool = False

    job_url:  str               = ""       
    apply_url: Optional[str]    = None

    description: Optional[str] = None
    posted_at:   datetime       = field(default_factory=lambda: datetime.now(timezone.utc))
    

    

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)