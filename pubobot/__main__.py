#!/usr/bin/python3
# encoding: utf-8
import time
import asyncio
import argparse
import os
import signal
import sys

# my modules
from . import console, config, bot, client, scheduler, stats3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="config.cfg", help="configuration file"
    )
    parser.add_argument("-l", "--logs", default="logs", help="log directory")
    parser.add_argument(
        "-d", "--db", default="database.sqlite3", help="sqlite3 database"
    )

    args = parser.parse_args()

    # Only enable input if running under a TTY
    enable_input = os.isatty(sys.stdin.fileno())

    console.init(args.logs, enable_input)
    scheduler.init()
    bot.init()
    stats3.init(args.db)
    config.init(args.config)
    client.init()

    loop = client.c.loop
    loop.create_task(bot_run())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, cleanly_exit, sig)

    client.run()  # runs until ctrl+c


async def bot_run():  # background thinking
    while True:
        if console.alive:
            frametime = time.time()
            bot.run(frametime)
            scheduler.run(frametime)
            console.run()
            await client.send()
            await asyncio.sleep(0.5)
        else:
            await client.close()
            print("QUIT NOW.")
            os._exit(0)


def cleanly_exit(sig):
    print(f"Received signal {sig}, exiting.")
    console.terminate()


if __name__ == "__main__":
    main()
