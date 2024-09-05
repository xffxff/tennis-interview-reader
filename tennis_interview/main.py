import argparse
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import json
import os

def create_en_prompt(transcript_text):
    prompt = f"""
**Prompt: Summary of YouTube Interview Transcript**

Objective:
The goal is to summarize the key content and main ideas discussed in a YouTube video interview transcript. The summary should be concise, capturing the essence and pivotal points of the interview, making it easy for someone who hasn’t seen the video to understand its primary takeaways.

Instructions:

1. **Introduction**:
   - Begin with a brief introduction that includes the names of the interviewer and interviewee, the date of the interview, and the primary topic or purpose of the interview.

2. **Summary**:
   - Provide a concise summary of the interview, highlighting the most important discussions and insights shared. Aim to capture the essence of the conversation in 2-3 paragraphs.

3. **Key Points**:
   - List 5-7 key points or topics that were discussed during the interview. These should be the most notable and impactful aspects of the conversation.

Here is the transcript of the interview for reference:
{transcript_text}
"""
    return prompt

def create_zh_prompt(transcript_text):
    prompt = f"""
**任务：YouTube采访视频的文字记录总结**

目标：
目标是总结一个YouTube视频采访的文字记录的关键内容和主要观点。总结应简明扼要，捕捉采访的精髓和关键点，使没有观看视频的人也能理解其主要内容。

说明：

1. **简介**：
   - 以简短的介绍开始，包括采访者和被采访者的名字、采访日期以及采访的主要主题或目的。

2. **总结**：
   - 提供一个简明的采访总结，突出最重要的讨论和分享的观点。目标是在2-3个段落内捕捉对话的精髓。

3. **关键点**：
   - 列出采访中讨论的5-7个关键点或话题。这些应是对话中最显著和最具影响力的方面。

这是采访的文字记录供参考：
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
    transcript = load_cached_transcript(video_id)
    if transcript is None:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        save_transcript_to_cache(video_id, transcript)
    
    # Format the transcript for the prompt
    transcript_text = "\n".join([f"- {entry['text']}" for entry in transcript])
    
    # Create the prompt
    if zh_response:
        prompt = create_zh_prompt(transcript_text)
    else:
        prompt = create_en_prompt(transcript_text)
    
    # Send the prompt to OpenAI
    response = send_to_openai(prompt, stream=True, stream_callback=lambda x: print(x, end="", flush=True))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and cache YouTube video transcript.")
    parser.add_argument("video_id", type=str, help="The ID of the YouTube video.")
    parser.add_argument("--zh", action="store_true", help="Use Chinese prompt.")
    args = parser.parse_args()
    
    main(video_id=args.video_id, zh_response=args.zh)