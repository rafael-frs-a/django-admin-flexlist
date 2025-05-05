import typing as t
from dataclasses import asdict, dataclass

T = t.TypeVar("T", bound="Singleton")


class Singleton:
    """
    A base class that implements the singleton pattern.
    Ensures only one instance of a class exists throughout the application.
    """

    _instance: t.Optional["Singleton"] = None

    def __new__(cls: t.Type[T], *args: t.Any, **kwargs: t.Any) -> T:
        """
        Creates a new instance only if one doesn't exist, otherwise returns the existing instance.

        Returns:
            The singleton instance of the class
        """
        if cls._instance is None or cls._instance.__class__ is not cls:
            cls._instance = super().__new__(cls)

        return t.cast(T, cls._instance)


@dataclass
class FlexListField:
    """
    Represents a field in the flexlist configuration.

    Attributes:
        name: The name of the field
        description: The human-readable description of the field
        visible: Whether the field should be displayed in the list view
    """

    name: str
    description: str
    visible: bool


def deep_update_dict(
    d1: dict[str, t.Any],
    d2: dict[str, t.Any],
    seen: t.Optional[set[int]] = None,
) -> None:
    """
    Recursively updates a dictionary with values from another dictionary.
    Preserves existing nested structures while updating only the specified values.

    Args:
        d1: The target dictionary to update
        d2: The source dictionary containing updates
        seen: Set of dictionary IDs to prevent infinite recursion with circular references
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
    """
    Safely converts a value to a dictionary.

    Args:
        value: The value to convert

    Returns:
        The input value if it's a dictionary, otherwise an empty dictionary
    """
    if isinstance(value, dict):
        return value

    return {}


def get_list_from_value(value: t.Any) -> list[t.Any]:
    """
    Safely converts a value to a list.

    Args:
        value: The value to convert

    Returns:
        The input value if it's a list, otherwise an empty list
    """
    if isinstance(value, list):
        return value

    return []


def make_list_fields_from_data(data: t.Any) -> list[FlexListField]:
    """
    Creates a list of FlexListField objects from a dictionary.

    Args:
        data: A dictionary or list containing field configurations

    Returns:
        A list of FlexListField objects created from the input data

    Note:
        Invalid field configurations are silently skipped
    """

    data_list = get_list_from_value(data)
    result: list[FlexListField] = []

    for field in data_list:
        field_dict = get_dict_from_value(field)

        try:
            result.append(FlexListField(**field_dict))
        except TypeError:
            continue

    return result


def make_payload_from_list_fields(
    list_fields: list[FlexListField],
) -> list[dict[str, t.Any]]:
    """
    Creates a payload from a list of FlexListField objects.

    Args:
        list_fields: A list of FlexListField objects to convert to dictionaries

    Returns:
        A list of dictionaries containing the field configurations

    Example:
        >>> fields = [FlexListField(name="user", description="User", visible=True)]
        >>> make_payload_from_list_fields(fields)
        [{"name": "user", "description": "User", "visible": True}]
    """

    return [asdict(field) for field in list_fields]


def make_update_payload_from_list_fields(
    list_fields: list[FlexListField], path: list[str]
) -> dict[str, t.Any]:
    """
    Creates an update payload from a list of FlexListField objects.

    Args:
        list_fields: A list of FlexListField objects to include in the payload
        path: A list of strings representing the path where the fields should be stored

    Returns:
        A nested dictionary structure with the fields stored at the specified path

    Example:
        >>> path = ["apps", "auth", "model_list"]
        >>> fields = [FlexListField(name="user", description="User", visible=True)]
        >>> make_update_payload_from_list_fields(fields, path)
        {"apps": {"auth": {"model_list": [{"name": "user", "description": "User", "visible": True}]}}}
    """

    payload: dict[str, t.Any] = {}
    current: dict[str, t.Any] = payload

    for key in path[:-1]:
        current[key] = {}
        current = current[key]

    current[path[-1]] = make_payload_from_list_fields(list_fields)
    return payload
