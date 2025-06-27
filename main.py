#!/usr/bin/env python3

import asyncio
import logging
import os

import discord
from aiohttp.client_exceptions import ClientConnectorError, ServerDisconnectedError
from discord.errors import Forbidden, HTTPException, NotFound
from dotenv import load_dotenv

from log_parsers import parse_valheim_chat, parse_zomboid_chat
from log_watcher import RealTimeLogProcessor

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def send_to_discord(message: str, channel_id: int):
    """
    Sends a message to the specified Discord channel with built-in
    retry logic for network and API errors.

    Args:
        message (str): The message content to send.
        channel_id (int): The ID of the Discord channel to send the message to.
    """
    max_retries = 5  # Maximum number of times to retry sending the message
    initial_delay = 5  # Initial delay in seconds before the first retry

    # Attempt to retrieve the channel outside the retry loop, as this
    # operation is less likely to fail due to transient network issues
    # and more likely due to incorrect ID or bot not being fully ready.
    channel = client.get_channel(channel_id)

    if not isinstance(channel, discord.TextChannel):
        logging.error(
            f"Channel with ID {channel_id} not found or is not a text channel. "
            f"Cannot send message: '{message}'."
        )
        return  # Exit if the channel is invalid

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(
                f"Attempt {attempt}/{max_retries}: Sending message to channel {channel_id}..."
            )
            await channel.send(message)
            logging.info(f"Successfully sent message to channel {channel_id}.")
            return  # Message sent successfully, exit function

        except (ClientConnectorError, ServerDisconnectedError) as e:
            # These exceptions indicate a problem connecting to Discord (network issue)
            logging.warning(
                f"Network error while sending to Discord (Attempt {attempt}/{max_retries}): {e}"
            )
            if attempt < max_retries:
                # Calculate exponential backoff delay
                delay = initial_delay * (2 ** (attempt - 1))
                logging.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
            else:
                logging.error(
                    f"Failed to send message after {max_retries} attempts due to persistent network error."
                )

        except (HTTPException, NotFound, Forbidden) as e:
            # These are discord.py specific exceptions for API errors
            # NotFound: Channel doesn't exist, Forbidden: Bot lacks permissions, HTTPException: General API error
            logging.error(
                f"Discord API error while sending to channel {channel_id} (Attempt {attempt}/{max_retries}): {e}"
            )
            # For these errors, retrying might not help if the issue is persistent (e.g., wrong channel ID, permissions).
            # We'll log and then break the loop to avoid endless retries on unresolvable issues.
            break  # Do not retry for these types of specific Discord API errors

        except Exception as e:
            # Catch any other unexpected exceptions
            logging.error(
                f"An unexpected error occurred while sending to Discord (Attempt {attempt}/{max_retries}): {e}"
            )
            if attempt < max_retries:
                delay = initial_delay * (2 ** (attempt - 1))
                logging.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
            else:
                logging.error(
                    f"Failed to send message after {max_retries} attempts due to an unexpected error."
                )

    logging.error(
        f"Message '{message}' could not be sent to channel {channel_id} after all attempts."
    )


# TODO: Make less DRY
async def monitor_logs():

    # RealTimeLogProcessor callback functions to prep and send game chat to discord

    async def process_test_chat(line: str):
        parsed_line = parse_zomboid_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 1257565711816069161)

    async def process_pzserver_chat(line: str):
        parsed_line = parse_zomboid_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 1381876552769208330)

    async def process_heavy_chat(line: str):
        parsed_line = parse_zomboid_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 950156506735730719)

    async def process_valheim_chat(line: str):
        parsed_line = parse_valheim_chat(line)
        if parsed_line:
            await send_to_discord(parsed_line, 1249231130901610628)

    # Project Zomboid test_pzserver
    # testpz_log_directory = "/home/test_pzserver/Zomboid/Logs/"
    # testpz_log_monitor = RealTimeLogProcessor(
    #     testpz_log_directory, "*chat.txt", process_test_chat
    # )

    # Project Zomboid Modded
    pzserver_log_directory = "/home/pzserver/Zomboid/Logs/"
    pzserver_log_monitor = RealTimeLogProcessor(
        pzserver_log_directory, "*chat.txt", process_pzserver_chat
    )

    # Project Zomboid heavy_pzserver
    # heavypz_log_directory = "/home/heavy_pzserver/Zomboid/Logs/"
    # heavypz_log_monitor = RealTimeLogProcessor(
    #     heavypz_log_directory, "*chat.txt", process_heavy_chat
    # )

    # Valheim server
    # valheim_log_directory = "/home/vhserver/log/console/"
    # valheim_log_monitor = RealTimeLogProcessor(
    #     valheim_log_directory, "vhserver-console.log", process_valheim_chat
    # )

    await asyncio.gather(
        # testpz_log_monitor.start(),
        pzserver_log_monitor.start(),
        # heavypz_log_monitor.start(),
        # valheim_log_monitor.start(),
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
