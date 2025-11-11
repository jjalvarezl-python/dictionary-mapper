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
        if not parts:
            return

        part = parts[0]
        m = re.match(r"^([^\[]+)\[(\d+)\]$", part)
        sub_m = re.match(r"^([^\[]+)\[(\d+)\]\.([^\[]]+)$", part)

        if len(parts) == 1:
            if sub_m:
                key, idx, subkey = sub_m.group(1), int(sub_m.group(2)), sub_m.group(3)
                lst: list[dict[str, object]] = cast("list[dict[str, object]]", dst.setdefault(key, []))
                while len(lst) <= idx:
                    lst.append({})
                lst[idx][subkey] = value
            elif m:
                key, idx = m.group(1), int(m.group(2))
                lst_items: list[object] = cast("list[object]", dst.setdefault(key, []))
                while len(lst_items) <= idx:
                    lst_items.append({})
                lst_items[idx] = value
            else:
                dst[part] = value
            return

        if m:
            key, idx = m.group(1), int(m.group(2))
            lst_nested: list[object] = cast("list[object]", dst.setdefault(key, []))
            while len(lst_nested) <= idx:
                lst_nested.append({})
            if not isinstance(lst_nested[idx], dict):
                lst_nested[idx] = {}
            self._set_by_path(cast("MutableMapping[str, object]", lst_nested[idx]), ".".join(parts[1:]), value)
        else:
            child = dst.setdefault(part, {})
            self._set_by_path(cast("MutableMapping[str, object]", child), ".".join(parts[1:]), value)

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
