import datetime
import functools
import json
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime.datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ) -> None:
        errors: list[Exception] = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self._critical_count = critical_count
        self._time_to_recover = time_to_recover
        self._triggers_on = triggers_on
        self._failed_count: int = 0
        self._block_time: datetime.datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            func_name = f"{func.__module__}.{func.__name__}"
            now = datetime.datetime.now(datetime.UTC)
            if self._is_blocked(now):
                if self._block_time is None:
                    raise BreakerError(func_name, now)
                raise BreakerError(func_name, self._block_time)
            self._reset_if_recovered(now)
            return self._call_func(func, func_name, *args, **kwargs)

        return wrapper

    def _is_blocked(self, now: datetime.datetime) -> bool:
        if self._block_time is None:
            return False
        blocked_seconds = (now - self._block_time).total_seconds()
        return blocked_seconds < self._time_to_recover

    def _reset_if_recovered(self, now: datetime.datetime) -> None:
        if self._block_time is not None and not self._is_blocked(now):
            self._block_time = None
            self._failed_count = 0

    def _handle_trigger_error(self, func_name: str, error: Exception) -> None:
        self._failed_count += 1
        if self._failed_count >= self._critical_count:
            block_time = datetime.datetime.now(datetime.UTC)
            self._block_time = block_time
            self._failed_count = 0
            raise BreakerError(func_name, block_time) from error

    def _call_func(
        self,
        func: CallableWithMeta[P, R_co],
        func_name: str,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R_co:
        try:
            result = func(*args, **kwargs)
        except Exception as error:
            if isinstance(error, self._triggers_on):
                self._handle_trigger_error(func_name, error)
            raise
        self._failed_count = 0
        return result


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
