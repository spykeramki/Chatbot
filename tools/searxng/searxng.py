import requests
from typing import List, Dict

class SearchResults(Dict):
    results: List[Dict[str, str]]

SEARXNG_URL = "http://localhost:8080"

def web_search_tool(query: str) -> SearchResults:
    """Search the web using the local SearXNG instance."""
    response = requests.get(
        f"{SEARXNG_URL}/search",
        params={
            "q": query,
            "format": "json",
        },
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        search_results: SearchResults = {"results": []}
        for result in data.get("results", []):
            search_results["results"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")
            })
        return search_results
    return 'failed to fetch search results'
