from fasthtml.common import FastHTML, serve
from tennis_interview.search import youtube_search
from tennis_interview.summary import summary
from fastapi.responses import StreamingResponse


app = FastHTML()

@app.get("/")
def home():
    return """
    <h1>YouTube Video Search</h1>
    <form action="/search" method="get">
        <input type="text" name="query" placeholder="Enter search query">
        <input type="submit" value="Search">
    </form>
    """

@app.get("/search")
def search(query: str):
    results = youtube_search(query)
    videos = results.get('items', [])
    
    html = "<h1>Search Results</h1>"
    for video in videos:
        title = video['snippet']['title']
        video_id = video['id']['videoId']
        thumbnail = video['snippet']['thumbnails']['default']['url']
        html += f"""
        <div>
            <h2>{title}</h2>
            <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">
                <img src="{thumbnail}" alt="{title}">
            </a>
            <br>
            <a href="/summary/{video_id}">Get Summary</a>
        </div>
        """
    
    return html

@app.get("/summary/{video_id}")
def get_summary(video_id: str):
    html = "<h1>Video Summary</h1>"
    html += "<div id='summary'></div>"
    html += f"""
    <script>
    function fetchSummary() {{
        fetch('/api/summary/{video_id}')
            .then(response => response.body.getReader())
            .then(reader => {{
                const decoder = new TextDecoder();
                function read() {{
                    reader.read().then(({{'done': done, 'value': value}}) => {{
                        if (done) {{
                            return;
                        }}
                        const text = decoder.decode(value);
                        document.getElementById('summary').innerHTML += text;
                        read();
                    }});
                }}
                read();
            }});
    }}
    fetchSummary();
    </script>
    """
    return html

@app.get("/api/summary/{video_id}")
async def api_summary(video_id: str):
    async def generate():
        for chunk in summary(video_id):
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    return StreamingResponse(generate(), media_type="text/plain")

serve()