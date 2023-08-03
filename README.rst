Redis Exec Retry 
================

This module wraps the execute_command method of the Redis class, allowing any retry passed to be used. It also introduces a new Backoff, LimitedTimeBackoff, allowing one to set a timeout before which the BackoffTimeoutExceeded is raised.

The purpose of the module is to provide an alternative to the official redis app, as we await an update to hanlding timeout errors.

Usage
-----
Provide a `retry` to the Redis class which shall be used later.


Examples
--------
.. code-block:: python

    import redis
    import socket
    import redis_exec_retry

    max_seconds = 2
    backoff_instance = redis.backoff.ExponentialBackoff()
    retry = redis.retry.Retry(
        backoff=redis_exec_retry.LimitedTimeBackOff(max_seconds, backoff_instance=backoff_instance),
        retries=-1,
        supported_errors=(
            redis.exceptions.BusyLoadingError,
            redis.exceptions.ConnectionError,
            redis.exceptions.TimeoutError,
            socket.timeout,
        ),
    )
    r = redis_exec_retry.Redis(port=1000, retry=retry)
    print(r.keys("*"))  # will run for 2 seconds before raising redis_exec_retry.BackoffTimeoutExceeded
