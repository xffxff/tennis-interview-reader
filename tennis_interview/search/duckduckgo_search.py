from duckduckgo_search import DDGS
from .video import Video, Thumbnails
from datetime import datetime


def duckduckgo_search(query, max_results=5):
    results = DDGS().videos(
        keywords=query,
        region="wt-wt",
        safesearch="off",
        timelimit="w",
        resolution="high",
        duration="medium",
        max_results=max_results,
    )

    videos = []
    for result in results:
        video = Video(
            id=result.get("content").split("v=")[1],
            title=result.get("title"),
            description=result.get("description"),
            url=result.get("content"),
            thumbnails=Thumbnails(
                small=result.get("images", {}).get("small"),
                medium=result.get("images", {}).get("medium"),
                large=result.get("images", {}).get("large"),
            ),
            published_date=datetime.fromisoformat(result.get("published")),
        )
        videos.append(video)
    return videos