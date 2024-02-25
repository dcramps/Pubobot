import time

from . import console


tasks = {}
next_task = False


def init():
    global tasks, next_task
    tasks = {}
    next_task = False


def run(frametime):
    if next_task:
        if frametime > tasks[next_task][0]:
            current_task = tasks.pop(next_task)
            try:
                current_task[1](*current_task[2])
            except Exception as e:
                console.display(
                    "SCHEDULER| ERROR: Task function failed @ {0} {1}, Exception: {2}".format(
                        current_task[1], current_task[2], e
                    )
                )
            define_next_task()


def add_task(name, delay, func, args, comment=None):
    if name not in tasks:
        tasks[name] = [
            time.time() + delay,
            func,
            args,
            comment,
        ]  # time to run task, func
        define_next_task()
    else:
        console.display("SCHEDULER| ERROR: Task with this name already exist!")


def cancel_task(name):
    if name in tasks:
        tasks.pop(name)
        if next_task == name:
            define_next_task()
    else:
        console.display("SCHEDULER| ERROR: No such task")


def define_next_task():
    global next_task
    if len(list(tasks.keys())) > 0:
        sorted_tasks = sorted([(value, key) for (key, value) in list(tasks.items())])
        if next_task != sorted_tasks[0][1]:
            next_task = sorted_tasks[0][1]
    else:
        next_task = False
