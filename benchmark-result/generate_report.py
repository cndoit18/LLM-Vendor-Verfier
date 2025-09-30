import json
import os
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional
from datetime import datetime
import math


def extract_vendor_from_filename(filename: str, model: str) -> str:
    """
    Extract vendor name from filename.
    Filename format: summary-{vendor}-{model}.json
    """
    # Remove 'summary-' prefix and '.json' suffix
    name_part = filename.replace("summary-", "").replace(".json", "")

    # Extract model suffix from the model field
    # Model format is typically "vendor/model-name" or just "model-name"
    if "/" in model:
        model_suffix = model.split("/", 1)[1]
    else:
        model_suffix = model

    # Remove the model suffix from the name to get vendor
    # Handle dots in version numbers by replacing them temporarily
    model_pattern = model_suffix.replace(".", "")
    name_normalized = name_part.replace(".", "")

    # Find the model pattern in the normalized name
    # The vendor is everything before the model pattern
    if model_pattern in name_normalized:
        # Find the position of model pattern
        pos = name_normalized.rfind(model_pattern)
        vendor_normalized = name_normalized[:pos].rstrip("-")

        # Map back to original with dots
        # Count hyphens to find the split point
        hyphen_count = vendor_normalized.count("-")
        parts = name_part.split("-")
        vendor = "-".join(parts[: hyphen_count + 1])
    else:
        # Fallback: use the whole name
        vendor = name_part

    return vendor


