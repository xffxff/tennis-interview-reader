from dotenv import load_dotenv
from fasthtml.common import *
from markdown import markdown
from starlette.responses import RedirectResponse

from tennis_interview.search import (
    duckduckgo_search,
    serper_api_search,
    youtube_api_search,
)
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
                        cls="w-full",
                    ),
                    cls="flex-grow mr-2",
                ),
                Button(
                    NotStr(
                        """<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>"""
                    ),
                    cls="py-2 px-3 border-none rounded-full bg-black hover:bg-gray-700 transition-colors duration-200",
                    hx_get="./api-select",
                    type="button",
                ),
                cls="flex items-center w-full",
            ),
            Div(
                api_select(hidden=True),
                id="api-select-container",
                cls="w-1/3 mt-2 mx-auto",
            ),
            cls="w-full max-w-3xl flex flex-col",
        ),
        hx_get="./search",
        target_id="res-list",
        hx_swap="innerHTML",
        cls="w-full max-w-xl",
    )

    div_cls = "flex flex-col items-center justify-start w-full mb-4"

    res_list = []
    if search_results:
        for video in search_results:
            res_list.append(VideoCard(video))
        div_cls += " pt-16"
    else:
        div_cls += " pt-64"

    res_list = Div(*res_list, id="res-list", cls="row")

    return Title("Tennis Interview Search"), Main(
        Div(
            H1("Video Reader", cls="text-6xl mb-8 font-serif font-thin"),
            search,
            cls=div_cls,
            id="search-container",
        ),
        res_list,
        cls="container",
        id="search-main",
        hx_swap_oob="true",
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
    max_results = 8
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


# 添加一个新的路由来处理 API 选择的示/隐藏
@rt("/api-select")
def get():
    global hidden_api_select
    hidden_api_select = not hidden_api_select
    return api_select(hidden=hidden_api_select)


serve()
