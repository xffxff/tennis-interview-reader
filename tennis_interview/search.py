import os

import googleapiclient.discovery


def youtube_search(query, max_results=5):
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

    return response


if __name__ == "__main__":
    query = "us open 2024 interview"
    response = youtube_search(query)
    from pprint import pprint

    pprint(response)
