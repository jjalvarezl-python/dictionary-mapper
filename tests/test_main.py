from typing import TypedDict, cast

import pytest

from dictionary_mapper import RawDictionaryMapper, SpecEntry, TransformationMapping, TypedDictionaryMapper


class MySecondaryNestedDict(TypedDict):
    secondary_int: int
    secondary_str: str


class MyNestedDict(TypedDict):
    nested_int: int
    nested_str: str
    secondary_field: list[MySecondaryNestedDict]


class MyTypedDict(TypedDict):
    int_field: int
    str_field: str
    complex_field: MyNestedDict
    list_field: str
    int_list: list[int]
    str_list: list[str]
    modificable_str_list: list[str]
    defined_none_field: str | None
    complex_list: list[MyNestedDict]
    complex_list_extra: list[MyNestedDict]


@pytest.fixture  # type: ignore[misc]
def src_dict() -> dict[str, object]:
    return {
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
            "modificable_int_list": [4, 5, 6],
            "modificable_str_list": ["a", "b", "c"],
            "modificable_none_list": [None, None, None],
            "defined_none_field": None,
            "complex_list": [
                {
                    "nested_int": 10,
                    "nested_str": "complex",
                },
                {"nested_int": 5},
                {"nested_str": "complex++"},
                {
                    "nested_str": "double complex",
                },
            ],
        },
    }


@pytest.fixture  # type: ignore[misc]
def spec() -> SpecEntry:
    return {
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
        "body.defined_none_field": "defined_none_field",
        "body.undefined_none_field": "undefined_none_field",
        "body.complex_list[0].nested_int": "complex_list[1].secondary_field[0].secondary_int",
        "body.complex_list[0].nested_str": "complex_list[1].secondary_field[3].secondary_str",
        "body.complex_list[2].nested_int": "complex_list[1].secondary_field[1].secondary_int",
        "body.complex_list[3].nested_str": "complex_list[1].secondary_field[2].secondary_str",
        "body.complex_list[1].nested_int": {
            "path": "complex_list[0].secondary_field[1].secondary_int",
            "default": 0,
            "transform": lambda x: cast("int", x) * 2,
        },
        "body.complex_list[2].nested_str": cast ("str | TransformationMapping", {
            "path": "complex_list[1].secondary_field[1].secondary_str",
            "default": "default string",
            "transform": lambda x: (x for _ in ()).throw( # type: ignore[misc]
                Exception("Should not be called"),
            ),
        }),
        "body.complex_list": "complex_list_extra",
        "body.complex_list[4]": "out_of_bounds_index",
        "body.complex_field[0]": "field_used_as_a_list",
        "body.complex_list[-1].not_exitstent_field": "non_existent_src_key",
        "test_non_existent_src_key": "",
        "body.complex_list[-//*8]": "modificable_str_list[1]",
        "body.complex_list[1]": "modificable_str_list[*-/--\u0085]",
        "": "",
        "body.modificable_str_list[1]": "modificable_str_list[1]",
        "body.modificable_int_list[1]": "modificable_int_list[1]",
        "body.modificable_none_list[1]": "modificable_none_list[1]",
        "body.complex_list[1]": "complex_list[6]",  # noqa: F601
    }


EXPECTED_INT_FIELD = 10


def common_assertions(maped_dict: dict[str, object]) -> None:
    assert maped_dict["int_field"] == EXPECTED_INT_FIELD
    assert maped_dict["str_field"] == "hello"
    assert cast("dict[str, object]", maped_dict["complex_field"])["nested_int"] == EXPECTED_INT_FIELD  # Transformed
    assert cast("dict[str, object]", maped_dict["complex_field"])["nested_str"] == "world"
    assert maped_dict["list_field"] == "test field"
    assert maped_dict["int_list"] == [1, 2, 3]
    assert maped_dict["str_list"] == ["1", "2", "3"]
    assert maped_dict["defined_none_field"] is None
    assert maped_dict["undefined_none_field"] is None
    complex_list = cast("list[dict[str, object]]", maped_dict["complex_list"])
    assert cast("list[dict[str, object]]", complex_list[1]["secondary_field"])[0]["secondary_int"] == EXPECTED_INT_FIELD
    assert cast("list[dict[str, object]]", complex_list[1]["secondary_field"])[3]["secondary_str"] == "complex"
    assert cast("list[dict[str, object]]", complex_list[1]["secondary_field"])[1]["secondary_int"] is None
    assert cast("list[dict[str, object]]", complex_list[1]["secondary_field"])[2]["secondary_str"] == "double complex"
    assert (
        cast("list[dict[str, object]]", complex_list[0]["secondary_field"])[1]["secondary_int"] == EXPECTED_INT_FIELD
    )  # Transformed
    assert cast("list[dict[str, object]]", complex_list[1]["secondary_field"])[1]["secondary_str"] == "default string"
    assert cast("list[dict[str, object]]", maped_dict["complex_list_extra"]) == [
        {
            "nested_int": 10,
            "nested_str": "complex",
        },
        {"nested_int": 5},
        {"nested_str": "complex++"},
        {
            "nested_str": "double complex",
        },
    ]
    assert cast("list[str | None]", maped_dict["modificable_str_list"]) == [
        None,
        "b",
    ]
    assert cast("list[int]", maped_dict["modificable_int_list"]) == [
        -1,
        5,
    ]


def test_map_raw_dict_to_raw_dict(src_dict: dict[str, object], spec: SpecEntry) -> None:
    dm: RawDictionaryMapper = RawDictionaryMapper()

    maped_dict: dict[str, object] = dm.create_transformed_dict(src_dict, spec)

    common_assertions(maped_dict)


def test_map_raw_dict_to_typed_dict(
    src_dict: dict[str, object],
    spec: SpecEntry,
) -> None:
    dm: TypedDictionaryMapper[MyTypedDict] = TypedDictionaryMapper()

    maped_dict: MyTypedDict = dm.create_transformed_dict(src_dict, spec)

    common_assertions(cast("dict[str, object]", maped_dict))
