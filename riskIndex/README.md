# Protected Area Grid Risk Index Model

A comprehensive mathematical model for calculating risk coefficients in wildlife protected areas to guide optimal allocation of patrol and monitoring resources.

## Features

- **Core Risk Model**: Human risk, Environmental risk, Species density calculations
- **Temporal Factors**: Diurnal and seasonal risk variations
- **Automatic Distance Calculation**: Auto-calculate distances from grid coordinates
- **Spatial-Temporal Risk Field**: Continuous interpolation across space and time
- **DSSA Algorithm**: Drone Swarm Scheduling Algorithm for patrol optimization
- **Visualization**: Risk heatmaps, component analysis, and temporal comparisons
- **Data Generation**: Synthetic data for testing and validation
- **Wrapper Script**: JSON-based configuration and data file I/O
- **Map Generation**: Square and hexagon grid map generators with configurable features
- **Feature Configuration**: JSON-based feature configuration (ponds, forests, mountains, etc.)
- **Heatmap Visualization**: Risk heatmap visualization from wrapper output

## Project Structure

```
riskIndex/
├── src/risk_model/
│   ├── core/              # Core data structures
│   ├── risk/              # Risk calculators
│   ├── data/              # Data generation and I/O
│   ├── config/            # Configuration management
│   ├── visualization/     # Plotting and visualization
│   └── advanced/          # IMMC enhancements
├── tests/                 # Unit tests
├── examples/              # Example scripts
├── plots/                 # Generated plots
├── demo_phase*.py              # Phase demonstration scripts
├── risk_model_wrapper.py        # Wrapper script for JSON file I/O
├── generate_hex_map.py          # Hexagon grid map generator
├── generate_square_map.py       # Square grid map generator
├── convert_map_for_wrapper.py   # Convert map data for wrapper
├── visualize_risk_from_json.py  # Risk heatmap visualizer
├── map_feature_config.json      # Map feature configuration
├── example_data.json            # Example input data
├── example_config.json          # Example configuration
└── example_results.json         # Example output results
```

## Quick Start

### Using the Wrapper Script

```bash
# Run with example data
python3 risk_model_wrapper.py --data example_data.json --config example_config.json --output results.json
```

### Run All Demos

```bash
# Phase 1: Core Model Implementation
python3 demo_phase1.py

# Phase 2: Risk Integration & Normalization
python3 demo_phase2.py

# Phase 3: Data Generation & Input/Output
python3 demo_phase3.py

# Phase 4: Visualization
python3 demo_phase4.py

# Phase 5: Testing & Validation
python3 demo_phase5.py

# Phase 6: Advanced Features (IMMC Enhancements)
python3 demo_phase6.py
```

## Coordinate System

The model uses a grid-based coordinate system:
- **Origin**: Bottom-left grid cell center
- **X-axis**: Increases to the right (column index)
- **Y-axis**: Increases upward (row index)
- **Distance Calculation**: Euclidean distance used for automatic distance computation

## Wrapper Script Usage

### Input Data Format (`data.json`)

```json
{
  "map_config": {
    "map_width": 10,
    "map_height": 6,
    "boundary_type": "RECTANGLE",
    "road_locations": [[2, 3], [5, 7]],
    "water_locations": [[1, 1], [8, 5]]
  },
  "grids": [
    {
      "grid_id": "A01",
      "x": 0,
      "y": 0,
      "fire_risk": 0.8,
      "terrain_complexity": 0.7,
      "vegetation_type": "FOREST",
      "species_densities": {
        "rhino": 0.9,
        "elephant": 0.7,
        "bird": 0.5
      }
    }
  ],
  "time": {
    "hour_of_day": 22,
    "season": "RAINY"
  }
}
```

### Configuration Format (`config.json`)

```json
{
  "risk_weights": {
    "human_weight": 0.4,
    "environmental_weight": 0.3,
    "density_weight": 0.3
  },
  "human_risk_weights": {
    "boundary_weight": 0.4,
    "road_weight": 0.35,
    "water_weight": 0.25
  },
  "environmental_risk_weights": {
    "fire_weight": 0.6,
    "terrain_weight": 0.4
  }
}
```

## Map Feature Configuration

Configure which map features to generate using `map_feature_config.json`. Set `1` to enable, `0` to disable.

### Feature Configuration Format

```json
{
  "features": {
    "ponds": 1,
    "large_water": 0,
    "forest": 1,
    "shrub": 1,
    "grassland": 1,
    "rhino": 1,
    "elephant": 1,
    "bird": 1,
    "roads": 1,
    "mountain": 0,
    "hills": 0
  },
  "vegetation_distribution": {
    "grassland_ratio": 0.35,
    "forest_ratio": 0.40,
    "shrub_ratio": 0.25
  },
  "water_config": {
    "pond_count": 3,
    "pond_min_radius": 2.0,
    "pond_max_radius": 4.0,
    "large_water_radius": 8.0,
    "has_river": 1
  },
  "road_config": {
    "main_road_count": 3,
    "curvature": 0.35,
    "branch_probability": 0.12
  },
  "terrain_config": {
    "mountain_count": 2,
    "mountain_radius": 4.0,
    "hill_count": 5,
    "hill_radius": 2.5
  }
}
```

