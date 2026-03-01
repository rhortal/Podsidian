import os
from pathlib import Path
from typing import Dict, List

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .feed_source import FeedSource


class LocalFeedsSource(FeedSource):
    """Feed source that reads podcast subscriptions from a local TOML file.

    The file should be located at ~/.config/podsidian/feeds.toml and contain
    podcast definitions in the following format:

        [[podcast]]
        title = "My Favorite Podcast"
        author = "Host Name"
        feed_url = "https://example.com/feed.xml"

    Alternative locations can be specified via the PODSIDIAN_FEEDS_PATH
    environment variable.
    """

    DEFAULT_FEEDS_PATH = "~/.config/podsidian/feeds.toml"

    def __init__(self, feeds_path: str = None):
        """Initialize the local feeds source.

        Args:
            feeds_path: Optional path to the feeds TOML file.
                        Defaults to ~/.config/podsidian/feeds.toml
        """
        self._feeds_path = feeds_path or os.environ.get(
            "PODSIDIAN_FEEDS_PATH", self.DEFAULT_FEEDS_PATH
        )

    @property
    def name(self) -> str:
        return "Local Feeds"

    def is_available(self) -> bool:
        """Check if the local feeds file exists and is readable.

        Returns:
            True if the feeds file exists, False otherwise
        """
        path = Path(os.path.expanduser(self._feeds_path))
        return path.exists() and path.is_file()

    def get_subscriptions(self) -> List[Dict[str, str]]:
        """Get podcast subscriptions from the local TOML file.

        Returns:
            List of dictionaries containing title, author, and feed_url

        Raises:
            FileNotFoundError: If the feeds file doesn't exist
            Exception: If there's an error parsing the TOML file
        """
        path = Path(os.path.expanduser(self._feeds_path))

        if not path.exists():
            raise FileNotFoundError(
                f"Local feeds file not found at {path}. "
                f"Create it at {path} with your podcast subscriptions."
            )

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise Exception(f"Error parsing feeds file: {e}")

        subscriptions = []
        for podcast in data.get("podcast", []):
            title = podcast.get("title")
            feed_url = podcast.get("feed_url")
            active = podcast.get("active", True)

            if not title or not feed_url:
                continue

            subscriptions.append(
                {
                    "title": title,
                    "author": podcast.get("author", ""),
                    "feed_url": feed_url,
                    "active": active,
                }
            )

        return subscriptions
