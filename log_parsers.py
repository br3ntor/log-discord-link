"""Functions to parse each log line and return text ready to send to discord."""

import re


def parse_zomboid_chat(log_line: str) -> str | None:
    if "Got Message:" not in log_line:
        return None
    # Split the text by curly braces
    parts = log_line.split("{", 1)[1].split("}")[0].split(",")

    # Extract key-value pairs and remove quotes
    extracted_data = {
        part.split("=")[0].strip(): part.split("=")[1].strip("'") for part in parts
    }
    formatted_text = extracted_data["author"] + ": " + extracted_data["text"]
    print(extracted_data)
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
