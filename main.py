#!/usr/bin/env python3

import asyncio
import glob
import os
import subprocess
from collections.abc import Callable


# TODO: Package it into my own module and upload to github perhaps
class LogMonitor:
    """
    Watches the contents of a log file and its
    name on the file system. If the file name changes it will
    start watching the new log file. The file name is watched
    through polling and we don't care if the first few lines
    are not caught.
    """

    def __init__(
        self,
        log_directory: str,
        log_file_pattern: str,
        line_callback: Callable[[str], None],
    ):
        self.log_directory = log_directory
        self.log_file_pattern = log_file_pattern
        self.line_callback = line_callback
        self.current_log_file = None
        self.current_task = None
        self.process = None

    async def tail_log(self, file_path: str, line_callback: Callable[[str], None]):
        """Uses tail to get newly logged line an run the callback on it."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                "tail",
                "-f",  # Use -f as log file names are unique when created
                file_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if self.process.stdout is None:
                print("Failed to access log")
                return

            print("Tailing new log file:")
            async for line in self.process.stdout:
                decoded_line = line.decode("utf-8").strip()
                line_callback(decoded_line)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.process:
                self.process.terminate()
                print("Terminated old process.")

    async def watch_log(
        self,
    ):
        """Responsible for watching the correct file name, expecting it
        will change when the program creating the log restarts."""
        while True:
            log_files = glob.glob(
                os.path.join(self.log_directory, self.log_file_pattern)
            )
            if log_files:
                # If there are ever more than one log file this will select newest
                latest_log_file = max(log_files, key=os.path.getctime)

                if latest_log_file != self.current_log_file:
                    print(f"New log file detected: {latest_log_file}")

                    if self.current_task:
                        self.current_task.cancel()
                        try:
                            await self.current_task
                        except asyncio.CancelledError:
                            print(f"Task cancelled for: {self.current_log_file}")
                        else:
                            print("what the...")
                            return

                    self.current_log_file = latest_log_file
                    self.current_task = asyncio.create_task(
                        self.tail_log(self.current_log_file, self.line_callback)
                    )
            else:
                print("No log file, server restarting? Waiting for fresh log file...")

            await asyncio.sleep(5)


async def main():
    def process_line(line: str):
        print(line)

    log_directory = "/home/test_pzserver/Zomboid/Logs/"
    log_monitor = LogMonitor(log_directory, "*chat.txt", process_line)

    await log_monitor.watch_log()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down")
