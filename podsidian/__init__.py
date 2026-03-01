__version__ = "1.1.0"


def __getattr__(name):
    if name == "cli":
        from .cli import cli

        return cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["cli"]
