#!/usr/bin/env python3
"""Minimal supported demo app for PortfolioAgent."""

from fastapi import Form
from fastapi.responses import HTMLResponse

from portfolio_agent import PortfolioAgent, create_app


SAMPLE_TEXT = """
Portfolio Agent Demo

Skills:
- Python
- FastAPI
- LangGraph
- Retrieval augmented generation

Projects:
- Built a reusable portfolio assistant package
- Built API services and developer tooling

Experience:
- Focused on backend systems, platform engineering, and applied AI products
"""


def build_demo_agent() -> PortfolioAgent:
    agent = PortfolioAgent.from_settings()
    agent.add_text(SAMPLE_TEXT, source="demo_profile.txt", document_type="txt")
    return agent


app = create_app(agent=build_demo_agent())


@app.get("/demo", response_class=HTMLResponse)
async def demo_home():
    return """
    <html>
      <body style="font-family: sans-serif; max-width: 720px; margin: 40px auto; line-height: 1.5;">
        <h1>Portfolio Agent Demo</h1>
        <p>This demo exposes the same API documented in the root README.</p>
        <p>Try the HTTP API:</p>
        <pre>curl -X POST http://127.0.0.1:8000/api/v1/query \\
  -H "Content-Type: application/json" \\
  -d '{"query":"What are the core skills?"}'</pre>
        <form method="post" action="/demo/query">
          <label for="query">Query</label><br />
          <input id="query" name="query" style="width: 100%; padding: 8px;" value="What are the core skills?" />
          <button type="submit" style="margin-top: 12px;">Ask</button>
        </form>
      </body>
    </html>
    """


@app.post("/demo/query", response_class=HTMLResponse)
async def demo_query(query: str = Form(...)):
    result = app.state.agent.query(query, session_id="demo")
    sources = "<br />".join(source.get("source") or source.get("id", "") for source in result.sources) or "None"
    return f"""
    <html>
      <body style="font-family: sans-serif; max-width: 720px; margin: 40px auto; line-height: 1.5;">
        <h1>Portfolio Agent Demo</h1>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>Response:</strong> {result.response}</p>
        <p><strong>Sources:</strong><br />{sources}</p>
        <p><a href="/demo">Ask another question</a></p>
      </body>
    </html>
    """
