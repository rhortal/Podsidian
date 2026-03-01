import os
import sys
from typing import List, Optional, Callable
from dataclasses import dataclass

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import has_focus
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import MenuContainer, MenuItem
from prompt_toolkit.widgets import Label, Frame, TextArea, Button
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from .podcast_manager import PodcastManager, PodcastEntry
from .podcast_search import PodcastSearcher, PodcastSearchResult


@dataclass
class PodcastListItem:
    """Wrapper for displaying a podcast in the list."""

    entry: PodcastEntry
    index: int

    @property
    def is_active(self) -> bool:
        return self.entry.active


class PodcastListTUI:
    """Interactive TUI for managing podcast subscriptions."""

    def __init__(self, manager: PodcastManager):
        self.manager = manager
        self.podcasts: List[PodcastEntry] = []
        self.selected_index = 0
        self.console = Console()
        self._load_podcasts()

    def _load_podcasts(self):
        """Load podcasts from the manager."""
        try:
            self.podcasts = self.manager.load_podcasts()
        except FileNotFoundError:
            self.podcasts = []

    def run(self):
        """Run the interactive TUI."""
        while True:
            self._render()
            choice = self._get_input()
            if choice == "q":
                break
            elif choice == "j" or choice == "down":
                self._move_down()
            elif choice == "k" or choice == "up":
                self._move_up()
            elif choice == " ":
                self._toggle_selected()
            elif choice == "d":
                self._delete_selected()
            elif choice == "e":
                self._edit_selected()
            elif choice == "a":
                self._add_podcast()
            elif choice == "r":
                self._refresh()

    def _render(self):
        """Render the podcast list."""
        self.console.clear()

        # Title
        self.console.print("\n[bold cyan]Podcast Manager[/bold cyan]")
        self.console.print(
            f"Total: {len(self.podcasts)} | Active: {sum(1 for p in self.podcasts if p.active)}"
        )
        self.console.print()

        if not self.podcasts:
            self.console.print("[yellow]No podcasts configured.[/yellow]")
            self.console.print("[dim]Press 'a' to add a podcast or 'h' for help.[/dim]\n")
            return

        # Table header
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column("Status", width=8)
        table.add_column("Podcast", style="cyan")
        table.add_column("Author", style="green")

        for i, podcast in enumerate(self.podcasts):
            status = "[green]● Active[/green]" if podcast.active else "[dim]○ Inactive[/dim]"
            title = podcast.title if podcast.active else f"[dim]{podcast.title}[/dim]"
            prefix = "→ " if i == self.selected_index else "  "

            table.add_row(
                f"{prefix}{i + 1}",
                status,
                title,
                podcast.author or "-",
            )

        self.console.print(table)
        self.console.print()

        # Selected podcast details
        if self.selected_index < len(self.podcasts):
            selected = self.podcasts[self.selected_index]
            self.console.print(f"[bold]Selected:[/bold] {selected.title}")
            self.console.print(f"[dim]Feed:[/dim] {selected.feed_url}")
            if selected.description:
                desc = (
                    selected.description[:100] + "..."
                    if len(selected.description) > 100
                    else selected.description
                )
                self.console.print(f"[dim]Description:[/dim] {desc}")

        # Help
        self.console.print()
        self.console.print("[bold]Controls:[/bold]")
        self.console.print("  [cyan]↑/↓[/cyan] or [cyan]k/j[/cyan]  Navigate")
        self.console.print("  [cyan]Space[/cyan]           Toggle active/inactive")
        self.console.print("  [cyan]Enter[/cyan]          Edit podcast")
        self.console.print("  [cyan]d[/cyan]              Delete podcast")
        self.console.print("  [cyan]a[/cyan]              Add new podcast")
        self.console.print("  [cyan]r[/cyan]              Refresh list")
        self.console.print("  [cyan]q[/cyan]              Quit")

    def _get_input(self) -> str:
        """Get user input (simple version using input())."""
        return input("\n> ").strip().lower()

    def _move_up(self):
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1

    def _move_down(self):
        """Move selection down."""
        if self.selected_index < len(self.podcasts) - 1:
            self.selected_index += 1

    def _toggle_selected(self):
        """Toggle the selected podcast's active status."""
        if self.selected_index < len(self.podcasts):
            podcast = self.podcasts[self.selected_index]
            podcast.active = not podcast.active
            self.manager.save_podcasts(self.podcasts)
            self.console.print(
                f"[green]Toggled:[/green] {podcast.title} → {'Active' if podcast.active else 'Inactive'}"
            )

    def _delete_selected(self):
        """Delete the selected podcast."""
        if self.selected_index < len(self.podcasts):
            podcast = self.podcasts[self.selected_index]
            confirm = input(f"Delete '{podcast.title}'? [y/N]: ").strip().lower()
            if confirm == "y":
                self.manager.remove_podcast(podcast.feed_url)
                self._load_podcasts()
                if self.selected_index >= len(self.podcasts):
                    self.selected_index = max(0, len(self.podcasts) - 1)
                self.console.print(f"[red]Deleted:[/red] {podcast.title}")

    def _edit_selected(self):
        """Edit the selected podcast."""
        if self.selected_index >= len(self.podcasts):
            return

        podcast = self.podcasts[self.selected_index]
        self.console.print("\n[bold]Edit Podcast[/bold]")
        self.console.print("(Leave empty to keep current value)\n")

        # Title
        new_title = input(f"Title [{podcast.title}]: ").strip()
        if not new_title:
            new_title = podcast.title

        # Author
        new_author = input(f"Author [{podcast.author}]: ").strip()
        if not new_author:
            new_author = podcast.author

        # Feed URL
        new_feed_url = input(f"Feed URL [{podcast.feed_url}]: ").strip()
        if not new_feed_url:
            new_feed_url = podcast.feed_url

        # Description
        new_description = input(
            f"Description [{podcast.description[:50] if podcast.description else ''}]: "
        ).strip()
        if not new_description:
            new_description = podcast.description

        # Active status
        active_str = "Y" if podcast.active else "n"
        new_active = input(f"Active (Y/n) [{active_str}]: ").strip().lower()
        if new_active == "y":
            new_active = True
        elif new_active == "n":
            new_active = False
        else:
            new_active = podcast.active

        # Update
        podcast.title = new_title
        podcast.author = new_author
        podcast.feed_url = new_feed_url
        podcast.description = new_description
        podcast.active = new_active

        self.manager.save_podcasts(self.podcasts)
        self.console.print("[green]Updated![/green]")

    def _add_podcast(self):
        """Add a new podcast via search."""
        self._interactive_search_and_add()

    def _refresh(self):
        """Refresh the podcast list from file."""
        self._load_podcasts()
        self.console.print("[green]Refreshed![/green]")

    def _interactive_search_and_add(self):
        """Interactive search and add workflow."""
        self.console.print("\n[bold]Add Podcast[/bold]")
        query = input("Search for podcasts: ").strip()

        if not query:
            return

        self.console.print("\n[cyan]Searching...[/cyan]")

        # Search
        searcher = PodcastSearcher(sources=["apple", "podcastindex"])
        results = searcher.search(query, limit=20)

        if not results:
            self.console.print("[yellow]No results found. Try a different search.[/yellow]")
            return

        # Display results
        self.console.print(f"\n[bold]Results ({len(results)}):[/bold]\n")
        for i, result in enumerate(results):
            self.console.print(f"  [cyan]{i + 1}.[/cyan] {result.title}")
            self.console.print(f"       [dim]{result.author}[/dim]")

        # Select
        self.console.print("\nEnter number to add (comma-separated for multiple, or 'a' for all): ")
        selection = input("> ").strip()

        if selection.lower() == "a":
            to_add = results
        else:
            indices = []
            for part in selection.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(results):
                        indices.append(idx)
            to_add = [results[i] for i in indices]

        # Add podcasts
        for result in to_add:
            entry = PodcastEntry(
                title=result.title,
                author=result.author,
                feed_url=result.feed_url,
                description=result.description,
                active=True,
            )
            try:
                self.manager.add_podcast(entry)
                self.console.print(f"[green]Added:[/green] {result.title}")
            except ValueError as e:
                self.console.print(f"[yellow]{e}[/yellow]")

        self._load_podcasts()


def run_podcast_manager():
    """Entry point for the podcast manager TUI."""
    manager = PodcastManager()
    tui = PodcastListTUI(manager)
    tui.run()
