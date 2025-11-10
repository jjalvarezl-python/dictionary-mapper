"""
dictionary_mapper.

A tool for mapping and transforming dictionaries based on predefined rules.
"""

import re
from collections.abc import Callable, Mapping, MutableMapping
from typing import TypedDict, cast


class TransformationMapping(TypedDict):
    """
    Mapping specification entry for dictionary transformation.

    Attributes
    ----------
    path : str
        Dotted path to the value in the source dictionary.
    default : object
        Default value if the path does not exist.
    transform : Callable[[object], object] | None
        Optional transformation function to apply to the value.

    """

    path: str
    default: object
    transform: Callable[[object], object] | None


SpecEntry = Mapping[str, str | TransformationMapping]


class RawDictionaryMapper:
    """A class for mapping raw dictionaries based on predefined rules."""

    def _get_by_path(self, source: dict[str, object], path: str, default: object = None) -> object:
        cur: object = source if path else default
        for part in path.split(".") if path else []:
            m = re.match(r"^([^\[]+)\[(\d+)\]$", part)
            if m:
                key, idx = m.group(1), int(m.group(2))
                cur = cur.get(key, default) if isinstance(cur, dict) else default
                if not isinstance(cur, list):
                    cur = default
                else:
                    try:
                        cur = cur[idx]
                    except IndexError:
                        cur = default
            elif isinstance(cur, dict):
                cur = cur.get(part, default)
            else:
                cur = default
            if cur is None:
                cur = default
        return cur

    def _set_by_path(self, dst: MutableMapping[str, object], path: str, value: object) -> None:
        parts = path.split(".")
        cur: MutableMapping[str, object] = dst
        for p in parts[:-1]:
            existing = cur.get(p)
            if not isinstance(existing, MutableMapping):
                existing = {}
                cur[p] = existing
            cur = cast("MutableMapping[str, object]", existing)
        cur[parts[-1]] = value

    def create_transformed_dict(self, source: dict[str, object], spec: SpecEntry) -> dict[str, object]:
        """
        Create a raw dictionary based on a source dictionary and mapping specifications.

        Parameters
        ----------
        source : dict
            The source dictionary to transform.
        spec : SpecEntry
            Specification defining how to map and transform the source dictionary.

        Returns
        -------
        dict[str, object]
            The transformed raw dictionary.

        """
        out: MutableMapping[str, object] = {}

        for entry, target in spec.items():
            if isinstance(target, str):
                path = target
                default = None
                transform = None
            else:
                path = target["path"]
                default = target["default"]
                transform = target["transform"]

            raw_val = self._get_by_path(source, entry, default)
            if callable(transform):
                try:
                    val = transform(raw_val)
                except Exception:  # noqa: BLE001
                    val = default
            else:
                val = raw_val

            self._set_by_path(out, path, val)

        return cast("dict[str, object]", out)


class TypedDictionaryMapper[T: Mapping[str, object]](RawDictionaryMapper):
    """A class for mapping typed dictionaries based on predefined rules."""

    def create_transformed_dict(self, source: dict[str, object], spec: SpecEntry) -> T:  # type: ignore[override]
        """
        Create a typed dictionary based on a source dictionary and mapping specifications.

        Parameters
        ----------
        source : dict
            The source dictionary to transform.
        spec : SpecEntry
            Specification defining how to map and transform the source dictionary.

        Returns
        -------
        T
            The transformed typed dictionary.

        """
        return cast("T", super().create_transformed_dict(source, spec))

