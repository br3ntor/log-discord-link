"""
For watching log files that get new names
on log rotation. For example, the log name
contains the file creation date and time.
"""

import asyncio
import glob
import os
import subprocess
from typing import Callable, Coroutine


class LogMonitor:
    """
    Watches the contents of a log file and its
    name on the file system. If the file name changes it will
    start watching the new log file. The file name is watched
    through polling and we don't care if the first few lines
    are not caught.

    Attributes:
        log_directory: Directory containing log file.
        log_file_pattern: A pattern to match a log file with
                            unique name or just the filename.
        line_callback: Function to handle new log lines.
    """

    def __init__(
        self,
        log_directory: str,
        log_file_pattern: str,
        line_callback: Callable[[str], Coroutine],
    ):
        self.log_directory = log_directory
        self.log_file_pattern = log_file_pattern
        self.line_callback = line_callback
        self.current_log_file = None
        self.current_task = None
        self.process = None

    async def tail_log(self, file_path: str):
        """Uses tail to get newly logged line, then run the callback on it.
        Use this if file name doesn't change on restart."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                "tail",
                "-Fn 1",
                file_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if self.process.stdout is None:
                print("Failed to access log")
                return

            print(f"Tailing log file: {file_path}")
            async for line in self.process.stdout:
                decoded_line = line.decode("utf-8").strip()
                await self.line_callback(decoded_line)

        except asyncio.CancelledError:
            print(f"TL:Task cancelled for: {file_path}")
        finally:
            if self.process:
                try:
                    print(self.process)
                    self.process.terminate()
                    await self.process.wait()
                    print("Terminated old process.")
                except ProcessLookupError as ple:
                    print("ProcessLookupError: Process already stopped.")
                    print(ple)

    async def watch_log(
        self,
    ):
        """Will tail log, watch the file name, and update tail if the log
        file name changes when program making the log restarts. Use this
        if the log filename changes on restarts."""
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
                            print(f"WL:Task cancelled for: {self.current_log_file}")

                    self.current_log_file = latest_log_file
                    self.current_task = asyncio.create_task(
                        self.tail_log(self.current_log_file)
                    )
            else:
                print("No log file, server restarting? Waiting for fresh log file...")

            await asyncio.sleep(5)

    async def start(self):
        """Start watching the log."""
        log_files = glob.glob(os.path.join(self.log_directory, self.log_file_pattern))

        if log_files:
            latest_log_file = max(log_files, key=os.path.getctime)
        else:
            print("No log file.")
            return

        # I really only want to look for * in my case
        glob_chars = ["*", "?", "[", "]"]
        has_glob_chars = any([True for g in glob_chars if g in self.log_file_pattern])
        if has_glob_chars:
            await self.watch_log()
        else:
            asyncio.create_task(self.tail_log(latest_log_file))
