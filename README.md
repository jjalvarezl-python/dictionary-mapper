# Dictionary Mapper

[![GitHub tag](https://img.shields.io/github/v/tag/jjalvarezl-python/dictionary-mapper?sort=semver)](https://github.com/jjalvarezl-python/dictionary-mapper/tags)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dictionary-mapper.svg)](https://pypi.org/project/dictionary-mapper)

-----

## Table of Contents

- [Usage](#Usage)
- [Installation](#installation)
- [License](#license)

## Usage

This library can map a source dictionary and generate a target new one following dot notation in source and target dictionaries.

Example:

1. Define a SpecEntry dict, keys are the source dict paths, values are the target dict paths:

```python
from dictionary_mapper import SpecEntry


spec: SpecEntry = {
    "body.int_field": "int_field",
    "body.str_field": "str_field",
    "body.complex_field.nested_int": {
        "path": "complex_field.nested_int",
        "default": 0,
        "transform": lambda x: cast("int", x) * 2,
    },
    "body.complex_field.nested_str": "complex_field.nested_str",
    "body.list[0].str_field": "list_field",
    "body.int_list": "int_list",
    "body.str_list": "str_list",
}
```

2. For raw dict output, then use the RawDictionaryMapper class

```python
...
from typing import cast
from dictionary_mapper import RawDictionaryMapper
...


src: dict[str, object] = {
    "body": {
        "int_field": 10,
        "str_field": "hello",
        "complex_field": {
            "nested_int": 5,
            "nested_str": "world",
        },
        "list": [
            {
                "str_field": "test field",
            },
        ],
        "int_list": [1, 2, 3],
        "str_list": ["1", "2", "3"],
    },
}


dm: RawDictionaryMapper = RawDictionaryMapper()

maped_dict: dict[str, object] = dm.create_transformed_dict(src, spec)

assert maped_dict["int_field"] == 10
assert maped_dict["str_field"] == "hello"
assert cast("dict[str, object]", maped_dict["complex_field"])["nested_int"] == 10  # Transformed
assert cast("dict[str, object]", maped_dict["complex_field"])["nested_str"] == "world"
assert maped_dict["list_field"] == "test field"
assert maped_dict["int_list"] == [1, 2, 3]
assert maped_dict["str_list"] == ["1", "2", "3"]
```

3. For TypedDicts you can use the TypedDictionaryMapper as follows

```python
...
from dictionary_mapper import TypedDictionaryMapper
...


class MyNestedDict(TypedDict):
    nested_int: int
    nested_str: str


class MyTypedDict(TypedDict):
    int_field: int
    str_field: str
    complex_field: MyNestedDict
    list_field: str
    int_list: list[int]
    str_list: list[str]

...

dm: TypedDictionaryMapper[MyTypedDict] = TypedDictionaryMapper()

maped_dict: MyTypedDict = dm.create_transformed_dict(src, spec)

assert maped_dict["int_field"] == 10
assert maped_dict["str_field"] == "hello"
assert maped_dict["complex_field"]["nested_int"] == 10  # Transformed
assert maped_dict["complex_field"]["nested_str"] == "world"
assert maped_dict["list_field"] == "test field"
assert maped_dict["int_list"] == [1, 2, 3]
assert maped_dict["str_list"] == ["1", "2", "3"]
```

4. You can add complex lists on the target, but you'll need to add allways the index to that lists, otherwhise will be recognized as primitive value.

```python
src = {
    ...
    "complex_list": [
        {
            "nested_int": 10,
            "nested_str": "complex",
        },
        {"nested_int": 5},
        {},
        {
            "nested_str": "double complex",
        },
    ],
    ...
}

...

spec = {
    ...
    "body.complex_list[0].nested_int": "complex_list[1].secondary_field[0].secondary_int",
    "body.complex_list[0].nested_str": "complex_list[1].secondary_field[3].secondary_str",
    "body.complex_list[2].nested_int": "complex_list[1].secondary_field[1].secondary_int",
    "body.complex_list[3].nested_str": "complex_list[1].secondary_field[2].secondary_str",
    "body.complex_list[1].nested_int": {
        "path": "complex_list[0].secondary_field[1].secondary_int",
        "default": 0,
        "transform": lambda x: cast("int", x) * 2,
    },
    ...
}

...

EXPECTED_INT_FIELD = 10

assert maped_dict["complex_list"][1]["secondary_field"][0]["secondary_int"] == EXPECTED_INT_FIELD
assert maped_dict["complex_list"][1]["secondary_field"][3]["secondary_str"] == "complex"
assert maped_dict["complex_list"][1]["secondary_field"][1]["secondary_int"] is None
assert maped_dict["complex_list"][1]["secondary_field"][2]["secondary_str"] == "double complex"
assert maped_dict["complex_list"][0]["secondary_field"][1]["secondary_int"] == EXPECTED_INT_FIELD  # Transformed

```

## Installation

Add recommended extensions at `.vscode/extensions.json`. Then run:

```console
pip install hatch hatch-pip-deepfreeze
hatch shell
```
These two commands creates everithing for you and vscode to start working ASAP.

## License

`dictionary-mapper` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
