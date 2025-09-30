"""Analyze the generated samples to provide statistics."""

import json
from collections import Counter, defaultdict
from pathlib import Path


def analyze_samples(file_path: str):
    """Analyze samples.jsonl and print statistics."""

    samples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            samples.append(json.loads(line))

    # Basic statistics
    total_samples = len(samples)

    # Tool statistics
    tool_names = []
    tool_param_counts = []
    message_counts = []
    user_message_counts = []
    assistant_message_counts = []

    for sample in samples:
        # Count messages
        messages = sample.get("messages", [])
        message_counts.append(len(messages))
        user_msg_count = sum(1 for m in messages if m.get("role") == "user")
        assistant_msg_count = sum(1 for m in messages if m.get("role") == "assistant")
        user_message_counts.append(user_msg_count)
        assistant_message_counts.append(assistant_msg_count)

        # Count tools
        tools = sample.get("tools", [])
        for tool in tools:
            func = tool.get("function", {})
            tool_names.append(func.get("name", "unknown"))
            params = func.get("parameters", {}).get("properties", {})
            tool_param_counts.append(len(params))

    # Calculate statistics
    tool_name_counter = Counter(tool_names)
    unique_tools = len(tool_name_counter)

    print("=" * 70)
    print("DeepSeek Tool Call Test Set Analysis")
    print("=" * 70)
    print()

    print(f"📊 Basic Statistics")
    print(f"  Total samples: {total_samples}")
    print(f"  Unique tool types: {unique_tools}")
    print()

    print(f"💬 Message Statistics")
    print(f"  Avg messages per sample: {sum(message_counts) / len(message_counts):.2f}")
    print(f"  Min messages: {min(message_counts)}")
    print(f"  Max messages: {max(message_counts)}")
    print(f"  Single-turn samples: {sum(1 for c in message_counts if c == 1)}")
    print(f"  Multi-turn samples: {sum(1 for c in message_counts if c > 1)}")
    print()

    print(f"🔧 Tool Statistics")
    print(
        f"  Avg parameters per tool: {sum(tool_param_counts) / len(tool_param_counts):.2f}"
    )
    print(f"  Min parameters: {min(tool_param_counts)}")
    print(f"  Max parameters: {max(tool_param_counts)}")
    print()

    print(f"🔝 Top 20 Most Common Tools")
    for idx, (tool_name, count) in enumerate(tool_name_counter.most_common(20), 1):
        percentage = (count / total_samples) * 100
        print(f"  {idx:2d}. {tool_name:40s} {count:4d} ({percentage:5.2f}%)")

    print()

    # Conversation complexity
    single_turn = sum(1 for c in user_message_counts if c == 1)
    multi_turn = sum(1 for c in user_message_counts if c > 1)

    print(f"🗣️ Conversation Complexity")
    print(
        f"  Single-turn (1 user message): {single_turn} ({single_turn/total_samples*100:.2f}%)"
    )
    print(
        f"  Multi-turn (2+ user messages): {multi_turn} ({multi_turn/total_samples*100:.2f}%)"
    )
    print()

    # Parameter complexity distribution
    param_distribution = Counter(tool_param_counts)
    print(f"📋 Parameter Complexity Distribution")
    for param_count in sorted(param_distribution.keys()):
        count = param_distribution[param_count]
        percentage = (count / total_samples) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {param_count:2d} params: {count:4d} ({percentage:5.2f}%) {bar}")

    print()
    print("=" * 70)
    print(f"✓ Analysis complete for {file_path}")
    print("=" * 70)


if __name__ == "__main__":
    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else "samples-deepseek.jsonl"

    if not Path(file_path).exists():
        print(f"Error: {file_path} not found!")
        sys.exit(1)

    analyze_samples(file_path)
