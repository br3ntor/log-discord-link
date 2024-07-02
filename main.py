#!/usr/bin/env python3

import asyncio
import logging
import os

import discord
from dotenv import load_dotenv

from log_watcher import LogMonitor

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def send_to_discord(message: str, channel_id: int):
    channel = client.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def monitor_logs():
    async def process_line(line: str):
        print(line)
        await send_to_discord(line, 1257565711816069161)

    # Project Zomboid test_pzserver
    testpz_log_directory = "/home/test_pzserver/Zomboid/Logs/"
    testpz_log_monitor = LogMonitor(testpz_log_directory, "*chat.txt", process_line)

    # Project Zomboid heavy_pzserver
    # heavypz_log_directory = "/home/heavy_pzserver/Zomboid/Logs/"
    # heavypz_log_monitor = LogMonitor(heavypz_log_directory, "*chat.txt", process_line)
    # Project Zomboid heavy_pzserver
    heavypz_log_directory = "/home/heavy_pzserver/log/console/"
    heavypz_log_monitor = LogMonitor(
        heavypz_log_directory, "pzserver-console.log", process_line
    )

    await asyncio.gather(testpz_log_monitor.start(), heavypz_log_monitor.start())
    # await testpz_log_monitor.start()
    # await heavypz_log_monitor.start()


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    print("Starting log monitor...")
    client.loop.create_task(monitor_logs())


@client.event
async def on_disconnect():
    print("Disconnect event")


if __name__ == "__main__":
    try:
        load_dotenv()
        logging.basicConfig(level=logging.INFO)
        token = os.getenv("TOKEN")
        if isinstance(token, str):
            client.run(token)

        # asyncio.run(monitor_logs())
    except KeyboardInterrupt:
        print("Shutting down")
