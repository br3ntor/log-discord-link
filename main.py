#!/usr/bin/env python3

import asyncio

from log_watcher import LogMonitor


async def main():
    def process_line(line: str):
        print(line)

    # Project Zomboid test_pzserver
    testpz_log_directory = "/home/test_pzserver/Zomboid/Logs/"
    testpz_log_monitor = LogMonitor(testpz_log_directory, "*chat.txt", process_line)

    # Project Zomboid heavy_pzserver
    heavypz_log_directory = "/home/heavy_pzserver/log/console/"
    heavypz_log_monitor = LogMonitor(
        heavypz_log_directory, "pzserver-console.log", process_line
    )

    await asyncio.gather(testpz_log_monitor.start(), heavypz_log_monitor.start())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down")
