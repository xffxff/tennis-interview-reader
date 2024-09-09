from dotenv import load_dotenv
from fasthtml.common import *
from markdown import markdown

from tennis_interview.search import serper_api_search as video_search
from tennis_interview.summary import summary as summary_video

load_dotenv()

gridlink = Link(
    rel="stylesheet",
    href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css",
    type="text/css",
)
css = Style(".card-img-top { width: 256px; height: 180px; object-fit: cover; }")
hdrs = (picolink, gridlink, css)

app, rt = fast_app(hdrs=hdrs)

summary_content = {"content": "", "generating": False}


@rt("/")
def get():
    inp = Input(
        id="new-query", name="query", placeholder="", value="us open 2024 interview"
    )
    add = Form(
        Group(inp, Button("Search")),
        hx_get="./search",
        target_id="res-list",
        hx_swap="innerHTML",
    )
    res_list = Div(id="res-list", cls="row")
    return Title("Tennis Interview Reading"), Main(
        H1("Tennis Interview Search"), add, res_list, cls="container"
    )


def VideoCard(video: Video):
    grid_cls = "box col-xs-12 col-sm-6 col-md-4 col-lg-3"
    title = video.title
    thumbnail = video.thumbnails.medium
    video_id = video.id
    return Div(
        Card(
            A(Img(src=thumbnail, cls="card-img-top"), href=f"/summary/{video_id}"),
            Div(P(B(title), cls="card-text"), cls="card-body"),
        ),
        id=f"video-{video_id}",
        cls=grid_cls,
    )


@rt("/search")
def get(query: str):
    results = video_search(query, max_results=12)
    res_list = []
    for video in results:
        res_list.append(VideoCard(video))
    return res_list


@threaded
def get_summary_content(response):
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            summary_content["content"] += chunk.choices[0].delta.content
    summary_content["generating"] = False


def SummaryContent():
    stream_args = {
        "hx_trigger": "every 0.2s",
        "hx_get": "/summary/content",
        "hx_swap": "outerHTML",
    }
    generating = "generating" in summary_content and summary_content["generating"]
    return Div(
        NotStr(markdown(summary_content["content"])),
        **stream_args if generating else {},
    )


@rt("/summary/content")
def get():
    return SummaryContent()


@rt("/summary/{video_id}")
def get(video_id: str):
    summary_content["generating"] = True
    summary_content["content"] = ""
    response = summary_video(video_id)
    get_summary_content(response)
    return Title("Video Summary"), Main(SummaryContent(), cls="container")


serve()
