import typing as t

import pytest


@pytest.fixture(scope="session")
def app_url() -> str:
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def page_timeout() -> int:
    return 10 * 1000  # milliseconds


@pytest.fixture(scope="session")
def window_width() -> int:
    return 1440


@pytest.fixture(scope="session")
def window_height() -> int:
    return 700


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, t.Any], window_width: int, window_height: int
) -> dict[str, t.Any]:
    return {
        **browser_context_args,
        "viewport": {"width": window_width, "height": window_height},
    }
