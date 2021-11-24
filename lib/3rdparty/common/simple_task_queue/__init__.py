# coding: utf-8
import sys
import time
import uuid
from logging import getLogger
from queue import PriorityQueue
from typing import List, Dict, Callable
from threading import Thread, Event
from collections import namedtuple

__all__ = [
    'task',
    'Task',
    'WorkerPool',
    'Job',
]

logger = getLogger(__name__)

_TaskInfo = namedtuple('_TaskInfo', ['name', 'func', 'ignore_result'])
_QueueInfo = namedtuple('_QueueInfo', ['name', 'priority', 'pool'])

_task_registry: Dict[str, _TaskInfo] = {}
_queue_registry: List[_QueueInfo] = []


def task(name: str, ignore_result=False):
    def wrapper(func):
        _task_registry[name] = _TaskInfo(name, func, ignore_result)
        logger.info('register task func=%s name=%s ignore_result=%s',
                    func, name, ignore_result)
        return func
    return wrapper


class Job:

    def __init__(self, name: str, func: Callable, ignore_result=True):
        self.created = time.time()
        self.name = name
        self.func = func
        self.ignore_result = ignore_result
        self._ret_value = None
        self._error = None
        self._lock = Event()

    def __lt__(self, other):
        if isinstance(other, Job):
            return self.created < other.created
        return False

    def __call__(self):
        try:
            self._ret_value = self.func()
        except Exception as e:
            self._ret_value = None
            tb = sys.exc_info()[2]
            self._error = (e, tb)
        self._lock.set()

    def is_done(self):
        return self._lock.is_set()

    def result(self):
        if self.ignore_result:
            return
        self._lock.wait()
        if self._error is not None:
            e, tb = self._error
            raise e.__class__(*e.args).with_traceback(tb)
        return self._ret_value


class Worker:

    def __init__(self, worker_id: int, queue: PriorityQueue, backend):
        self.worker_id = worker_id
        self._queue = queue
        self.backend = backend
        self._worker = None

    def start(self):
        if self._worker is None:
            self._worker = self.backend(target=self.do_work)
            self._worker.start()

    def do_work(self):
        while True:
            item = self._queue.get()
            if isinstance(item, tuple) and len(item) == 2:
                _, job = item
                if isinstance(job, Job):
                    job()
                    continue
            break

    def join(self):
        return self._worker.join()


class WorkerPool:

    def __init__(self, worker_num=4, default_priority=50):
        # TODO: multiprocessing
        self.pool_id = uuid.uuid4().hex
        self.worker_num = worker_num
        self.default_priority = default_priority
        self._queue = PriorityQueue()
        self._workers = []
        self._look = Event()

    def add_queue(self, name: str, priority: int) -> None:
        q_info = _QueueInfo(name, priority, self)
        _queue_registry.append(q_info)

    def start(self) -> None:
        self.add_queue('', self.default_priority)
        self._look.set()
        for i in range(self.worker_num):
            worker = Worker(i, self._queue, Thread)
            worker.start()
            self._workers.append(worker)

    def stop(self, wait=True) -> None:
        if not self.is_working():
            return
        self._look.clear()
        if wait:
            stop_job_priority = float('inf')
        else:
            stop_job_priority = float('-inf')
        for i in range(self.worker_num):
            self._queue.put((stop_job_priority, None))
        for worker in self._workers:
            worker.join()

    def is_working(self):
        return self._look.is_set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(wait=True)
        return False

    def add_task(self, name: str, func: Callable,
                 priority: int, ignore_result: True) -> Job:
        job = Job(name, func, ignore_result)
        self._queue.put((-priority, job))
        return job


class Task:

    def __init__(self, name: str):
        self.name = name
        self.task = _task_registry.get(name)
        if self.task is None:
            raise ValueError('unknown task: %s' % name)
        self.q_info = self._resolve_queue()

    def _resolve_queue(self) -> _QueueInfo:
        match_q_info = None
        match_len = -1
        for q_info in _queue_registry:
            if not self.name.startswith(q_info.name):
                continue
            if not q_info.pool.is_working():
                continue
            if match_len < len(q_info.name):
                match_q_info = q_info
                match_len = len(q_info.name)
        if match_q_info is not None:
            return match_q_info
        else:
            raise RuntimeError('Worker pool is not running')

    def _make_job(self, args, kwargs) -> Job:
        job = self.q_info.pool.add_task(
                self.name,
                lambda: self.task.func(*args, **kwargs),
                self.q_info.priority,
                ignore_result=self.task.ignore_result)
        return job

    def __call__(self, *args, **kwargs):
        job = self._make_job(args, kwargs)
        return job.result()

    def promise(self, *args, **kwargs) -> Job:
        job = self._make_job(args, kwargs)
        return job
