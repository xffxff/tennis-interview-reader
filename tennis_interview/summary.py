import argparse
import json
import os

from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi


def create_prompt(transcript_text):
    prompt = f"""
Below I will provide you with a transcript of an interview. These transcripts may be automatically generated subtitles from a YouTube video and are not completely accurate, but they can be used as a reference. Please complete the following tasks based on the transcript:

1. Summarize the content of the interview, briefly outlining the main points and key viewpoints.
2. List all the questions from the interview and the interviewee's responses. The interviewee's responses do not need to be summarized; try to keep them as original as possible.

Here is the interview transcript for reference. 
{transcript_text}
"""
    return prompt


def send_to_openai(prompt, stream=False, stream_callback=None):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    response = client.chat.completions.create(
        model="moyi-chat-v03",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=stream,
    )

    if stream:
        res = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                delta = chunk.choices[0].delta.content
                if stream_callback is not None:
                    stream_callback(delta)
                res += delta
    else:
        res = response.choices[0].message.content

    return res


CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def load_cached_transcript(video_id):
    cache_file = os.path.join(CACHE_DIR, f"{video_id}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as file:
            return json.load(file)
    return None


def save_transcript_to_cache(video_id, transcript):
    cache_file = os.path.join(CACHE_DIR, f"{video_id}.json")
    with open(cache_file, "w") as file:
        json.dump(transcript, file)


def summary(video_id):
    transcript_text = load_cached_transcript(video_id)
    if transcript_text is None:
        supported_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in supported_transcripts:
            print("Getting transcript for language:", transcript.language)
            transcript_text = transcript.fetch()
            break
        if transcript_text is None:
            print("No transcript found.")
            return
        save_transcript_to_cache(video_id, transcript_text)

    # Format the transcript for the prompt
    transcript_text = "\n".join([f"- {entry['text']}" for entry in transcript_text])

    # Create the prompt
    prompt = create_prompt(transcript_text)

    # Send the prompt to OpenAI
    # response = send_to_openai(
    #     prompt, stream=True, stream_callback=lambda x: print(x, end="", flush=True)
    # )
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    response = client.chat.completions.create(
        model="moyi-chat-v03",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    return response
