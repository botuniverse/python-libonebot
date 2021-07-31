"""

"""

import asyncio
from typing import Any, Callable, Awaitable, Iterable, List


async def run_async_funcs(
    funcs: Iterable[Callable[..., Awaitable[Any]]], *args, **kwargs
) -> List[Any]:
    """
    同时运行多个异步函数，并等待所有函数运行完成，返回运行结果列表。
    """
    results = []
    coros = []
    for f in funcs:
        coros.append(f(*args, **kwargs))
    if coros:
        results += await asyncio.gather(*coros)
    return results
