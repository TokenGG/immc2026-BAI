# Wildlife Reserve Protection Optimization (DSSA)

A Python implementation of the Dynamic Sparrow Search Algorithm (DSSA) for optimizing wildlife protection resource allocation in a reserve using hexagonal honeycomb grids.

## Features

- **Hexagonal Grid System**: Uses axial coordinate system for accurate distance calculations
- **Terrain-Based Deployment Constraints**: Resources can only be deployed in suitable terrain types
- **Multi-Resource Optimization**: Optimizes placement of patrols, cameras, drones, and fences
- **DSSA Algorithm**: Efficient metaheuristic optimization with producers, followers, and scouts
- **Comprehensive Visualization**: Risk heatmaps, deployment maps, convergence curves, and terrain maps
- **Time-Dynamic Analysis**: Analyzes protection effectiveness over time with varying patrol schedules
- **Demo Runner**: Easy-to-use demo script with configurable scenarios

## Project Structure

```
hexdynamic/
├── data_loader.py              # Data loading and configuration management
├── grid_model.py               # Hexagonal grid model and distance calculations
├── coverage_model.py           # Protection coverage and benefit calculations
├── dynamic_coverage_model.py   # Time-dynamic protection analysis
├── dssa_optimizer.py           # Dynamic Sparrow Search Algorithm implementation
├── visualization.py            # Plotting and visualization functions
├── main.py                     # Main program entry point
├── demo.py                     # Demo runner with full scenario
├── config.json                 # Main program configuration
├── demo_config.json            # Demo configuration
├── risk_calculator.py          # Risk calculation utilities
├── example_usage.py            # Usage examples
├── demo_complete.py            # Complete demo script
├── demo_20x20_multi_resource.py # 20x20 multi-resource demo
├── demo_dynamic_protection.py  # Dynamic protection demo
├── test_rectangular_grid.py    # Rectangular grid test
├── test_tight_grid.py          # Tight grid test
├── test_simple_tightness.py    # Tightness test
├── requirements.txt            # Python dependencies
├── IMPLEMENTATION.md           # Implementation details
└── README.md                   # This file
```

## Installation

### Requirements

- Python 3.7+
- numpy
- matplotlib
- pandas (optional)

### Install Dependencies

```bash
pip install numpy matplotlib pandas
```

## Usage

### Quick Start with Demo

Run the complete demo with default configuration:

```bash
python demo.py
```

Or specify a custom configuration file:

```bash
python demo.py demo_config.json
python demo.py --config=my_config.json
python demo.py --output-dir=./my_output
```

The demo will:
1. Generate a rectangular hexagonal grid with configurable size
2. Set up risk distribution with high-risk grids
3. Run DSSA optimization for resource allocation
4. Calculate Key Performance Indicators (KPIs)
5. Generate all visualizations in a timestamped output directory
6. Save results to JSON and summary report

### Using Main Program

Run the basic scenario:

```bash
python main.py
```

This will:
1. Generate a hexagonal grid with random terrain and risk values
2. Run DSSA optimization for 100 iterations
3. Generate all visualizations in the `output/` directory
4. Save results to `output/results.json`

### Demo Configuration

Edit `demo_config.json` to customize the demo scenario:

```json
{
  "grid_size": {
    "width": 30,
    "height": 30
  },
  "risk_configuration": {
    "high_risk_grid_count": 20,
    "high_risk_value": 0.9,
    "normal_risk_range": [0.1, 0.5]
  },
  "resource_inventory": {
    "patrol_personnel": 10,
    "uavs": 3,
    "surveillance_cameras": 5,
    "base_camps": 2,
    "camp_capacity": 3
  },
  "time_dynamic_config": {
    "time_steps": 24,
    "analysis_enabled": true,
    "target_protection": 0.7
  }
}
```

### Main Program Configuration

Edit `config.json` to customize the main program:

```json
{
  "grid_radius": 5,
  "constraints": {
    "total_patrol": 20,
    "total_camps": 5,
    "max_rangers_per_camp": 5,
    "total_cameras": 10,
    "total_drones": 3,
    "total_fence_length": 50.0
  },
  "coverage_params": {
    "patrol_radius": 5.0,
    "drone_radius": 8.0,
    "camera_radius": 3.0,
    "fence_protection": 0.5,
    "wp": 0.3,
    "wd": 0.3,
    "wc": 0.2,
    "wf": 0.2
  }
}
```

### Programmatic Usage

```python
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig

# Initialize optimizer
optimizer = WildlifeProtectionOptimizer()

# Setup scenario
optimizer.setup_default_scenario()

# Configure DSSA
dssa_config = DSSAConfig(
    population_size=50,
    max_iterations=100,
    producer_ratio=0.2,
    scout_ratio=0.2
)

# Run optimization
solution, fitness, history = optimizer.run_optimization(dssa_config)

# Print results
optimizer.print_solution_summary()

# Generate visualizations
optimizer.generate_all_visualizations(output_dir='./output')

# Save results
optimizer.save_results(output_path='./output/results.json')
```

## Model Components

### 1. Hexagonal Grid System

- Uses axial coordinates (q, r) for grid representation
- Calculates distances using hexagonal distance formula
- Supports terrain classification (5 types)

### 2. Terrain Types

| Terrain | Patrol | Camp | Drone | Camera | Fence |
|---------|--------|------|-------|--------|-------|
| Salt Marsh | 0 | 0 | 1 | 0 | 0 |
| Sparse Grass | 1 | 1 | 1 | 1 | 1 |
| Dense Grass | 1 | 1 | 1 | 0 | 1 |
| Water Hole | 0 | 0 | 1 | 0 | 0 |
| Road | 1 | 1 | 1 | 1 | 1 |

