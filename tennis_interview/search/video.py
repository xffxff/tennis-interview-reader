from dataclasses import dataclass
from datetime import datetime


@dataclass
class Thumbnails:
    small: str
    medium: str
    large: str


@dataclass
class Video:
    id: str
    title: str
    description: str
    url: str
    thumbnails: Thumbnails
    published_date: datetime