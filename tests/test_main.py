from typing import TypedDict, cast

from dictionary_mapper import RawDictionaryMapper, SpecEntry, TypedDictionaryMapper


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

EXPECTED_INT_FIELD = 10

def test_map_raw_dict_to_raw_dict() -> None:
    dm: RawDictionaryMapper = RawDictionaryMapper()

    maped_dict: dict[str, object] = dm.create_transformed_dict(src, spec)

    assert maped_dict["int_field"] == EXPECTED_INT_FIELD
    assert maped_dict["str_field"] == "hello"
    assert cast("dict[str, object]", maped_dict["complex_field"])["nested_int"] == EXPECTED_INT_FIELD  # Transformed
    assert cast("dict[str, object]", maped_dict["complex_field"])["nested_str"] == "world"
    assert maped_dict["list_field"] == "test field"
    assert maped_dict["int_list"] == [1, 2, 3]
    assert maped_dict["str_list"] == ["1", "2", "3"]


def test_map_raw_dict_to_typed_dict() -> None:
    dm: TypedDictionaryMapper[MyTypedDict] = TypedDictionaryMapper()

    maped_dict: MyTypedDict = dm.create_transformed_dict(src, spec)

    assert maped_dict["int_field"] == EXPECTED_INT_FIELD
    assert maped_dict["str_field"] == "hello"
    assert maped_dict["complex_field"]["nested_int"] == EXPECTED_INT_FIELD  # Transformed
    assert maped_dict["complex_field"]["nested_str"] == "world"
    assert maped_dict["list_field"] == "test field"
    assert maped_dict["int_list"] == [1, 2, 3]
    assert maped_dict["str_list"] == ["1", "2", "3"]
