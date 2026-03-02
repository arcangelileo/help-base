"""Embeddable search widget router — serves iframe endpoint and JS snippet."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.models.article import Article
from helpbase.models.helpcenter import HelpCenter
from helpbase.services.search import search_articles

router = APIRouter(prefix="/widget", tags=["widget"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/{slug}/embed.js", response_class=Response)
async def widget_js(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Serve the embeddable JavaScript snippet that creates a search widget."""
    hc_result = await db.execute(
        select(HelpCenter).where(HelpCenter.slug == slug)
    )
    hc = hc_result.scalar_one_or_none()
    if not hc:
        return Response("// Help center not found", media_type="application/javascript")

    base_url = settings.base_url.rstrip("/")
    primary_color = hc.primary_color or "#4F46E5"
    # Escape HC name for safe JS string insertion
    safe_name = hc.name.replace("\\", "\\\\").replace("'", "\\'").replace("<", "\\x3c").replace(">", "\\x3e").replace("\n", " ").replace("\r", "")

    js_code = f"""
(function() {{
  'use strict';

  if (window.__helpbase_widget_loaded) return;
  window.__helpbase_widget_loaded = true;

  var SLUG = '{slug}';
  var BASE_URL = '{base_url}';
  var PRIMARY_COLOR = '{primary_color}';
  var HC_NAME = '{safe_name}';

  // Create widget container
  var container = document.createElement('div');
  container.id = 'helpbase-widget-container';
  container.innerHTML = '';
  document.body.appendChild(container);

  // Inject styles
  var style = document.createElement('style');
  style.textContent = `
    #helpbase-widget-btn {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: ${{PRIMARY_COLOR}};
      color: #fff;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(0,0,0,0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99998;
      transition: transform 0.2s, box-shadow 0.2s;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    #helpbase-widget-btn:hover {{
      transform: scale(1.08);
      box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }}
    #helpbase-widget-btn svg {{
      width: 24px;
      height: 24px;
    }}
    #helpbase-widget-panel {{
      position: fixed;
      bottom: 96px;
      right: 24px;
      width: 380px;
      max-width: calc(100vw - 48px);
      max-height: 520px;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
      z-index: 99999;
      overflow: hidden;
      display: none;
      flex-direction: column;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      animation: helpbase-slide-up 0.25s ease-out;
    }}
    @keyframes helpbase-slide-up {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    #helpbase-widget-panel.open {{
      display: flex;
    }}
    .helpbase-header {{
      padding: 16px 20px;
      background: ${{PRIMARY_COLOR}};
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .helpbase-header h3 {{
      margin: 0;
      font-size: 15px;
      font-weight: 600;
    }}
    .helpbase-header button {{
      background: none;
      border: none;
      color: #fff;
      cursor: pointer;
      padding: 4px;
      opacity: 0.8;
      transition: opacity 0.15s;
    }}
    .helpbase-header button:hover {{
      opacity: 1;
    }}
    .helpbase-search {{
      padding: 12px 16px;
      border-bottom: 1px solid #e5e7eb;
    }}
    .helpbase-search input {{
      width: 100%;
      padding: 10px 12px 10px 36px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
      box-sizing: border-box;
      background: #f9fafb;
    }}
    .helpbase-search input:focus {{
      border-color: ${{PRIMARY_COLOR}};
      box-shadow: 0 0 0 3px ${{PRIMARY_COLOR}}22;
      background: #fff;
    }}
    .helpbase-search-wrap {{
      position: relative;
    }}
    .helpbase-search-wrap svg {{
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      width: 16px;
      height: 16px;
      color: #9ca3af;
    }}
    .helpbase-results {{
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;
      min-height: 120px;
      max-height: 360px;
    }}
    .helpbase-result-item {{
      display: block;
      padding: 10px 20px;
      text-decoration: none;
      color: #111827;
      transition: background 0.1s;
      border-bottom: 1px solid #f3f4f6;
    }}
    .helpbase-result-item:hover {{
      background: #f9fafb;
    }}
    .helpbase-result-item h4 {{
      margin: 0 0 4px 0;
      font-size: 14px;
      font-weight: 600;
      color: #111827;
    }}
    .helpbase-result-item p {{
      margin: 0;
      font-size: 12px;
      color: #6b7280;
      line-height: 1.5;
    }}
    .helpbase-result-item p mark {{
      background: ${{PRIMARY_COLOR}}22;
      color: ${{PRIMARY_COLOR}};
      padding: 0 2px;
      border-radius: 2px;
    }}
    .helpbase-empty {{
      padding: 32px 20px;
      text-align: center;
      color: #6b7280;
      font-size: 13px;
    }}
    .helpbase-empty svg {{
      width: 40px;
      height: 40px;
      color: #d1d5db;
      margin: 0 auto 12px;
    }}
    .helpbase-footer {{
      padding: 10px 16px;
      border-top: 1px solid #e5e7eb;
      text-align: center;
    }}
    .helpbase-footer a {{
      font-size: 11px;
      color: #9ca3af;
      text-decoration: none;
      transition: color 0.15s;
    }}
    .helpbase-footer a:hover {{
      color: #6b7280;
    }}
    .helpbase-loading {{
      padding: 24px;
      text-align: center;
      color: #9ca3af;
      font-size: 13px;
    }}
  `;
  document.head.appendChild(style);

  // Create floating button
  var btn = document.createElement('button');
  btn.id = 'helpbase-widget-btn';
  btn.setAttribute('aria-label', 'Search help articles');
  btn.innerHTML = '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
  container.appendChild(btn);

  // Create panel
  var panel = document.createElement('div');
  panel.id = 'helpbase-widget-panel';
  panel.innerHTML = `
    <div class="helpbase-header">
      <h3>${{HC_NAME}} Help</h3>
      <button onclick="document.getElementById('helpbase-widget-panel').classList.remove('open')" aria-label="Close">
        <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="helpbase-search">
      <div class="helpbase-search-wrap">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <input type="text" id="helpbase-search-input" placeholder="Search for help..." autocomplete="off" />
      </div>
    </div>
    <div class="helpbase-results" id="helpbase-results">
      <div class="helpbase-empty">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
        <p>Type to search help articles</p>
      </div>
    </div>
    <div class="helpbase-footer">
      <a href="${{BASE_URL}}" target="_blank">Powered by HelpBase</a>
    </div>
  `;
  container.appendChild(panel);

  // Toggle panel
  btn.addEventListener('click', function() {{
    var isOpen = panel.classList.contains('open');
    if (isOpen) {{
      panel.classList.remove('open');
    }} else {{
      panel.classList.add('open');
      document.getElementById('helpbase-search-input').focus();
    }}
  }});

  // Close on Escape
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
      panel.classList.remove('open');
    }}
  }});

  // Search logic
  var debounceTimer;
  var searchInput = document.getElementById('helpbase-search-input');
  var resultsDiv = document.getElementById('helpbase-results');

  searchInput.addEventListener('input', function() {{
    clearTimeout(debounceTimer);
    var q = searchInput.value.trim();
    if (!q) {{
      resultsDiv.innerHTML = '<div class="helpbase-empty"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg><p>Type to search help articles</p></div>';
      return;
    }}
    debounceTimer = setTimeout(function() {{
      resultsDiv.innerHTML = '<div class="helpbase-loading">Searching...</div>';
      fetch(BASE_URL + '/widget/' + SLUG + '/search?q=' + encodeURIComponent(q))
        .then(function(r) {{ return r.json(); }})
        .then(function(data) {{
          if (!data.results || data.results.length === 0) {{
            resultsDiv.innerHTML = '<div class="helpbase-empty"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg><p>No results found for &ldquo;' + escapeHtml(q) + '&rdquo;</p></div>';
            return;
          }}
          var html = '';
          data.results.forEach(function(r) {{
            html += '<a class="helpbase-result-item" href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener noreferrer">';
            html += '<h4>' + escapeHtml(r.title) + '</h4>';
            if (r.snippet) {{ html += '<p>' + sanitizeSnippet(r.snippet) + '</p>'; }}
            html += '</a>';
          }});
          resultsDiv.innerHTML = html;
        }})
        .catch(function() {{
          resultsDiv.innerHTML = '<div class="helpbase-empty"><p>Search unavailable. Please try again.</p></div>';
        }});
    }}, 300);
  }});

  function escapeHtml(text) {{
    var d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }}

  function sanitizeSnippet(html) {{
    // Only allow <mark> tags from FTS5 snippet() — strip everything else
    return html.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/&lt;mark&gt;/g,'<mark>').replace(/&lt;\\/mark&gt;/g,'</mark>');
  }}
}})();
"""

    return Response(
        content=js_code.strip(),
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=300",
        },
    )


@router.get("/{slug}/search", response_class=JSONResponse)
async def widget_search(
    slug: str,
    q: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """JSON search endpoint for the widget — CORS-enabled."""
    hc_result = await db.execute(
        select(HelpCenter).where(HelpCenter.slug == slug)
    )
    hc = hc_result.scalar_one_or_none()
    if not hc:
        return JSONResponse(
            {"error": "Help center not found", "results": []},
            status_code=404,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    results = []
    if q.strip():
        raw_results = await search_articles(db, hc.id, q.strip(), limit=8)
        base_url = settings.base_url.rstrip("/")
        for r in raw_results:
            art_result = await db.execute(
                select(Article.slug).where(Article.id == r["article_id"])
            )
            art_slug = art_result.scalar_one_or_none()
            r["url"] = f"{base_url}/h/{slug}/articles/{art_slug or r['article_id']}?q={q.strip()}"
        results = raw_results

    return JSONResponse(
        {"results": results, "query": q},
        headers={"Access-Control-Allow-Origin": "*"},
    )


@router.options("/{slug}/search")
async def widget_search_options(slug: str):
    """Handle CORS preflight for widget search."""
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )
