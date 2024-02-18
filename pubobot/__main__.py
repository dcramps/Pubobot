#!/usr/bin/python3
# encoding: utf-8
import time, asyncio, os

#my modules
from . import console, config, bot, client, scheduler, stats3

console.init()
scheduler.init()
bot.init()
stats3.init()
config.init()
client.init()

async def bot_run(): #background thinking
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
			

client.c.loop.create_task(bot_run())
client.run() #runs until ctrl+c
