import os
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PodcastSearchResult:
    """Represents a podcast search result."""

    title: str
    author: str
    feed_url: str
    description: str = ""
    artwork_url: str = ""
    language: str = ""
    episode_count: int = 0
    source: str = ""  # "apple", "podcastindex", "fyyd"


class ApplePodcastsSearch:
    """Search Apple Podcasts via iTunes Search API."""

    BASE_URL = "https://itunes.apple.com/search"

    def search(self, query: str, limit: int = 20) -> List[PodcastSearchResult]:
        """Search podcasts using Apple Podcasts (iTunes) API."""
        params = {
            "term": query,
            "media": "podcast",
            "entity": "podcast",
            "limit": min(limit, 50),
        }

        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            feed_url = item.get("feedUrl", "")
            if not feed_url:
                continue

            results.append(
                PodcastSearchResult(
                    title=item.get("collectionName", item.get("trackName", "")),
                    author=item.get("artistName", ""),
                    feed_url=feed_url,
                    description=item.get("description", ""),
                    artwork_url=item.get("artworkUrl600", item.get("artworkUrl100", "")),
                    language=item.get("primaryGenreName", ""),
                    episode_count=item.get("trackCount", 0),
                    source="apple",
                )
            )

        return results


class PodcastIndexSearch:
    """Search PodcastIndex API."""

    BASE_URL = "https://api.podcastindex.org/api/1.0/search/byterm"

    def __init__(self):
        self._api_key = os.environ.get("PODCASTINDEX_API_KEY", "")
        self._api_secret = os.environ.get("PODCASTINDEX_API_SECRET", "")

    def search(self, query: str, limit: int = 20) -> List[PodcastSearchResult]:
        """Search podcasts using PodcastIndex API."""
        if not self._api_key or not self._api_secret:
            return []

        import time
        import hashlib

        # Build auth headers
        auth_date = str(int(time.time()))
        auth_hash = hashlib.sha1(
            f"{self._api_key}{self._api_secret}{auth_date}".encode()
        ).hexdigest()

        headers = {
            "X-Auth-Date": auth_date,
            "X-Auth-Key": self._api_key,
            "X-Auth-Hash": auth_hash,
            "User-Agent": "Podsidian/1.0",
        }

        params = {
            "q": query,
            "max": min(limit, 50),
        }

        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("feeds", []):
                feed_url = item.get("url", "")
                if not feed_url:
                    continue

                results.append(
                    PodcastSearchResult(
                        title=item.get("title", ""),
                        author=item.get("author", ""),
                        feed_url=feed_url,
                        description=item.get("description", ""),
                        artwork_url=item.get("image", item.get("icon", "")),
                        language=item.get("language", ""),
                        episode_count=item.get("episodeCount", 0),
                        source="podcastindex",
                    )
                )

            return results
        except Exception:
            return []


class FyydSearch:
    """Search fyyd (German podcast search)."""

    BASE_URL = "https://api.fyyd.de/0.2/search"

    def search(self, query: str, limit: int = 20) -> List[PodcastSearchResult]:
        """Search podcasts using fyyd API."""
        params = {
            "query": query,
            "limit": min(limit, 50),
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("data", []):
                feed_url = item.get("url", "")
                if not feed_url:
                    continue

                # Get author from owner if available
                author = item.get("author", "")
                if not author and item.get("owner"):
                    author = item.get("owner", {}).get("name", "")

                results.append(
                    PodcastSearchResult(
                        title=item.get("title", ""),
                        author=author,
                        feed_url=feed_url,
                        description=item.get("description", ""),
                        artwork_url=item.get("image", ""),
                        language="de",  # fyyd is primarily German podcasts
                        episode_count=item.get("episodeCount", 0),
                        source="fyyd",
                    )
                )

            return results
        except Exception:
            return []


class PodcastSearcher:
    """Unified podcast search across multiple sources."""

    def __init__(self, sources: Optional[List[str]] = None):
        """Initialize searcher with desired sources.

        Args:
            sources: List of sources to use. Options: ["apple", "podcastindex", "fyyd"]
                    If None, uses all available.
        """
        self.sources = sources or ["apple", "podcastindex", "fyyd"]
        self._searchers = {
            "apple": ApplePodcastsSearch(),
            "podcastindex": PodcastIndexSearch(),
            "fyyd": FyydSearch(),
        }

    def search(self, query: str, limit: int = 20) -> List[PodcastSearchResult]:
        """Search podcasts across all configured sources.

        Args:
            query: Search query string
            limit: Maximum results per source

        Returns:
            Combined and deduplicated list of search results
        """
        all_results = []
        seen_urls = set()

        for source in self.sources:
            if source not in self._searchers:
                continue

            try:
                results = self._searchers[source].search(query, limit)
                for result in results:
                    # Deduplicate by feed URL
                    if result.feed_url.lower() not in seen_urls:
                        seen_urls.add(result.feed_url.lower())
                        all_results.append(result)
            except Exception:
                continue

        return all_results
