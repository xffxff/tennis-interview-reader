from fasthtml.common import *
from tennis_interview.search import youtube_search
from tennis_interview.summary import summary as summary_video
from markdown import markdown

hdrs = (MarkdownJS(), HighlightJS(langs=['python', 'javascript', 'html', 'css']), )

app, rt = fast_app(hdrs=hdrs)

summary_content = {
    "content": "",
    "generating": False
}

@rt("/")
def get():
    inp = Input(id="new-query", name="query", placeholder="", value="us open 2024 interview")
    add = Form(Group(inp, Button("Search")), hx_get="./search", target_id="res-list", hx_swap="innerHTML")
    res_list = Div(id="res-list")
    return Title("Tennis Interview Reading"), Main(H1("Tennis Interview Search"), add, res_list, cls="container")

@rt("/search")
def get(query: str):
    results = youtube_search(query)
    videos = results.get('items', [])
    res_list = []
    for video in videos:
        title = video.get('snippet', {}).get('title')
        video_id = video.get('id', {}).get('videoId')
        thumbnail = video.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url')
        div = Div(
            A(H2(title), href=f"/summary/{video_id}"),
            A(Img(src=thumbnail), href=f"https://www.youtube.com/watch?v={video_id}"),
        )
        res_list.append(div)
    clear_input = Input(id="new-query", name="query", hx_swap_oob="true")
    return Div(*res_list), clear_input

@threaded
def get_summary_content(response):
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            summary_content["content"] += chunk.choices[0].delta.content
    summary_content["generating"] = False

def SummaryContent():
    stream_args = {"hx_trigger":"every 0.2s", "hx_get":"/summary/content", "hx_swap":"outerHTML"}
    print(summary_content)
    generating = 'generating' in summary_content and summary_content['generating']
    print(generating)
    return Div(NotStr(markdown(summary_content["content"])), **stream_args if generating else {})

@rt("/summary/content")
def get():
    return SummaryContent()

@rt("/summary/{video_id}")
def get(video_id: str):
    summary_content["generating"] = True
    summary_content["content"] = ""
    response = summary_video(video_id)
    get_summary_content(response)
    return Title("Video Summary"), Main(SummaryContent())

serve()