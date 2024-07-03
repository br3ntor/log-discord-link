#!/usr/bin/env python3

import asyncio
import logging
import os

import discord
from dotenv import load_dotenv

from log_parsers import parse_valheim_chat, parse_zomboid_chat
from log_watcher import RealTimeLogProcessor

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def send_to_discord(message: str, channel_id: int):
    channel = client.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def monitor_logs():

    # RealTimeLogProcessor callback functions to prep and send game chat to discord

    async def process_pel_chat(line: str):
        parsed_line = parse_zomboid_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 1257565711816069161)

    async def process_heavy_chat(line: str):
        parsed_line = parse_zomboid_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 1257565711816069161)

    async def process_valheim_chat(line: str):
        parsed_line = parse_valheim_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 1249231130901610628)

    # Project Zomboid pel_pzserver
    pelpz_log_directory = "/home/pel_pzserver/Zomboid/Logs/"
    pelpz_log_monitor = RealTimeLogProcessor(
        pelpz_log_directory, "*chat.txt", process_pel_chat
    )

    # Project Zomboid heavy_pzserver
    heavypz_log_directory = "/home/heavy_pzserver/Zomboid/Logs/"
    heavypz_log_monitor = RealTimeLogProcessor(
        heavypz_log_directory, "*chat.txt", process_heavy_chat
    )

    # Valheim server
    valheim_log_directory = "/home/vhserver/log/console/"
    valheim_log_monitor = RealTimeLogProcessor(
        valheim_log_directory, "vhserver-console.log", process_valheim_chat
    )

    await asyncio.gather(
        pelpz_log_monitor.start(),
        heavypz_log_monitor.start(),
        valheim_log_monitor.start(),
    )


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

    except KeyboardInterrupt:
        print("Shutting down")
