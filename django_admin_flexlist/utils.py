import typing as t
from dataclasses import dataclass

T = t.TypeVar("T", bound="Singleton")


class Singleton:
    _instance: t.Optional["Singleton"] = None

    def __new__(cls: t.Type[T], *args: t.Any, **kwargs: t.Any) -> T:
        if cls._instance is None or cls._instance.__class__ is not cls:
            cls._instance = super().__new__(cls)

        return t.cast(T, cls._instance)


@dataclass
class FlexListField:
    name: str
    description: str
    visible: bool


def deep_update_dict(
    d1: dict[str, t.Any],
    d2: dict[str, t.Any],
    seen: t.Optional[set[int]] = None,
) -> None:
    """
    Update d1 with d2 recursively so we don't overwrite an entire item at the root,
    like the 'apps' key, when updating just one particular nested dictionary value.
    """

    if seen is None:
        seen = set()

    if id(d1) in seen:  # Prevent infinite loops with self-referencing dictionaries.
        return

    seen.add(id(d1))

    for key, value in d2.items():
        if isinstance(value, dict) and key in d1 and isinstance(d1[key], dict):
            deep_update_dict(d1[key], value, seen)
        else:
            d1[key] = value


def get_dict_from_value(value: t.Any) -> dict[str, t.Any]:
    if isinstance(value, dict):
        return value

    return {}


def get_list_from_value(value: t.Any) -> list[t.Any]:
    if isinstance(value, list):
        return value

    return []
