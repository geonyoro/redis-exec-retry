import socket
import time
import typing

import redis
from redis.retry import Retry


class Redis(redis.Redis):
    def execute_command(self, *args, **options):
        kwargs = self.get_connection_kwargs()
        retry = kwargs.get("retry")
        if retry:
            super_ref = super()
            return retry.call_with_retry(
                lambda: super_ref.execute_command(*args, **options), lambda _: _
            )
        else:
            return super().execute_command(*args, **options)


class BackoffTimeoutExceeded(redis.exceptions.RedisError):
    pass


class LimitedTimeBackOff(redis.backoff.AbstractBackoff):
    """
    Sets a max runtime x seconds to any backoff after which an error is raised.

    Passing seconds <=0 as the max_run_secs makes it run like any of the other backoffs.
    """

    def __init__(
        self,
        max_run_secs: typing.Union[int, float],
        backoff_instance: redis.backoff.AbstractBackoff,
    ):
        self._max_run_secs = max_run_secs
        self._start = None
        self.backoff_instance = backoff_instance

    def compute(self, failures):
        if failures == 1:
            # first failure, start running
            self._start = time.time()
        elif (
            self._start
            and self._max_run_secs > 0
            and (time.time() - self._start) > self._max_run_secs
        ):
            raise BackoffTimeoutExceeded

        return self._backoff_instance.compute(failures)


backoff_instance = redis.backoff.ExponentialBackoff()
retry = Retry(
    backoff=LimitedTimeBackOff(2, backoff_instance=backoff_instance),
    retries=-1,
    supported_errors=(
        redis.exceptions.BusyLoadingError,
        redis.exceptions.ConnectionError,
        redis.exceptions.TimeoutError,
        socket.timeout,
    ),
)
r = Redis(port=1000, retry=retry)
print(r.keys("*"))  # will run for 2 seconds before
