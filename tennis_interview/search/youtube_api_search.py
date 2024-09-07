import os
from datetime import datetime

import googleapiclient.discovery

from .video import Thumbnails, Video


def youtube_api_search(query, max_results=5):
    api_service_name = "youtube"
    api_version = "v3"

    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key found in environment variables. Please set the 'GOOGLE_API_KEY' variable."
        )

    # Build the API client using the API key
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key
    )

    request = youtube.search().list(part="snippet", maxResults=max_results, q=query)
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        thumbnails = Thumbnails(
            small=item.get("snippet", {})
            .get("thumbnails", {})
            .get("default", {})
            .get("url"),
            medium=item.get("snippet", {})
            .get("thumbnails", {})
            .get("medium", {})
            .get("url"),
            large=item.get("snippet", {})
            .get("thumbnails", {})
            .get("high", {})
            .get("url"),
        )
        id = item.get("id", {}).get("videoId")
        url = f"https://www.youtube.com/watch?v={id}"
        video = Video(
            id=id,
            title=item.get("snippet", {}).get("title"),
            description=item.get("snippet", {}).get("description"),
            url=url,
            thumbnails=thumbnails,
            published_date=datetime.fromisoformat(
                item.get("snippet", {}).get("publishedAt")
            ),
        )
        videos.append(video)
    return videos
