import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path to avoid importing through podsidian/__init__.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules directly
from podsidian.feed_source import FeedSource, get_feed_source
from podsidian.local_feeds import LocalFeedsSource


class TestFeedSourceProtocol:
    """Tests for the FeedSource abstract base class."""

    def test_feed_source_is_abc(self):
        """Test that FeedSource cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FeedSource()


class TestLocalFeedsSource:
    """Tests for LocalFeedsSource implementation."""

    def test_default_path(self):
        """Test default feeds path configuration."""
        source = LocalFeedsSource()
        assert source.DEFAULT_FEEDS_PATH == "~/.config/podsidian/feeds.toml"

    def test_custom_path(self):
        """Test custom feeds path."""
        source = LocalFeedsSource("/custom/path/feeds.toml")
        assert source._feeds_path == "/custom/path/feeds.toml"

    def test_env_var_override(self):
        """Test environment variable override."""
        os.environ["PODSIDIAN_FEEDS_PATH"] = "/env/path/feeds.toml"
        try:
            source = LocalFeedsSource()
            assert source._feeds_path == "/env/path/feeds.toml"
        finally:
            del os.environ["PODSIDIAN_FEEDS_PATH"]

    def test_is_available_when_file_exists(self):
        """Test is_available returns True when file exists."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[[podcast]]\ntitle = "Test"\nfeed_url = "http://example.com"')
            temp_path = f.name

        try:
            source = LocalFeedsSource(temp_path)
            assert source.is_available() is True
        finally:
            os.unlink(temp_path)

    def test_is_available_when_file_not_exists(self):
        """Test is_available returns False when file doesn't exist."""
        source = LocalFeedsSource("/nonexistent/path.toml")
        assert source.is_available() is False

    def test_get_subscriptions_parses_toml(self):
        """Test parsing valid TOML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""[[podcast]]
title = "Test Podcast"
author = "Test Author"
feed_url = "https://example.com/feed.xml"
""")
            temp_path = f.name

        try:
            source = LocalFeedsSource(temp_path)
            subs = source.get_subscriptions()
            assert len(subs) == 1
            assert subs[0]["title"] == "Test Podcast"
            assert subs[0]["author"] == "Test Author"
            assert subs[0]["feed_url"] == "https://example.com/feed.xml"
        finally:
            os.unlink(temp_path)

    def test_get_subscriptions_multiple_podcasts(self):
        """Test parsing multiple podcasts from TOML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""[[podcast]]
title = "Podcast One"
author = "Author One"
feed_url = "https://example.com/feed1.xml"

[[podcast]]
title = "Podcast Two"
author = "Author Two"
feed_url = "https://example.com/feed2.xml"
""")
            temp_path = f.name

        try:
            source = LocalFeedsSource(temp_path)
            subs = source.get_subscriptions()
            assert len(subs) == 2
            assert subs[0]["title"] == "Podcast One"
            assert subs[1]["title"] == "Podcast Two"
        finally:
            os.unlink(temp_path)

    def test_get_subscriptions_skips_invalid_entries(self):
        """Test that invalid entries are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("""[[podcast]]
title = "Valid Podcast"
feed_url = "https://example.com/feed.xml"

[[podcast]]
title = "Missing URL"

[[podcast]]
feed_url = "https://example.com/feed2.xml"
""")
            temp_path = f.name

        try:
            source = LocalFeedsSource(temp_path)
            subs = source.get_subscriptions()
            assert len(subs) == 1
            assert subs[0]["title"] == "Valid Podcast"
        finally:
            os.unlink(temp_path)

    def test_get_subscriptions_file_not_found(self):
        """Test error when file doesn't exist."""
        source = LocalFeedsSource("/nonexistent/path.toml")
        with pytest.raises(FileNotFoundError):
            source.get_subscriptions()

    def test_get_subscriptions_invalid_toml(self):
        """Test error handling for invalid TOML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("invalid toml content {")
            temp_path = f.name

        try:
            source = LocalFeedsSource(temp_path)
            with pytest.raises(Exception):
                source.get_subscriptions()
        finally:
            os.unlink(temp_path)

    def test_name_property(self):
        """Test name property returns correct value."""
        source = LocalFeedsSource()
        assert source.name == "Local Feeds"


class TestGetFeedSourceFactory:
    """Tests for the get_feed_source factory function."""

    def test_get_apple_podcasts_source(self):
        """Test getting Apple Podcasts source."""
        from podsidian.apple_podcasts import ApplePodcastsFeedSource

        source = get_feed_source("apple_podcasts")
        assert isinstance(source, ApplePodcastsFeedSource)

    def test_get_local_source(self):
        """Test getting local source."""
        source = get_feed_source("local")
        assert isinstance(source, LocalFeedsSource)

    def test_get_source_none_defaults_to_apple(self):
        """Test None defaults to apple_podcasts."""
        source = get_feed_source(None)
        # Should return Apple Podcasts (or raise if not available)
        # We just check it doesn't raise here
        assert source is not None

    def test_get_source_unknown_type_raises(self):
        """Test unknown source type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_feed_source("unknown_type")
        assert "Unknown feed source type" in str(exc_info.value)


class TestApplePodcastsFeedSource:
    """Tests for ApplePodcastsFeedSource implementation."""

    def test_apple_podcasts_source_class(self):
        """Test ApplePodcastsFeedSource can be imported and is a FeedSource."""
        from podsidian.apple_podcasts import ApplePodcastsFeedSource

        assert issubclass(ApplePodcastsFeedSource, FeedSource)

    def test_name_property(self):
        """Test name property returns Apple Podcasts."""
        from podsidian.apple_podcasts import ApplePodcastsFeedSource

        source = ApplePodcastsFeedSource()
        assert source.name == "Apple Podcasts"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
