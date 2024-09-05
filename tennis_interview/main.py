import argparse
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import json
import os

def create_zh_prompt(transcript_text):
    prompt = f"""
下面我将提供给你一场采访的文字记录，这些文字记录可能是 Youtube 视频中自动生成的字幕，并不是完全准确的，但是可以作为参考。请你更具文字记录完成以下任务：

1. 总结采访中的内容，用简要的语言概括出采访的主要内容和关键观点。
2. 提取罗列出本次采访中的所有问题，以及受访者的回答，受访者的回答不用提炼总结，尽量保持原汁原味

这是采访的文字记录供参考，要求用中文回答，包括提问和回答：
{transcript_text}
"""
    return prompt

def send_to_openai(prompt, stream=False, stream_callback=None):
    client = OpenAI(api_key="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", base_url="http://10.2.4.31:32643/v1")
    
    response = client.chat.completions.create(
        model="moyi-chat-v03",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=stream
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

CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def load_cached_transcript(video_id):
    cache_file = os.path.join(CACHE_DIR, f"{video_id}.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    return None

def save_transcript_to_cache(video_id, transcript):
    cache_file = os.path.join(CACHE_DIR, f"{video_id}.json")
    with open(cache_file, 'w') as file:
        json.dump(transcript, file)
        
def main(video_id, zh_response=False):
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
    prompt = create_zh_prompt(transcript_text)
    
    # Send the prompt to OpenAI
    response = send_to_openai(prompt, stream=True, stream_callback=lambda x: print(x, end="", flush=True))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and cache YouTube video transcript.")
    parser.add_argument("video_id", type=str, help="The ID of the YouTube video.")
    args = parser.parse_args()
    
    main(video_id=args.video_id, zh_response=args.zh)