def load_summary_files(directory: str) -> List[Dict]:
    """Load all summary-*.json files from the directory."""
    summary_files = []
    dir_path = Path(directory)

    for file_path in sorted(dir_path.glob("summary-*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract vendor from filename
            model = data.get("model", "")
            vendor = extract_vendor_from_filename(file_path.name, model)

            data["vendor"] = vendor
            data["filename"] = file_path.name
            summary_files.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return summary_files


def group_by_model(summaries: List[Dict]) -> Dict[str, List[Dict]]:
    """Group summaries by model name."""
    grouped = defaultdict(list)
    for summary in summaries:
        model = summary.get("model", "unknown")
        grouped[model].append(summary)
    return dict(grouped)


def sort_by_successful_tool_calls(summaries: List[Dict]) -> List[Dict]:
    """Sort summaries by successful_tool_call_count in descending order."""
    return sorted(
        summaries, key=lambda x: x.get("successful_tool_call_count", 0), reverse=True
    )


def calculate_euclidean_distance(summary1: Dict, summary2: Dict) -> float:
    """Calculate Euclidean distance between two summaries based on key metrics."""
    # Metrics to use for distance calculation
    metrics = [
        "finish_stop",
        "finish_tool_calls",
        "finish_others",
        "schema_validation_error_count",
        "successful_tool_call_count",
    ]

    # Calculate Euclidean distance
    distance_squared = 0
    for metric in metrics:
        val1 = summary1.get(metric, 0)
        val2 = summary2.get(metric, 0)
        distance_squared += (val1 - val2) ** 2

    return math.sqrt(distance_squared)


def estimate_max_distance(dataset_count: int) -> float:
    """
    Estimate the maximum possible Euclidean distance given the dataset count.

    Worst case scenario:
    - One vendor has all samples as finish_stop (dataset_count, 0, 0, 0, 0)
    - Another has all as successful tool calls (0, dataset_count, 0, 0, dataset_count)

    This gives distance = sqrt(2 * dataset_count^2) = dataset_count * sqrt(2)
    """
    return dataset_count * math.sqrt(5)  # Using 5 metrics


def find_official_vendor(summaries: List[Dict]) -> Optional[Dict]:
    """Find the official vendor (baseline) from the list of summaries."""
    # Look for vendor name containing 'official'
    for summary in summaries:
        vendor = summary.get("vendor", "").lower()
        if "official" in vendor:
            return summary

    # If no official vendor found, return None
    return None


def calculate_similarity_scores(summaries: List[Dict]) -> List[Dict]:
    """
    Calculate similarity scores for all summaries compared to the official vendor.

    Returns a new list with similarity scores added.
    """
    official = find_official_vendor(summaries)

    result_summaries = []
    for summary in summaries:
        summary_with_similarity = summary.copy()

        if official is None:
            # No official vendor found, set similarity to None
            summary_with_similarity["similarity_to_official"] = None
        elif summary is official:
            # Official vendor has 100% similarity to itself
            summary_with_similarity["similarity_to_official"] = 1.0
        else:
            # Calculate similarity for other vendors
            distance = calculate_euclidean_distance(summary, official)
            # Get dataset count from success_count + failure_count
            dataset_count = summary.get("success_count", 0) + summary.get(
                "failure_count", 0
            )
            max_distance = estimate_max_distance(dataset_count)

            # Similarity = 1 - (distance / max_distance)
            similarity = 1.0 - (distance / max_distance) if max_distance > 0 else 0.0
            # Clamp to [0, 1] range
            similarity = max(0.0, min(1.0, similarity))
            summary_with_similarity["similarity_to_official"] = similarity

        result_summaries.append(summary_with_similarity)

    return result_summaries


def generate_markdown_table(grouped_data: Dict[str, List[Dict]]) -> str:
    """Generate markdown table from grouped data."""
    lines = []
    lines.append("# Benchmark Report")
    lines.append("")
    lines.append(f"**Generated at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("This report is auto-generated from all summary JSON files.")
    lines.append("")

    for model, summaries in sorted(grouped_data.items()):
        lines.append(f"## Model: `{model}`")
        lines.append("")

        # Calculate similarity scores
        summaries_with_similarity = calculate_similarity_scores(summaries)

        # Sort by successful_tool_call_count
        sorted_summaries = sort_by_successful_tool_calls(summaries_with_similarity)

        # Create table header
        lines.append(
            "| Vendor | Success Count | Failure Count | Finish Stop | Finish Tool Calls | Finish Others | Schema Validation Errors | **Successful Tool Call Count** | **Similarity to Official** |"
        )
        lines.append(
            "|--------|---------------|---------------|-------------|-------------------|---------------|--------------------------|-------------------------------|---------------------------|"
        )

        # Add table rows
        for summary in sorted_summaries:
            vendor = summary.get("vendor", "unknown")
            success_count = summary.get("success_count", 0)
            failure_count = summary.get("failure_count", 0)
            finish_stop = summary.get("finish_stop", 0)
            finish_tool_calls = summary.get("finish_tool_calls", 0)
            finish_others = summary.get("finish_others", 0)
            schema_errors = summary.get("schema_validation_error_count", 0)
            successful_tool_calls = summary.get("successful_tool_call_count", 0)
            similarity = summary.get("similarity_to_official")

            # Format similarity score
            if similarity is None:
                similarity_str = "N/A"
            else:
                similarity_str = f"{similarity:.4f}"

            lines.append(
                f"| {vendor} | {success_count} | {failure_count} | {finish_stop} | {finish_tool_calls} | {finish_others} | {schema_errors} | **{successful_tool_calls}** | **{similarity_str}** |"
            )

        lines.append("")

    # Add summary statistics
    total_summaries = sum(len(summaries) for summaries in grouped_data.values())
    lines.append("---")
    lines.append("")
    lines.append(f"**Total models**: {len(grouped_data)}")
    lines.append("")
    lines.append(f"**Total vendors**: {total_summaries}")
    lines.append("")

    return "\n".join(lines)


def generate_leaderboard_content(grouped_data: Dict[str, List[Dict]]) -> str:
    """Generate leaderboard content for README.md (tables only, no header)."""
    lines = []

    for model, summaries in sorted(grouped_data.items()):
        lines.append(f"### Model: `{model}`")
        lines.append("")

        # Calculate similarity scores
        summaries_with_similarity = calculate_similarity_scores(summaries)

        # Sort by successful_tool_call_count
        sorted_summaries = sort_by_successful_tool_calls(summaries_with_similarity)

        # Create table header
        lines.append(
            "| Vendor | Success Count | Failure Count | Finish Stop | Finish Tool Calls | Finish Others | Schema Validation Errors | **Successful Tool Call Count** | **Similarity to Official** |"
        )
        lines.append(
            "|--------|---------------|---------------|-------------|-------------------|---------------|--------------------------|-------------------------------|---------------------------|"
        )

        # Add table rows
        for summary in sorted_summaries:
            vendor = summary.get("vendor", "unknown")
            success_count = summary.get("success_count", 0)
            failure_count = summary.get("failure_count", 0)
            finish_stop = summary.get("finish_stop", 0)
            finish_tool_calls = summary.get("finish_tool_calls", 0)
            finish_others = summary.get("finish_others", 0)
            schema_errors = summary.get("schema_validation_error_count", 0)
            successful_tool_calls = summary.get("successful_tool_call_count", 0)
            similarity = summary.get("similarity_to_official")

            # Format similarity score
            if similarity is None:
                similarity_str = "N/A"
            else:
                similarity_str = f"{similarity:.4f}"

            lines.append(
                f"| {vendor} | {success_count} | {failure_count} | {finish_stop} | {finish_tool_calls} | {finish_others} | {schema_errors} | **{successful_tool_calls}** | **{similarity_str}** |"
            )

        lines.append("")

    return "\n".join(lines)


def update_readme(grouped_data: Dict[str, List[Dict]], readme_path: Path):
    """Update the README.md file with the leaderboard content."""
    if not readme_path.exists():
        print(f"README.md not found at {readme_path}")
        return

    # Read current README content
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Generate leaderboard content
    leaderboard_content = generate_leaderboard_content(grouped_data)

    # Find the "## 评估榜单" section
    leaderboard_marker = "## 评估榜单"
    next_section_marker = "## 评估结果"

    # Find the positions
    leaderboard_start = content.find(leaderboard_marker)
    if leaderboard_start == -1:
        print("Warning: '## 评估榜单' section not found in README.md")
        return

    # Find the start of content after the marker (skip the line with the marker)
    content_start = content.find("\n", leaderboard_start) + 1

    # Find the next section
    next_section_start = content.find(next_section_marker, content_start)
    if next_section_start == -1:
        print("Warning: '## 评估结果' section not found after '## 评估榜单'")
        return

    # Construct new content
    new_content = (
        content[:content_start]
        + "\n"
        + leaderboard_content
        + "\n"
        + content[next_section_start:]
    )

    # Write back to README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"README.md updated successfully: {readme_path}")


def main():
    """Main function to generate the report."""
    # Get the directory of this script
    script_dir = Path(__file__).parent

    # Load all summary files
    summaries = load_summary_files(script_dir)

    if not summaries:
        print("No summary files found.")
        return

    print(f"Found {len(summaries)} summary files.")

    # Group by model
    grouped_data = group_by_model(summaries)

    # Generate markdown
    markdown_content = generate_markdown_table(grouped_data)

    # Write to report.md
    output_path = script_dir / "report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Report generated successfully: {output_path}")
    print(f"Total models: {len(grouped_data)}")
    for model, summaries in grouped_data.items():
        print(f"  - {model}: {len(summaries)} vendors")

    # Update README.md with leaderboard
    readme_path = script_dir.parent / "README.md"
    update_readme(grouped_data, readme_path)


if __name__ == "__main__":
    main()