### Available Features

| Feature | Description |
|---------|-------------|
| `ponds` | Water ponds (small circular water bodies) |
| `large_water` | Large single water body (lake) |
| `forest` | Forest vegetation type |
| `shrub` | Shrub vegetation type |
| `grassland` | Grassland vegetation type |
| `rhino` | Rhino species density |
| `elephant` | Elephant species density |
| `bird` | Bird species density |
| `roads` | Curved roads with branches |
| `mountain` | Mountain terrain (increases terrain complexity) |
| `hills` | Hill terrain (moderately increases terrain complexity) |

## Hexagon Map Generator

Generate rectangular hexagon grid maps with curved roads and water features.

### Basic Usage

```bash
# Generate map with default settings (15 cols × 12 rows)
python3 generate_hex_map.py
```

### Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--cols` | `-c` | 15 | Number of columns in hex grid |
| `--rows` | `-r` | 12 | Number of rows in hex grid |
| `--data` | `-d` | rect_hex_map_data.json | Output JSON data file path |
| `--map-image` | `-m` | rect_hex_map_features.jpg | Output map features image path |
| `--config` | `-f` | map_feature_config.json | Feature configuration JSON file path |
| `--help` | `-h` | - | Show help message |

### Examples

```bash
# Show help
python3 generate_hex_map.py --help

# Generate 20 cols × 15 rows map
python3 generate_hex_map.py --cols 20 --rows 15

# Generate with custom feature configuration
python3 generate_hex_map.py --cols 20 --rows 15 --config my_config.json

# Custom output file names
python3 generate_hex_map.py --cols 25 --rows 18 --data my_map.json --map-image my_map.jpg

# Using short options
python3 generate_hex_map.py -c 20 -r 15 -f my_config.json -d output.json
```

### Features

- **Rectangular Boundary**: Hexagon grid with rectangular outer boundary
- **Configurable Features**: Enable/disable features via JSON config
- **Curved Roads**: Random walk generated roads with branching
- **Water Features**: Ponds + winding river + large lakes
- **Terrain Features**: Mountains and hills (new)
- **No Grid Borders**: Hexagon borders are hidden (linewidth=0)
- **Even-Q Offset Coordinates**: Uses offset coordinates for rectangular grid layout

## Square Map Generator

Generate square grid maps with curved roads and water features.

### Basic Usage

```bash
# Generate map with default settings (40 cols × 30 rows)
python3 generate_square_map.py
```

### Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--cols` | `-c` | 30 | Number of columns in square grid |
| `--rows` | `-r` | 20 | Number of rows in square grid |
| `--data` | `-d` | square_map_data.json | Output JSON data file path |
| `--map-image` | `-m` | square_map_features.jpg | Output map features image path |
| `--config` | `-f` | map_feature_config.json | Feature configuration JSON file path |
| `--help` | `-h` | - | Show help message |

### Examples

```bash
# Show help
python3 generate_square_map.py --help

# Generate 50 cols × 25 rows map
python3 generate_square_map.py --cols 50 --rows 25

# Generate with custom feature configuration
python3 generate_square_map.py --cols 50 --rows 25 --config my_config.json

# Custom output file names
python3 generate_square_map.py --cols 100 --rows 50 --data my_map.json --map-image my_map.jpg
```

## Map to Wrapper Converter

Convert map generator output to wrapper format (renames `num_cols`/`num_rows` to `map_width`/`map_height` and ensures coordinates exist).

### Basic Usage

```bash
python3 convert_map_for_wrapper.py --input map_data.json --output map_for_wrapper.json
```

### Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--input` | `-i` | required | Input JSON file from map generator |
| `--output` | `-o` | required | Output JSON file for wrapper |

## Complete Workflow: Map → Risk Calculation → Heatmap

This is the recommended workflow for generating risk heatmaps from scratch.

### Step 1: Generate Map Data

Choose either square or hexagon grid, with optional feature configuration:

```bash
# Square grid map (100×50) with default features
python3 generate_square_map.py --cols 100 --rows 50 --data map_data.json

# Square grid map with custom feature configuration
python3 generate_square_map.py --cols 100 --rows 50 --config map_feature_config.json --data map_data.json

# OR Hexagon grid map (100×50)
python3 generate_hex_map.py --cols 100 --rows 50 --config map_feature_config.json --data map_data.json
```

### Step 2: Convert for Wrapper

