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
hidden_api_select = True


def api_select(hidden=False):
    cls = "text-sm py-1 text-gray-400"
    if hidden:
        cls += " hidden"
    return Select(
        Option("YouTube API", value="youtube"),
        Option("DuckDuckGo", value="duckduckgo"),
        Option("Serper", value="serper"),
        name="api",
        id="search-api",
        hx_swap_oob="true",
        cls=cls,
    )

def SearchPage(session, search_results: list[Video] = None):
    search = Form(
        Div(
            Div(
                Search(
                    Input(
                        type="search",
                        id="new-query",
                        name="query",
                        placeholder="Search for a tennis interview",
                        value=session.get("last_query", ""),
                        cls="w-full !mb-0",  
                    ),
                    cls="flex-grow",  
                ),
                Button(
                    cls="ml-2 h-10 w-10 rounded-full cursor-pointer flex items-center justify-center bg-zinc-900 flex-shrink-0",  # Add flex-shrink-0 to prevent button from shrinking
                    hx_get="./api-select",
                ),
                cls="flex items-center w-full",
            ),
            cls="w-full max-w-3xl",  
        ),
        Div(
            api_select(hidden=True),
            id="api-select-container",
            cls="w-1/3 mt-2 mx-auto",
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
def get(session):
    session["last_query"] = ""
    return SearchPage(session)


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
    session["last_api"] = api  
    return SearchPage(session, results)


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
    last_api = session.get("last_api", "youtube")  
    return RedirectResponse(url=f"/search?query={last_query}&api={last_api}")


# 添加一个新的路由来处理 API 选择的显示/隐藏
@rt("/api-select")
def get():
    global hidden_api_select
    hidden_api_select = not hidden_api_select
    return api_select(hidden=hidden_api_select)


serve()
