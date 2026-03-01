from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class FeedSource(ABC):
    """Abstract base class for podcast feed sources.

    Implementations must provide a way to retrieve podcast subscriptions
    from their respective sources (Apple Podcasts, local file, etc.).
    """

    @abstractmethod
    def get_subscriptions(self) -> List[Dict[str, str]]:
        """Get all podcast subscriptions from the source.

        Returns:
            List of dictionaries containing:
            - title: Podcast title
            - author: Podcast author
            - feed_url: RSS feed URL

        Raises:
            FileNotFoundError: If the source cannot be found
            Exception: For other errors reading from the source
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the feed source is available/accessible.

        Returns:
            True if the source can be accessed, False otherwise
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this feed source.

        Returns:
            Human-readable name for the feed source
        """
        pass


def get_feed_source(source_type: Optional[str] = None) -> FeedSource:
    """Factory function to get the appropriate feed source.

    Args:
        source_type: Type of feed source ('apple_podcasts', 'local', or None for auto-detect)

    Returns:
        FeedSource implementation instance

    Raises:
        ValueError: If an unknown source type is specified
        FileNotFoundError: If the requested source is not available
    """
    if source_type is None or source_type == "apple_podcasts":
        from .apple_podcasts import ApplePodcastsFeedSource

        return ApplePodcastsFeedSource()
    elif source_type == "local":
        from .local_feeds import LocalFeedsSource

        return LocalFeedsSource()
    else:
        raise ValueError(f"Unknown feed source type: {source_type}")
