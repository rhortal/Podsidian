import os
import re
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import tomllib
except ImportError:
    import tomli as tomllib


@dataclass
class PodcastEntry:
    """Represents a podcast entry in the feeds config."""

    title: str
    feed_url: str
    author: str = ""
    description: str = ""
    active: bool = True
    added_at: str = ""


class PodcastManager:
    """Manages podcast subscriptions stored in local TOML file."""

    DEFAULT_FEEDS_PATH = "~/.config/podsidian/feeds.toml"

    def __init__(self, feeds_path: Optional[str] = None):
        """Initialize the podcast manager.

        Args:
            feeds_path: Optional path to the feeds TOML file.
        """
        self._feeds_path = feeds_path or os.environ.get(
            "PODSIDIAN_FEEDS_PATH", self.DEFAULT_FEEDS_PATH
        )

    @property
    def feeds_path(self) -> Path:
        """Get the Path object for the feeds file."""
        return Path(os.path.expanduser(self._feeds_path))

    def load_podcasts(self) -> List[PodcastEntry]:
        """Load all podcasts from the feeds file.

        Returns:
            List of PodcastEntry objects

        Raises:
            FileNotFoundError: If the feeds file doesn't exist
        """
        if not self.feeds_path.exists():
            raise FileNotFoundError(f"Feeds file not found at {self.feeds_path}")

        with open(self.feeds_path, "rb") as f:
            data = tomllib.load(f)

        podcasts = []
        for item in data.get("podcast", []):
            podcasts.append(
                PodcastEntry(
                    title=item.get("title", ""),
                    feed_url=item.get("feed_url", ""),
                    author=item.get("author", ""),
                    description=item.get("description", ""),
                    active=item.get("active", True),
                    added_at=item.get("added_at", ""),
                )
            )

        return podcasts

    def save_podcasts(self, podcasts: List[PodcastEntry]) -> None:
        """Save podcasts to the feeds file.

        Args:
            podcasts: List of PodcastEntry objects to save
        """
        # Ensure directory exists
        self.feeds_path.parent.mkdir(parents=True, exist_ok=True)

        # Build TOML content
        lines = ["# Podsidian Podcast Subscriptions\n"]
        lines.append(f"# Generated: {datetime.now().isoformat()}\n\n")

        for podcast in podcasts:
            lines.append("[[podcast]]\n")
            lines.append(f'title = "{self._escape_toml(podcast.title)}"\n')
            lines.append(f'feed_url = "{self._escape_toml(podcast.feed_url)}"\n')
            if podcast.author:
                lines.append(f'author = "{self._escape_toml(podcast.author)}"\n')
            if podcast.description:
                lines.append(f'description = """{podcast.description}"""\n')
            if not podcast.active:
                lines.append("active = false\n")
            if podcast.added_at:
                lines.append(f'added_at = "{podcast.added_at}"\n')
            lines.append("\n")

        with open(self.feeds_path, "w") as f:
            f.writelines(lines)

    def _escape_toml(self, s: str) -> str:
        """Escape a string for TOML."""
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def add_podcast(self, podcast: PodcastEntry) -> None:
        """Add a podcast to the feeds file.

        Args:
            podcast: PodcastEntry to add
        """
        try:
            podcasts = self.load_podcasts()
        except FileNotFoundError:
            podcasts = []

        # Check for duplicates
        for existing in podcasts:
            if existing.feed_url.lower() == podcast.feed_url.lower():
                raise ValueError(f"Podcast already exists: {podcast.feed_url}")

        if not podcast.added_at:
            podcast.added_at = datetime.now().isoformat()

        podcasts.append(podcast)
        self.save_podcasts(podcasts)

    def remove_podcast(self, feed_url: str) -> bool:
        """Remove a podcast by feed URL.

        Args:
            feed_url: Feed URL of the podcast to remove

        Returns:
            True if removed, False if not found
        """
        podcasts = self.load_podcasts()
        original_count = len(podcasts)
        podcasts = [p for p in podcasts if p.feed_url.lower() != feed_url.lower()]

        if len(podcasts) < original_count:
            self.save_podcasts(podcasts)
            return True
        return False

    def toggle_podcast(self, feed_url: str) -> Optional[bool]:
        """Toggle a podcast's active status.

        Args:
            feed_url: Feed URL of the podcast to toggle

        Returns:
            New active status, or None if not found
        """
        podcasts = self.load_podcasts()

        for podcast in podcasts:
            if podcast.feed_url.lower() == feed_url.lower():
                podcast.active = not podcast.active
                self.save_podcasts(podcasts)
                return podcast.active

        return None

    def update_podcast(self, feed_url: str, updates: Dict[str, str]) -> bool:
        """Update a podcast's details.

        Args:
            feed_url: Feed URL of the podcast to update
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        podcasts = self.load_podcasts()

        for podcast in podcasts:
            if podcast.feed_url.lower() == feed_url.lower():
                for key, value in updates.items():
                    if hasattr(podcast, key):
                        setattr(podcast, key, value)
                self.save_podcasts(podcasts)
                return True

        return False

    def get_podcast(self, feed_url: str) -> Optional[PodcastEntry]:
        """Get a podcast by feed URL.

        Args:
            feed_url: Feed URL to look up

        Returns:
            PodcastEntry if found, None otherwise
        """
        podcasts = self.load_podcasts()
        for podcast in podcasts:
            if podcast.feed_url.lower() == feed_url.lower():
                return podcast
        return None
