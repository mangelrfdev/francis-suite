"""
core/registry.py

PluginRegistry maps XML tag names to their Plugin classes.
Plugins register themselves automatically via the @plugin decorator.

Example:
    @plugin(tag="http-call")
    class HttpCallPlugin(AbstractPlugin):
        ...

    registry = PluginRegistry.instance()
    plugin_class = registry.get("http-call")  # HttpCallPlugin
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from francis_suite.plugins.base import AbstractPlugin


class PluginRegistry:
    """
    Central registry that maps tag names to Plugin classes.
    Implemented as a singleton — there is one registry per process.
    """

    _instance: "PluginRegistry | None" = None

    def __init__(self) -> None:
        self._plugins: dict[str, type] = {}

    @classmethod
    def instance(cls) -> "PluginRegistry":
        """Return the global singleton registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton. Used in tests only.
        Never call this in production code.
        """
        cls._instance = None

    def register(self, tag: str, plugin_class: type) -> None:
        """
        Register a plugin class under a tag name.
        Raises ValueError if the tag is already registered.
        """
        if tag in self._plugins:
            existing = self._plugins[tag].__name__
            raise ValueError(
                f"Tag '{tag}' is already registered by {existing}. "
                f"Cannot register {plugin_class.__name__} for the same tag."
            )
        self._plugins[tag] = plugin_class

    def get(self, tag: str) -> type | None:
        """
        Return the plugin class for a tag name.
        Returns None if the tag is not registered.
        """
        return self._plugins.get(tag)

    def require(self, tag: str) -> type:
        """
        Return the plugin class for a tag name.
        Raises ValueError if the tag is not registered.
        Use this in the runtime where unknown tags are errors.
        """
        plugin_class = self._plugins.get(tag)
        if plugin_class is None:
            raise ValueError(
                f"Unknown tag <{tag}>. "
                f"No plugin is registered for this tag name."
            )
        return plugin_class

    def all_tags(self) -> list[str]:
        """Return all registered tag names."""
        return list(self._plugins.keys())

    def __len__(self) -> int:
        return len(self._plugins)

    def __repr__(self) -> str:
        return f"PluginRegistry({len(self._plugins)} plugins: {self.all_tags()})"


def plugin(tag: str):
    """
    Decorator that registers a Plugin class in the global registry.

    Usage:
        @plugin(tag="http-call")
        class HttpCallPlugin(AbstractPlugin):
            ...

    The class is registered automatically when the module is imported.
    """
    def decorator(cls: type) -> type:
        PluginRegistry.instance().register(tag, cls)
        return cls
    return decorator