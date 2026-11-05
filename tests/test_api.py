import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from flow.api import Handler, headline, places


def test_headline_from_url_slug() -> None:
    url = "https://x.com/2026/09/04/israeli-release-strait-of-hormuz-shipping-mideast-news/"
    assert headline(url) == "Israeli release strait of hormuz shipping mideast news"
    assert headline("https://www.x.com/article?id=1") == "x.com"


def test_copilot_place_names_resolve_to_map_nodes() -> None:
    found = {p["id"] for p in places(["Bab al\u2011Mandeb", "Sikka port", "India", "Hormuz"])}
    assert found == {"bab_el_mandeb", "sikka", "hormuz"}


def test_api_endpoints() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        d = json.load(urlopen(f"{base}/api/dashboard"))
        assert len(d["chokepoints"]) == 5 and d["lanes"] and d["facilities"]
        s = json.load(urlopen(f"{base}/api/sim?chokepoints=hormuz&months=6"))
        assert s["commodities"][0]["lost_mmt"] > 0
        assert isinstance(json.load(urlopen(f"{base}/api/news?limit=5")), list)
        with pytest.raises(HTTPError) as bad:
            urlopen(f"{base}/api/sim?chokepoints=atlantis")
        assert bad.value.code == 400
        with pytest.raises(HTTPError) as empty:
            urlopen(Request(f"{base}/api/ask", data=b'{"question": ""}', method="POST"))
        assert empty.value.code == 400
    finally:
        server.shutdown()
