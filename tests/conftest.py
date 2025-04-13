import tkinter as tk
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
    # Let's get 80% of the screen width
    return int(tk.Tk().winfo_screenwidth() * 0.8)


@pytest.fixture(scope="session")
def window_height() -> int:
    # Let's get 80% of the screen height
    return int(tk.Tk().winfo_screenheight() * 0.8)


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, t.Any], window_width: int, window_height: int
) -> dict[str, t.Any]:
    return {
        **browser_context_args,
        "viewport": {"width": window_width, "height": window_height},
    }
