from fasthtml.common import *
from tennis_interview.search import youtube_search
from tennis_interview.summary import summary as summary_video

hdrs = (MarkdownJS(), HighlightJS(langs=['python', 'javascript', 'html', 'css']), )

app, rt = fast_app(hdrs=hdrs)

@app.get("/")
def home():
    inp = Input(id="new-query", name="query", placeholder="", value="us open 2024 interview")
    add = Form(Group(inp, Button("Search")), hx_get="./search", target_id="res-list", hx_swap="innerHTML")
    res_list = Div(id="res-list")
    return Title("Tennis Interview Reading"), Main(H1("Tennis Interview Search"), add, res_list, cls="container")

@app.get("/search")
def search(query: str):
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

summary_content = ""
summary_generating = False
@threaded
def get_summary_content(response):
    global summary_content
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            summary_content += chunk.choices[0].delta.content
    global summary_generating
    summary_generating = False


def SummaryContent():
    stream_args = {"hx_trigger":"every 0.1s", "hx_swap":"outerHTML", "hx_get":"/summary/content"}
    return Div(summary_content, **stream_args if summary_generating else {}, cls="marked")

@app.get("/summary/content")
def get():
    return SummaryContent()

@app.get("/summary/{video_id}")
def summary(video_id: str):
    global summary_generating
    summary_generating = True
    response = summary_video(video_id)
    get_summary_content(response)
    return Title("Video Summary"), Main(H1("Video Summary"), SummaryContent())

serve()