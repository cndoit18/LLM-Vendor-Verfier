"""
Convert glaive_toolcall_zh dataset to samples.jsonl format for tool call validation.

This script extracts conversations that end with a function_call and formats them
for testing DeepSeek's tool call capability (without tool role support).
"""

import json
import sys
from pathlib import Path
from loguru import logger


def parse_tools(tools_str: str) -> list[dict]:
    """Parse tools string and convert to OpenAI function calling format."""
    tools_list = json.loads(tools_str)
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {}),
            },
        }
        for tool in tools_list
    ]


def convert_conversation(conversations: list[dict]) -> list[dict]:
    """
    Convert conversation format to OpenAI messages format.

    Only include messages up to the first function_call to test the model's
    ability to generate tool calls from scratch.

    Mapping:
    - human -> user
    - gpt -> assistant (only if before function_call)
    - function_call -> expected output (not included in input messages)
    - observation -> skip (tool role not supported)
    """
    messages = []

    for conv in conversations:
        role = conv.get("from")
        value = conv.get("value", "")

        if role == "human":
            messages.append({"role": "user", "content": value})
        elif role == "gpt":
            messages.append({"role": "assistant", "content": value})
        elif role == "function_call":
            # Stop here - this is what we want the model to generate
            break
        # Skip observation (tool role)

    return messages


def extract_first_function_call(conversations: list[dict]) -> dict | None:
    """Extract the first function call for reference."""
    for conv in conversations:
        if conv.get("from") == "function_call":
            try:
                return json.loads(conv.get("value", "{}"))
            except json.JSONDecodeError:
                return None
    return None


def should_include_sample(conversations: list[dict]) -> bool:
    """
    Determine if this sample should be included.

    Include if:
    1. Has at least one function_call
    2. Has user input before function_call
    """
    has_function_call = any(c.get("from") == "function_call" for c in conversations)
    has_user_input = any(c.get("from") == "human" for c in conversations)

    return has_function_call and has_user_input


def convert_dataset(
    input_file: str,
    output_file: str,
    model: str = "deepseek-chat",
    temperature: float = 0.0,
    max_tokens: int = 4096,
    user: str = "test-user",
):
    """Convert the dataset to samples.jsonl format."""

    logger.info(f"Reading dataset from {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    logger.info(f"Total samples in dataset: {len(dataset)}")

    converted_samples = []
    skipped_count = 0

    for idx, item in enumerate(dataset):
        conversations = item.get("conversations", [])
        tools_str = item.get("tools", "[]")

        # Check if this sample is valid
        if not should_include_sample(conversations):
            skipped_count += 1
            continue

        try:
            # Convert messages
            messages = convert_conversation(conversations)

            # Skip if no messages or no user message
            if not messages or not any(m["role"] == "user" for m in messages):
                skipped_count += 1
                continue

            # Parse tools
            tools = parse_tools(tools_str)

            if not tools:
                skipped_count += 1
                continue

            # Get expected function call for reference (optional)
            expected_call = extract_first_function_call(conversations)

            # Create sample (only include API-compatible fields)
            sample = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
                "user": user,
                "tools": tools,
            }

            converted_samples.append(sample)

        except Exception as e:
            logger.warning(f"Error converting sample {idx}: {e}")
            skipped_count += 1
            continue

    logger.info(f"Converted {len(converted_samples)} samples")
    logger.info(f"Skipped {skipped_count} samples")

    # Write to JSONL
    logger.info(f"Writing to {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in converted_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    logger.info("Conversion complete!")

    # Print statistics
    print("\n" + "=" * 60)
    print("Conversion Statistics")
    print("=" * 60)
    print(f"Total input samples: {len(dataset)}")
    print(f"Successfully converted: {len(converted_samples)}")
    print(f"Skipped: {skipped_count}")
    print(f"Output file: {output_file}")
    print("=" * 60 + "\n")

    # Sample preview
    if converted_samples:
        print("Sample preview (first item):")
        print(
            json.dumps(converted_samples[0], ensure_ascii=False, indent=2)[:500] + "..."
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert glaive_toolcall_zh dataset to samples.jsonl"
    )
    parser.add_argument(
        "--input",
        default="Z:/works/huggingface.co/datasets/glaive_toolcall_zh/glaive_toolcall_zh_1k.json",
        help="Input dataset JSON file",
    )
    parser.add_argument(
        "--output",
        default="samples-deepseek.jsonl",
        help="Output JSONL file",
    )
    parser.add_argument(
        "--model",
        default="deepseek-chat",
        help="Model name to use in requests",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for generation (default: 0.0 for deterministic testing)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max tokens for generation",
    )
    parser.add_argument(
        "--user",
        default="test-user",
        help="User identifier for requests",
    )

    args = parser.parse_args()

    convert_dataset(
        input_file=args.input,
        output_file=args.output,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        user=args.user,
    )
