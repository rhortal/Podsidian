# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Podsidian is a sophisticated podcast content management system that bridges podcast RSS feeds with Obsidian knowledge management. It processes podcast episodes through AI-powered transcription, semantic search, and exports structured markdown files to Obsidian vaults.

## Feed Source System

Podsidian supports multiple feed source implementations via a pluggable architecture:

### Available Sources
- **apple_podcasts**: Read subscriptions from Apple Podcasts app (default)
- **local**: Read subscriptions from a local TOML file

### Configuration
In `~/.config/podsidian/config.toml`:
```toml
[feed_source]
type = "local"  # or "apple_podcasts"
local_feeds_path = "~/.config/podsidian/feeds.toml"
```

### Local Feeds Format
Create `~/.config/podsidian/feeds.toml`:
```toml
[[podcast]]
title = "My Favorite Podcast"
author = "Host Name"
feed_url = "https://example.com/feed.xml"
```

### Adding New Feed Sources
1. Create a new module (e.g., `podsidian/my_source.py`)
2. Implement the `FeedSource` abstract base class from `feed_source.py`
3. Register in the `get_feed_source()` factory function in `feed_source.py`

See `podsidian/local_feeds.py` and `podsidian/apple_podcasts.py` for examples.

## Podcast Management CLI

New commands for managing local podcasts:
```bash
# Search for podcasts (Apple Podcasts, PodcastIndex, fyyd)
podsidian podcasts search "query"
podsidian podcasts list
podsidian podcasts add <feed_url> -t "Title" -a "Author"
podsidian podcasts toggle <feed_url>
podsidian podcasts remove <feed_url>
podsidian podcasts manage  # Interactive TUI
```

### Key Components

- **FeedSource** (`feed_source.py`): Abstract base class for feed sources
- **LocalFeedsSource** (`local_feeds.py`): Local TOML file feed source
- **ApplePodcastsFeedSource** (`apple_podcasts.py`): Apple Podcasts app feed source
- **PodcastManager** (`podcast_manager.py`): Manage local podcast feeds
- **PodcastSearcher** (`podcast_search.py`): Search podcasts via multiple APIs
- **PodcastProcessor** (`core.py`): Main processing engine that orchestrates the entire pipeline
- **CLI Interface** (`cli.py`): Click-based command system with rich progress indicators
- **Database Models** (`models.py`): SQLAlchemy schema for Podcasts and Episodes
- **MCP Server** (`stdio_server.py`): Model Context Protocol implementation for AI agent integration
- **Configuration System** (`config.py`): TOML-based config management with validation

## Tech Stack

- **Language**: Python 3.9+
- **Build System**: Hatch with UV package manager
- **Database**: SQLite + SQLAlchemy ORM
- **AI/ML**: OpenAI Whisper, Sentence Transformers, Annoy vector search
- **Web APIs**: FastAPI + Uvicorn
- **CLI**: Click framework with Rich progress indicators
- **External Services**: OpenRouter for LLM operations

## Common Development Commands

```bash
# Environment setup
uv venv && source .venv/bin/activate
uv pip install hatch && uv pip install -e .
# Alternative: ./scripts/setup_dev.sh

# Core operations
podsidian init                    # Initialize configuration
podsidian show-config            # Display current config and status
podsidian ingest --debug         # Process new episodes with debug output
podsidian search "query"         # Perform semantic search
podsidian briefing               # Generate personalized news briefing
podsidian mcp --stdio           # Start MCP server for AI agents

# Database operations
podsidian backup create         # Create database backup
podsidian backup list          # List available backups
podsidian backup restore       # Restore from backup

# Linting and formatting
ruff check .                   # Check code style (100-char line limit)
ruff format .                  # Format code
```

## High-Level Architecture

### Core Processing Pipeline
1. **Feed Source Integration** → Fetch podcast subscriptions from configured source
2. **RSS Feed Parsing** → Fetch episode metadata and audio URLs
3. **Audio Processing** → Whisper transcription with domain detection
4. **AI Correction** → LLM-powered transcript refinement using detected domain context
5. **Embedding Generation** → Sentence transformers for semantic vectors
6. **Vector Storage** → Annoy index for fast similarity search
7. **Obsidian Export** → Structured markdown with metadata and tags

### Key Components

- **PodcastProcessor** (`core.py`): Main processing engine that orchestrates the entire pipeline
- **CLI Interface** (`cli.py`): Click-based command system with rich progress indicators
- **Database Models** (`models.py`): SQLAlchemy schema for Podcasts and Episodes
- **MCP Server** (`stdio_server.py`): Model Context Protocol implementation for AI agent integration
- **Configuration System** (`config.py`): TOML-based config management with validation

### Important Entry Points

- **Main CLI**: `podsidian/cli.py:cli()` - Primary command interface
- **Core Engine**: `podsidian/core.py:PodcastProcessor` - Main processing class
- **MCP Server**: `podsidian/stdio_server.py` - AI agent integration endpoint
- **API Server**: `podsidian/api.py` - HTTP API for web integrations

## Configuration and Data

- **Config File**: `~/.config/podsidian/config.toml` (use `config.toml.example` as template)
- **Local Feeds File**: `~/.config/podsidian/feeds.toml` (when using local feed source)
- **Database**: `~/.local/share/podsidian/podsidian.db` (SQLite)
- **Vector Index**: Stored alongside database for semantic search
- **Audio Cache**: Configurable location for downloaded episode audio

## Development Notes

### Database Management
- Uses SQLAlchemy ORM with manual migration system
- Run `podsidian/migrate_db.py` for schema updates
- Backup system includes safety checks and metadata validation

### AI Integration
- Domain detection improves transcription accuracy by providing context to correction LLM
- Cost tracking monitors OpenRouter API usage across all operations
- MCP protocol enables integration with Claude Desktop and other AI agents

### Testing
- Feed source tests: `testing/test_feed_source.py` - Unit tests for feed source implementations
- MCP server tests: `testing/test_mcp_client.py` - Integration tests for MCP server
- Use `--debug` flag for detailed operation logging
- Database operations include transaction rollback on errors

### Running Tests
```bash
# Create and activate virtual environment
uv venv && source .venv/bin/activate

# Install test dependencies
uv pip install pytest tomli

# Run feed source tests
python -m pytest testing/test_feed_source.py -v

# Run all tests
python -m pytest testing/ -v
```

### Code Style
- Configured for 100-character line limit
- Use Ruff for linting and formatting
- Python 3.9+ features expected
- Type hints preferred for new code