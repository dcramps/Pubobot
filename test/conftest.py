import pytest_asyncio
import time
import asyncio

import discord.ext.test as dpytest


@pytest_asyncio.fixture(scope="session")
async def bot():
    from pubobot import console, scheduler, bot, stats3, config, client

    console.init(enable_input=False)
    scheduler.init()
    bot.init()
    stats3.init()
    config.init()
    client.init()

    dpytest.configure(client.c)

    async def run_background_tasks():
        while True:
            if not console.alive:
                await client.close()
                break

            frametime = time.time()
            bot.run(frametime)
            scheduler.run(frametime)
            console.run()

            await client.send()
            await asyncio.sleep(0.001)

    loop = asyncio.get_running_loop()
    background_task = loop.create_task(run_background_tasks())

    yield client.c

    console.terminate()
    await background_task
