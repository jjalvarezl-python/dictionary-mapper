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

    def _set_by_path(self, dst: MutableMapping[str, object], path: str, value: object) -> None:  # noqa: C901
        parts = path.split(".")
        cur = dst
        for i, part in enumerate(parts):
            m = re.match(r"^([^\[]+)\[(\d+)\]$", part)
            is_last = i == len(parts) - 1

            if m:
                key, idx = m.group(1), int(m.group(2))
                lst: list[object] = cast("list[object]", cur.setdefault(key, []))
                while len(lst) <= idx:
                    if isinstance(value, str):
                        lst.append("")
                    elif isinstance(value, (int, float)):
                        lst.append(-1)
                    elif isinstance(value, dict):
                        lst.append({})
                    else:
                        lst.append(None)
                if is_last:
                    lst[idx] = value
                    return
                if not isinstance(lst[idx], dict):
                    lst[idx] = {}
                cur = cast("MutableMapping[str, object]", lst[idx])
            else:
                if is_last:
                    cur[part] = value
                    return
                if part not in cur or not isinstance(cur[part], dict):
                    cur[part] = {}
                cur = cast("MutableMapping[str, object]", cur[part])

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
