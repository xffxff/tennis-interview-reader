import json
import os
from datetime import datetime, timedelta

import requests

from .video import Thumbnails, Video


def serper_api_search(query, max_results=5):
    url = "https://google.serper.dev/videos"

    # Get API key from environment variable
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key found in environment variables. Please set the 'SERPER_API_KEY' variable."
        )

    payload = json.dumps({"q": query, "num": max_results})
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=payload)
    response_data = response.json()

    videos = []
    for item in response_data.get("videos", []):
        thumbnails = Thumbnails(
            small=item.get("imageUrl"),
            medium=item.get("imageUrl"),
            large=item.get("imageUrl"),
        )

        # Convert relative time to datetime
        published_date = parse_relative_time(item.get("date"))

        video = Video(
            id=(
                item.get("link").split("v=")[-1]
                if "youtube.com" in item.get("link", "")
                else None
            ),
            title=item.get("title"),
            description=item.get("snippet"),
            url=item.get("link"),
            thumbnails=thumbnails,
            published_date=published_date,
        )
        videos.append(video)

    return videos[:max_results]


def parse_relative_time(relative_time):
    if not relative_time:
        return None

    now = datetime.now()

    if "hour" in relative_time:
        hours = int(relative_time.split()[0])
        return now - timedelta(hours=hours)
    elif "day" in relative_time:
        days = int(relative_time.split()[0])
        return now - timedelta(days=days)
    elif "week" in relative_time:
        weeks = int(relative_time.split()[0])
        return now - timedelta(weeks=weeks)
    elif "month" in relative_time:
        months = int(relative_time.split()[0])
        return now - timedelta(days=months * 30)  # Approximation
    elif "year" in relative_time:
        years = int(relative_time.split()[0])
        return now - timedelta(days=years * 365)  # Approximation

    return None
