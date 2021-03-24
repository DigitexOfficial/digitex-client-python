import asyncio
import threading
from functools import wraps, lru_cache

force_sync = False
force_async = False

@lru_cache()
def should_use_sync():
    """Detect whether we're being used in a sync or async environment."""
    if force_sync:
        return True
    if force_async:
        return False
    return asyncio._get_running_loop() is None

background_event_loop = None
background_event_loop_lock = threading.Lock()
background_event_loop_event = threading.Event()

def get_or_create_background_event_loop():
    def background_thread():
        global background_event_loop
        assert background_event_loop is None
        background_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(background_event_loop)
        background_event_loop_event.set()
        background_event_loop.run_forever()

    with background_event_loop_lock:
        if background_event_loop is not None:
            return background_event_loop

        threading.Thread(target=background_thread, daemon=True).start()
        background_event_loop_event.wait()
        return background_event_loop

def run(awaitable):
    if should_use_sync():
        loop = get_or_create_background_event_loop()
        future = asyncio.run_coroutine_threadsafe(awaitable, loop)
        return future.result()
    return awaitable

def auto_async(f):
    """Make an async function automatically behave in a sync fashion if needed.

    This decorator enables a single function, which must itself be written as
    an async function, to be transparently usable both as an async function and
    as a sync function, by running it in a asyncio event loop if an otherwise sync
    environment is detected.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        awaitable = f(*args, **kwargs)
        return run(awaitable)
    return wrapper

def synchonized(f):
    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        # First, ensure there is a lock.
        # We cannot do this in init() because it has
        # to be done from inside the loop. This is
        # not racy, because there are no await points
        # here.
        if self.lock is None:
            self.lock = asyncio.Lock()
        # And now, use it.
        async with self.lock:
            return await f(self, *args, **kwargs)
    return wrapper

def auto_async_iter(klass):
    def __next__(self):
        try:
            return run(self.__anext__())
        except StopAsyncIteration:
            raise StopIteration()
    klass.__next__ = __next__
    return klass
