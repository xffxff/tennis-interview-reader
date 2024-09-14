from dotenv import load_dotenv
from fasthtml.common import *
from markdown import markdown
from starlette.responses import RedirectResponse

from tennis_interview.search import youtube_api_search, duckduckgo_search, serper_api_search
from tennis_interview.summary import summary as summary_video

load_dotenv()

gridlink = Link(
    rel="stylesheet",
    href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css",
    type="text/css",
)
tailwindcss = Script(src="https://cdn.tailwindcss.com")
tailwind_config = Script(
    """
    tailwind.config = {
        corePlugins: {
            preflight: false,
        }
    }
"""
)
css = Style(".card-img-top { width: 256px; height: 180px; object-fit: cover; }")
hdrs = (picolink, gridlink, tailwindcss, tailwind_config, css)

app, rt = fast_app(hdrs=hdrs)

summary_content = {"content": "", "generating": False, "cancelled": False}


def SearchPage(query: Optional[str] = None, search_results: list[Video] = None):
    search = Form(
        Div(
            Search(
                Input(
                    type="search",
                    id="new-query",
                    name="query",
                    placeholder="Search for a tennis interview",
                    value=query,
                ),
            ),
            cls="w-full",
        ),
        Div(
            Select(
                Option("YouTube API", value="youtube", selected=True),
                Option("DuckDuckGo", value="duckduckgo"),
                Option("Serper", value="serper"),
                name="api",
                id="search-api",
                cls="text-sm py-1 text-gray-400"
            ),
            cls="w-1/3 mt-0 mx-auto",
        ),
        hx_get="./search",
        target_id="res-list",
        hx_swap="innerHTML",
        cls="w-full max-w-md flex flex-col",
    )

    div_cls = "flex flex-col items-center justify-center w-full"

    res_list = []
    if search_results:
        for video in search_results:
            res_list.append(VideoCard(video))
    else:
        div_cls += " h-screen"

    res_list = Div(*res_list, id="res-list", cls="row")

    return Title("Tennis Interview Search"), Main(
        Div(
            H1("Tennis Interview Search", cls="text-2xl mb-4"),
            search,
            cls=div_cls,
            id="search-container",
            hx_swap_oob="true",
        ),
        res_list,
        cls="container",
    )


@rt("/")
def get():
    return SearchPage()


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
def get(query: str, api: str, session):
    max_results = 12
    if api == "youtube":
        results = youtube_api_search(query, max_results=max_results)
    elif api == "duckduckgo":
        results = duckduckgo_search(query, max_results=max_results)
    elif api == "serper":
        results = serper_api_search(query, max_results=max_results)
    session["last_query"] = query
    return SearchPage(query,results)


@threaded
def get_summary_content(response):
    for chunk in response:
        if summary_content["cancelled"]:
            break
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
    summary_content["cancelled"] = False
    response = summary_video(video_id)
    get_summary_content(response)
    return Title("Video Summary"), Main(
        SummaryContent(),
        A(
            "Back to Search Results",
            href=f"/back-to-search",
            cls="mt-4 inline-block",
        ),
        cls="container",
    )


@rt("/back-to-search")
def get(session):
    summary_content["generating"] = False
    summary_content["content"] = ""
    summary_content["cancelled"] = True
    print("cancelled", summary_content["cancelled"])
    last_query = session.get("last_query", "")
    return RedirectResponse(url=f"/search?query={last_query}")


serve()
