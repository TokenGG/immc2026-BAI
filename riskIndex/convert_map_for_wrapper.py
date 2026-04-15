#!/usr/bin/env python3
"""
Convert map generator output to wrapper format.
"""

import json
import sys
import argparse


def convert_map_for_wrapper(input_file: str, output_file: str):
    """
    Convert map generator output (with num_cols/num_rows) to wrapper format (with map_width/map_height).

    Args:
        input_file: Input JSON file from map generator
        output_file: Output JSON file for wrapper
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    map_config = data['map_config']

    # Rename num_cols/num_rows to map_width/map_height
    if 'num_cols' in map_config:
        map_config['map_width'] = map_config.pop('num_cols')
    if 'num_rows' in map_config:
        map_config['map_height'] = map_config.pop('num_rows')

    # Ensure x/y coordinates exist in grids
    for grid in data['grids']:
        if 'x' not in grid:
            grid['x'] = grid.get('hex_col', 0)
        if 'y' not in grid:
            grid['y'] = grid.get('hex_row', 0)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Converted {input_file} -> {output_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Convert Map to Wrapper Format - Convert map generator output for use with risk_model_wrapper.py"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Input JSON file from map generator"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Output JSON file for wrapper"
    )

    args = parser.parse_args()

    convert_map_for_wrapper(args.input, args.output)


if __name__ == "__main__":
    main()
