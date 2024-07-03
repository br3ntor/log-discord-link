"""Functions to parse each log line and return text ready to send to discord."""

import re


def parse_zomboid_chat(log_line: str) -> str | None:
    if "Got message:" not in log_line:
        return None

    # Simplified regex pattern to match the components
    pattern = r"ChatMessage\{chat=(.*?), author='(.*?)', text='(.*?)'\}"

    match = re.search(pattern, log_line)

    if match is None:
        return None

    chat = match.group(1)
    author = match.group(2)
    text = match.group(3)

    if chat != "General":
        return None

    formatted_text = f"{author}: {text}"

    print(formatted_text)
    return formatted_text


def parse_valheim_chat(log_line: str) -> str | None:
    if "Console:" not in log_line:
        return None

    pattern = r"(<color=.*?>)(.*?)(</color>)"
    matches = re.findall(pattern, log_line)

    print(matches)

    # Extract only the text from each match and create a list
    extracted_text = [
        match[1] for match in matches
    ]  # match[1] is the text between tags

    formatted_text = ": ".join(extracted_text)

    print(formatted_text)  # Output: ["Peebody", "I HAVE ARRIVED!"]
    return formatted_text
