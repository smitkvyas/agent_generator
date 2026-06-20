"""
Utils for AI module

This module contains the utility functions for the AI module.

Functions:
    format_json_response -- Format the JSON response.
    escape_invalid_json_chars -- Escape invalid JSON characters.
"""

import ast
import json
import re

from loguru import logger


def is_valid_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False


def format_json_response(response: str) -> dict:
    """
    Format the JSON response with auto-detection and fallback sanitization.

    Args:
        response (str): Raw response from model.

    Returns:
        dict: Parsed JSON object.
    """
    logger.debug("Raw response in  format_json_response:", response)
    # Case 1: Markdown JSON block
    if response.startswith("```json"):
        match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if match:
            logger.debug("Markdown JSON block detected in format_json_response")
            json_text = match.group(1)
            logger.debug("Extracted JSON text in format_json_response:", json_text)
            return json.loads(json_text)
        raise ValueError("Invalid JSON block format")

    # Case 2: Already valid JSON
    if is_valid_json(response):
        logger.debug("Valid JSON detected in format_json_response")
        return json.loads(response)

    # Case 3: JSON is a literal string
    try:
        evaluated = ast.literal_eval(response)
        logger.debug("Evaluated response in format_json_response:", evaluated)
        if is_valid_json(evaluated):
            return json.loads(evaluated)
    except Exception:
        pass

    # Case 4: Apply fallback sanitization
    try:
        logger.debug("Applying fallback sanitization in format_json_response", response)
        response = escape_invalid_json_chars(response)
        logger.debug("After escaping invalid chars in format_json_response:", response)
        response = quote_unquoted_keys(response)
        logger.debug("Sanitized response in format_json_response:", response)
        return json.loads(response)
    except Exception as e:
        raise ValueError(f"Unable to parse or sanitize JSON: {e}")


def escape_invalid_json_chars(json_string: str) -> str:
    """
    Escapes unescaped special characters inside JSON strings, including:
    - Newlines (\n)
    - Carriage returns (\r)
    - Tabs (\t)
    - Unescaped double quotes within a string

    Arguments:
        json_string (str): The JSON string to process.

    Returns:
        str: The cleaned JSON string
    """

    result = []
    in_string = False
    escape_next = False
    length = len(json_string)
    i = 0

    while i < length:
        char = json_string[i]

        if escape_next:
            # Preserve valid escape sequences
            result.append("\\" + char)
            escape_next = False

        elif char == "\\":
            # Start of an escape sequence
            escape_next = True

        elif char == '"':
            if in_string:
                # Verify if it's a closing quote
                j = i + 1
                while j < length and json_string[j].isspace():
                    j += 1
                if j == length or json_string[j] in {",", "}", "]", ":"}:
                    in_string = False  # Closing quote
                else:
                    result.append("\\")  # Escape unescaped quotes
            else:
                in_string = True  # Start of a string
            result.append(char)

        elif in_string:
            # Escape special characters inside JSON strings
            if char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(char)

        else:
            result.append(char)

        i += 1

    return "".join(result)


def quote_unquoted_keys(json_string: str) -> str:
    """
    Adds quotes around unquoted keys in a JSON string.

    Args:
        json_string (str): The JSON string to process.

    Returns:
        str: The JSON string with quotes around unquoted keys.
    """
    pattern = r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)"
    return re.sub(pattern, r'\1"\2"\3', json_string)