### 3. Coverage Models

- **Patrol Coverage**: Exponential decay with distance
- **Drone Coverage**: Terrain-dependent visibility
- **Camera Coverage**: Terrain-dependent visibility
- **Fence Protection**: Reduces intrusion probability

### 4. DSSA Algorithm

- **Producers**: Explore new solutions around best solution
- **Followers**: Move toward best solution or producers
- **Scouts**: Random exploration to avoid local optima
- **Feasibility Repair**: Ensures all solutions respect constraints

## Output Files

After running the main program, the following files are generated in `output/`:

1. **risk_heatmap.png**: Visualizes poaching risk across the reserve
2. **deployment_map.png**: Shows optimal resource placement
3. **convergence_curve.png**: DSSA fitness over iterations
4. **terrain_map.png**: Terrain distribution across the reserve
5. **results.json**: Detailed optimization results in JSON format

### Demo Output Files

When running `demo.py`, the following additional files are generated:

1. **1_risk_heatmap.png**: Grid risk value heatmap
2. **2_resource_distribution.png**: Resource distribution map
3. **3_protection_heatmap.png**: Protection level heatmap
4. **4_convergence_curve.png**: DSSA convergence curve
5. **5_terrain_map.png**: Terrain distribution map
6. **6_time_dynamic_analysis.png**: Time-dynamic protection analysis (if enabled)
7. **demo_results.json**: Complete results data
8. **summary_report.txt**: Human-readable summary report
9. **config.txt**: Configuration in key:value format
10. **execution_summary.txt**: Execution time and summary

## Key Performance Indicators (KPIs)

The demo outputs three important metrics for evaluating protection effectiveness:

### 1. Best Fitness (最佳适应度)

**Definition**: The fitness value of the optimal solution found by the DSSA optimization algorithm.

**Calculation**:
```
Best Fitness = (Σ [R_i × (1 - e^(-E_i))]) / (Σ R_i)
```

Where:
- `R_i` = Risk value of grid i
- `E_i` = Combined protection effect at grid i (from patrols, drones, cameras, and fences)
- Numerator = Sum of protection benefits across all grids
- Denominator = Sum of all risk values

**Interpretation**:
- Range: [0, 1]
- Higher is better
- Value of 1 indicates perfect protection for all high-risk areas
- This is the objective function maximized by the optimization algorithm

### 2. Total Protection Benefit (总保护效益)

**Definition**: The sum of protection benefits across all grids, without normalization.

**Calculation**:
```
B_i = R_i × (1 - e^(-E_i))
Total Protection Benefit = Σ B_i
```

Where:
- `B_i` = Protection benefit for grid i
- `(1 - e^(-E_i))` = Saturation function with diminishing returns
- `R_i` = Risk value (higher risk grids contribute more when protected)

**Interpretation**:
- Range: [0, Σ R_i]
- Higher is better
- Measures absolute total protection provided
- Useful for comparing different scenarios with the same risk distribution

### 3. Average Protection Benefit (平均保护效益)

**Definition**: The average protection benefit per grid.

**Calculation**:
```
Average Protection Benefit = (Σ B_i) / N
```

Where:
- `Σ B_i` = Total Protection Benefit
- `N` = Total number of grids

**Interpretation**:
- Range: [0, max(R_i)]
- Higher is better
- Measures average protection level across the entire reserve
- Useful for comparing scenarios with different grid sizes

### Summary Table

| Metric | Calculation | Normalized | Purpose |
|--------|-------------|-----------|---------|
| **Best Fitness** | Σ(R_i·(1-e^(-E_i))) / ΣR_i | Yes (by total risk) | Optimization objective, compares solution quality |
| **Total Protection Benefit** | Σ(R_i·(1-e^(-E_i))) | No | Absolute total protection value |
| **Average Protection Benefit** | Σ(R_i·(1-e^(-E_i))) / N | No (by grid count) | Average protection per grid |

## Mathematical Model

### Objective Function

Maximize total protection benefit:

```
F = Σ R_i × (1 - exp(-E_i))
```

Where:
- R_i = Risk at grid i
- E_i = Combined protection effect at grid i

### Protection Effect

```
E_i = w_p × Patrol_i + w_d × Drone_i + w_c × Camera_i + w_f × Fence_i
```

### Constraints

- Resource quantity limits
- Terrain-based deployment feasibility
- Maximum rangers per camp

## Parameters

### DSSA Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| population_size | 50 | Number of sparrows in population |
| max_iterations | 100 | Maximum optimization iterations |
| producer_ratio | 0.2 | Proportion of producers |
| scout_ratio | 0.2 | Proportion of scouts |
| ST | 0.8 | Safety threshold |
| R2 | 0.5 | Warning value |

### Coverage Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| patrol_radius | 5.0 | Patrol effective radius |
| drone_radius | 8.0 | Drone effective radius |
| camera_radius | 3.0 | Camera effective radius |
| fence_protection | 0.5 | Fence protection coefficient |
| wp | 0.3 | Patrol weight |
| wd | 0.3 | Drone weight |
| wc | 0.2 | Camera weight |
| wf | 0.2 | Fence weight |

## Performance

- **Grid Size**: 91 hexagonal cells (radius=5)
- **Optimization Time**: ~30-60 seconds (100 iterations)
- **Memory Usage**: ~50-100 MB

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational and research purposes.

## References

- Sparrow Search Algorithm (SSA) for optimization
- Hexagonal grid systems for spatial modeling
- Wildlife protection resource allocation models