The map generators produce files with `num_cols`/`num_rows`. The wrapper expects `map_width`/`map_height`. Use the conversion script:

```bash
python3 convert_map_for_wrapper.py --input map_data.json --output map_for_wrapper.json
```

### Step 3: Calculate Risk with Wrapper

```bash
python3 risk_model_wrapper.py \
    --data map_for_wrapper.json \
    --output risk_results.json
```

### Step 4: Generate Risk Heatmap

```bash
# Square grid heatmap (default)
python3 visualize_risk_from_json.py \
    --results risk_results.json \
    --input map_for_wrapper.json \
    --output risk_heatmap.jpg \
    --grid-type square

# OR Hexagon grid heatmap
python3 visualize_risk_from_json.py \
    --results risk_results.json \
    --input map_for_wrapper.json \
    --output risk_heatmap.jpg \
    --grid-type hex
```

## Risk Heatmap Visualizer

Generate risk heatmaps from wrapper script output. Supports both square and hexagon grids.

### Basic Usage

```bash
# Generate heatmap with default settings (square grid, no features)
python3 visualize_risk_from_json.py --results results.json
```

### Command Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--results` | `-r` | required | Path to risk results JSON file |
| `--input` | `-i` | None | Optional path to input data JSON (for feature overlay) |
| `--output` | `-o` | risk_heatmap_from_json.jpg | Output heatmap image path |
| `--grid-type` | `-g` | square | Grid type: 'square' or 'hex' |
| `--show-labels` | - | True | Show risk value labels on heatmap |
| `--no-labels` | - | - | Hide risk value labels |
| `--show-features` | - | False | Show feature overlays (road/water/mountain/hill) |
| `--no-features` | - | - | Hide feature overlays (default) |

### Examples

```bash
# Show help
python3 visualize_risk_from_json.py --help

# Basic square grid heatmap
python3 visualize_risk_from_json.py --results results.json --output heatmap.jpg

# Hexagon grid heatmap
python3 visualize_risk_from_json.py --results results.json --grid-type hex --output hex_heatmap.jpg

# With all features overlay (road/water/mountain/hill)
python3 visualize_risk_from_json.py --results results.json --input data.json --show-features

# Full options: hex grid, with features, no labels
python3 visualize_risk_from_json.py \
    --results results.json \
    --input data.json \
    --output full_heatmap.jpg \
    --grid-type hex \
    --show-features \
    --no-labels
```

### Features

- **Dual Grid Support**: Square and hexagon (even-q offset) grids
- **Multiple Feature Overlays**: Road, water, mountain, and hill overlays
- **Contrast-Optimized Labels**: Auto-selects black/white text for maximum readability
- **Dynamic Font Sizing**: Font size adjusts based on grid count
- **Large Grid Optimization**: Auto-disables labels for grids > 500 cells
- **No Borders**: Grid cells are borderless for seamless appearance

## Model Overview

### Risk Formula

```
R'_{i,t} = (ω₁·H_{i,t} + ω₂·E_i + ω₃·Σ_s w_s·D_{s,i,t}) × T_t × S_t

R_i = (R'_{i,t} - R_min) / (R_max - R_min)
```

### Components

| Component | Description |
|-----------|-------------|
| H_{i,t} | Human risk (boundary/road/water proximity) |
| E_i | Environmental risk (fire + terrain complexity) |
| D_{s,i,t} | Weighted species density |
| T_t | Diurnal factor (day/night) |
| S_t | Seasonal factor (dry/rainy) |

## IMMC Competition Enhancements

### 1. Spatio-Temporal Risk Field

Continuous risk interpolation using Gaussian or IDW kernels:

```python
from risk_model.advanced import SpatioTemporalRiskField

risk_field = SpatioTemporalRiskField(grids, risk_results)
risk = risk_field.get_risk_at(x=50, y=50, t=2, season=Season.RAINY)
```

### 2. DSSA Algorithm (Drone Swarm Scheduling)

Pseudo-code and implementation for optimal patrol scheduling. See `risk_model/advanced/dssa.py` for the complete IMMC-formatted algorithm.

### 3. Complete Workflow

```
Generate Data → Calculate Risks → Build Risk Field → Optimize Patrols → Visualize
```

## Requirements

- Python 3.8+
- numpy
- matplotlib

## Development Phases

| Phase | Status | Demo |
|-------|--------|------|
| 1. Core Model Implementation | ✅ | `demo_phase1.py` |
| 2. Risk Integration & Normalization | ✅ | `demo_phase2.py` |
| 3. Data Generation & I/O | ✅ | `demo_phase3.py` |
| 4. Visualization | ✅ | `demo_phase4.py` |
| 5. Testing & Validation | ✅ | `demo_phase5.py` |
| 6. IMMC Advanced Features | ✅ | `demo_phase6.py` |

## License

For IMMC competition use.
