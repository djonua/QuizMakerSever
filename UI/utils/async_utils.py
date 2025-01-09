import asyncio
import functools
from typing import Callable, Any
from contextlib import contextmanager

@contextmanager
def get_event_loop():
    """Контекстный менеджер для работы с event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()

def async_handler(func: Callable) -> Callable:
    """Декоратор для обработки асинхронных функций в Streamlit"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with get_event_loop() as loop:
            return loop.run_until_complete(func(*args, **kwargs))
    return wrapper
