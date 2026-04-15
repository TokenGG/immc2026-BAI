# Protected Area Grid Risk Index Model - Design Document

## 1. Model Objectives

In wildlife protected areas, resources such as patrol personnel, drones, fixed monitoring equipment, and rescue teams are limited. To maximize conservation effectiveness, the protected area needs to be modeled as a grid, with a **risk coefficient** calculated for each grid cell to guide optimal allocation of patrol and monitoring resources.

This model comprehensively considers:
- Human threat risk
- Environmental risk
- Animal distribution density
- Seasonal variations
- Diurnal variations

to calculate a **comprehensive risk value** for each grid cell.

Final output: risk values for each grid cell

```
R_i ∈ [0, 1]
```

Higher values indicate areas requiring more intensive monitoring.

---

## 2. Risk Calculation Formula

### 2.1 Comprehensive Risk (Non-Normalized)

```
R'_{i,t} = (ω₁·H_{i,t} + ω₂·E_i + ω₃·Σ_s w_s·D_{s,i,t}) × T_t × S_t
```

### 2.2 Normalization

```
R_i = (R'_{i,t} - R_min) / (R_max - R_min)
```

Result range:
```
R_i ∈ [0, 1]
```

Where:
- R_min = Minimum risk value across all grids
- R_max = Maximum risk value across all grids

### 2.3 Symbol Index

| Symbol | Meaning |
|--------|---------|
| i | Grid cell identifier |
| t | Time |
| s | Species |
| H_{i,t} | Human risk |
| E_i | Environmental risk |
| D_{s,i,t} | Species density |
| T_t | Diurnal influence factor |
| S_t | Seasonal influence factor |
| P_t | Poaching time probability |
| w_s | Species weight |
| ω₁, ω₂, ω₃ | Weight coefficients |

---

## 3. Human Risk Model

Human risk reflects the threat level of human activities such as poaching.

```
H_{i,t} = (α₁·d_boundary + α₂·d_road + α₃·d_water) × P_t
```

Note: Shorter distances result in higher human risk (distances should be normalized reciprocal values).

### 3.1 Parameters

| Parameter | Meaning |
|-----------|---------|
| d_boundary | Distance to protected area boundary |
| d_road | Distance to road |
| d_water | Distance to water source |
| P_t | Poaching time probability |

### 3.2 Weight Parameters

| Parameter | Meaning | Example Value |
|-----------|---------|---------------|
| α₁ | Boundary influence weight | 0.4 |
| α₂ | Road influence weight | 0.35 |
| α₃ | Water source influence weight | 0.25 |

Constraint:
```
α₁ + α₂ + α₃ = 1
```

---

## 4. Environmental Risk Model

Environmental risk reflects the impact of natural conditions on animal safety.

```
E_i = β₁·V_fire + β₂·C_terrain
```

### 4.1 Parameters

| Parameter | Meaning | Range |
|-----------|---------|-------|
| V_fire | Fire risk index | [0, 1] |
| C_terrain | Terrain complexity | [0, 1] |

### 4.2 Parameter Description

**Fire Risk (V_fire)**
- Range: 0 ≤ V_fire ≤ 1
- Sources:
  - Vegetation dryness
  - Temperature
  - Historical fire records

**Terrain Complexity (C_terrain)**
- Represents terrain influence on animal injury probability
- Examples:
  - Mountains
  - Canyons
  - Steep slopes
- Range: 0 ≤ C_terrain ≤ 1

---

## 5. Species Density Model

Animal density reflects conservation value.

```
D_{s,i,t}
```

Represents: Density of species (s) in grid (i) at time (t).

### 5.1 Weighted Species Density

```
Σ_s w_s·D_{s,i,t}
```

### 5.2 Species Weights (Example)

| Species | Weight |
|---------|--------|
| Rhino | 0.5 |
| Elephant | 0.3 |
| Bird | 0.2 |

Endangered animals have higher weights.

### 5.3 Seasonal Variation

```
D_{s,i,t} = D_{s,i} × M_season
```

**Seasonal Adjustment Coefficients (M_season)**

| Species | Rainy Season | Dry Season |
|---------|--------------|------------|
| Elephant | 1.3 | 0.9 |
| Rhino | 1.2 | 1.0 |
| Bird | 1.5 | 0.8 |

---

## 6. Seasonal Influence Model

Different seasons affect:
- Animal distribution
- Poaching activity
- Patrol difficulty

### 6.1 Seasonal Factor

```
S_t = {
    1.0   Dry Season
    1.2   Rainy Season
}
```

### 6.2 Seasonal Effects

| Season | Impact |
|--------|--------|
| Dry Season | Animals dispersed |
| Rainy Season | Animals concentrated at water sources |

Risk is typically higher during rainy season.

---

## 7. Diurnal Influence Model

Poaching activity is typically more frequent at night.

### 7.1 Diurnal Factor (Discrete)

```
T_t = {
    1.0   Daytime
    1.3   Nighttime
}
```

### 7.2 Diurnal Factor (Continuous)

```
T_t = 1 + γ·sin(2πt/24)
```

### 7.3 Risk Levels by Time

| Time | Risk |
|------|------|
| Daytime | Lower |
| Nighttime | Higher |

### 7.4 Example Time Factors

| Time | Factor |
|------|--------|
| 08:00 | 1.0 |
| 12:00 | 0.9 |
| 20:00 | 1.2 |
| 24:00 | 1.3 |

---

## 8. Model Weight Settings

Final risk weights:

```
ω₁ + ω₂ + ω₃ = 1
```

### 8.1 Example Weights

| Parameter | Meaning | Value |
|-----------|---------|-------|
| ω₁ | Human risk weight | 0.4 |
| ω₂ | Environmental risk weight | 0.3 |
| ω₃ | Animal density weight | 0.3 |

---

## 9. Input Data Structure

Model input data includes:

### 9.1 Enumeration Types

#### VegetationType Enum
```
VegetationType {
    GRASSLAND = "grassland"
    FOREST = "forest"
    SHRUB = "shrub"
}
```

#### Season Enum
```
Season {
    DRY = "dry"
    RAINY = "rainy"
}
```

### 9.2 Coordinate System

The model uses a grid-based coordinate system:

- **Origin**: Bottom-left grid cell center
- **X-axis**: Increases to the right (column index, 0-based)
- **Y-axis**: Increases upward (row index, 0-based)
- **Distance Metric**: Euclidean distance used for all distance calculations

### 9.3 Grid Data Class

#### Grid (Input - Core Model)
```
@dataclass
Grid {
    grid_id: str                    # Unique identifier (e.g., "A12")
    x: float                        # X coordinate of grid center
    y: float                        # Y coordinate of grid center
    distance_to_boundary: float          # Normalized distance to boundary [0,1]
    distance_to_road: float            # Normalized distance to road [0,1]
    distance_to_water: float           # Normalized distance to water [0,1]
}
```

#### GridInputData (Wrapper - Auto Distance Calculation)
```
@dataclass
GridInputData {
    grid_id: str                    # Unique identifier (e.g., "A12")
    x: int                          # Column index (0-based)
    y: int                          # Row index (0-based)
    fire_risk: float                 # Fire risk index [0,1]
    terrain_complexity: float          # Terrain complexity [0,1]
    vegetation_type: str             # Vegetation type
    species_densities: Dict[str, float]  # Species densities
}
```

### 9.4 Map Configuration

```
@dataclass
MapConfig {
    map_width: int                   # Number of columns
    map_height: int                  # Number of rows
    boundary_type: str               # "RECTANGLE"
    road_locations: List[Tuple[int, int]]   # Road positions as (x, y)
    water_locations: List[Tuple[int, int]]  # Water source positions as (x, y)
}
```

### 9.5 Distance Calculation

Distances are automatically calculated from grid coordinates:

**Distance to Boundary (Rectangular):**
```
dist_left = x
dist_right = (map_width - 1) - x
dist_bottom = y
dist_top = (map_height - 1) - y

min_dist_grid = min(dist_left, dist_right, dist_bottom, dist_top)
normalized_dist = min_dist_grid / max_possible_dist
distance_to_boundary = 1.0 - normalized_dist  # Closer = higher risk
```

**Distance to Feature (Road/Water):**
```
distance_to_feature = 1.0 - (min_euclidean_distance / max_possible_distance)
```

### 9.6 Species Data Classes

#### Species
```
@dataclass
Species {
    name: str                         # Species name (e.g., "rhino", "elephant", "bird")
    weight: float                     # Conservation weight (higher = more important)
    rainy_season_multiplier: float      # Density multiplier for rainy season
    dry_season_multiplier: float        # Density multiplier for dry season
}
```

#### SpeciesDensity
```
@dataclass
SpeciesDensity {
    densities: Dict[str, float]          # {species_name -> normalized_density [0,1]]
}
```

### 9.7 Environment Data Class

#### Environment
```
@dataclass
Environment {
    fire_risk: float                 # Fire risk index [0,1]
    terrain_complexity: float          # Terrain complexity [0,1]
    vegetation_type: VegetationType     # Type of vegetation
}
```

### 9.8 Time Context Class

#### TimeContext
```
@dataclass
TimeContext {
    hour_of_day: int                 # Hour of the day [0, 23]
    season: Season                  # Current season (DRY or RAINY)

    # Derived properties:
    is_daytime: bool                 # True if 6:00-18:00
    is_nighttime: bool               # True if 18:00-6:00
}
```

### 9.9 Summary of Input Fields

#### Grid Spatial Data (Core Model)

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| grid_id | string | - | Unique identifier (e.g., "A12" |
| x | float | ≥ 0 | X coordinate of grid center |
| y | float | ≥ 0 | Y coordinate of grid center |
| distance_to_boundary | float | [0,1] | Normalized distance to protected area boundary (0=at boundary, 1=farthest) |
| distance_to_road | float | [0,1] | Normalized distance to nearest road (0=at road, 1=farthest) |
| distance_to_water | float | [0,1] | Normalized distance to nearest water source |

#### Grid Spatial Data (Wrapper with Auto Distance)

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| grid_id | string | - | Unique identifier (e.g., "A12") |
| x | int | ≥ 0 | Column index (0-based, from left) |
| y | int | ≥ 0 | Row index (0-based, from bottom) |

#### Map Configuration

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| map_width | int | ≥ 1 | Number of columns in grid |
| map_height | int | ≥ 1 | Number of rows in grid |
| boundary_type | string | - | Boundary type ("RECTANGLE") |
| road_locations | List[[x,y]] | - | Road positions as grid coordinates |
| water_locations | List[[x,y]] | - | Water source positions as grid coordinates |

#### Environmental Data

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| fire_risk | float | [0,1] | Fire risk index (0=safe, 1=dangerous) |
| terrain_complexity | float | [0,1] | Terrain complexity (0=flat, 1=complex) |
| vegetation_type | enum | - | Vegetation type (GRASSLAND, FOREST, SHRUB) |

#### Animal Data

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| species_name | string | - | Name of species |
| density | float | [0,1] | Normalized density of species in grid |
| weight | float | >0 | Conservation weight of species |
| rainy_season_multiplier | float | ≥0 | Density multiplier for rainy season |
| dry_season_multiplier | float | ≥0 | Density multiplier for dry season |

#### Time Data

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| hour_of_day | integer | [0,23] | Hour of the day |
| season | enum | - | Season (DRY, RAINY) |

---

## 10. Model Output

### 10.1 Output Data Classes

#### RiskComponents (Intermediate Output)
```
@dataclass
RiskComponents {
    human_risk: float             # Human risk component [0, ~1]
    environmental_risk: float        # Environmental risk component [0, ~1]
    density_value: float          # Weighted species density value [0, ~1]
    diurnal_factor: float         # Diurnal multiplier (typically 1.0-1.3)
    seasonal_factor: float        # Seasonal multiplier (typically 1.0-1.2)

    # Derived property:
    temporal_factor: float        # diurnal_factor × seasonal_factor
}
```

#### GridRiskResult (Final Output for Single Grid)
```
@dataclass
GridRiskResult {
    grid_id: str                  # Grid identifier (e.g., "A12")
    raw_risk: float               # Non-normalized risk value
    normalized_risk: Optional[float]   # Normalized risk [0,1]
    components: Optional[RiskComponents]  # Individual risk components
}
```

### 10.2 Normalization Output

#### NormalizationEngine State
```
NormalizationEngine {
    min_risk: Optional[float]     # Minimum raw risk in batch
    max_risk: Optional[float]     # Maximum raw risk in batch
    is_fitted: bool               # True after fit() is called
}
```

#### Normalization Formula
```
R_i = (R'_i - R_min) / (R_max - R_min)
```

Where:
- R'_i = Raw risk value for grid i
- R_min = Minimum raw risk across all grids in batch
- R_max = Maximum raw risk across all grids in batch
- R_i = Normalized risk value [0, 1]

### 10.3 Batch Output Structure

#### Batch Calculation Result
```
List[GridRiskResult] [
    GridRiskResult {
        grid_id: "A00",
        raw_risk: 1.423,
        normalized_risk: 1.000,
        components: RiskComponents {
            human_risk: 0.937,
            environmental_risk: 0.760,
            density_value: 1.032,
            diurnal_factor: 1.3,
            seasonal_factor: 1.2
        }
    },
    GridRiskResult {
        grid_id: "A01",
        ...
    },
    ...
]
```

### 10.4 Output Fields Summary

#### GridRiskResult Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| grid_id | string | - | Unique grid identifier |
| raw_risk | float | ≥0 | Non-normalized composite risk value |
| normalized_risk | float | [0,1] | Normalized risk for comparison (null if not normalized) |

#### RiskComponents Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| human_risk | float | [0, ~1] | Human threat risk |
| environmental_risk | float | [0, ~1] | Environmental risk |
| density_value | float | [0, ~1] | Weighted species density (conservation value) |
| diurnal_factor | float | ≥0 | Time of day multiplier |
| seasonal_factor | float | ≥0 | Season multiplier |
| temporal_factor | float | ≥0 | Combined time multiplier (derived) |

### 10.5 Example Output

#### Single Grid Example
```
GridRiskResult {
    grid_id: "A12",
    raw_risk: 1.380,
    normalized_risk: 0.82,
    components: RiskComponents {
        human_risk: 0.92,
        environmental_risk: 0.76,
        density_value: 0.96,
        diurnal_factor: 1.3,
        seasonal_factor: 1.2
    }
}
```

#### Tabular Output Example

| Grid | Raw Risk | Normalized Risk | Human | Env | Density | Temporal |
|------|----------|----------------|-------|-----|---------|----------|
| A12 | 1.380 | 0.82 | 0.92 | 0.76 | 0.96 | 1.56 |
| B07 | 1.051 | 0.65 | 0.77 | 0.46 | 0.76 | 1.56 |
| C14 | 0.534 | 0.33 | 0.38 | 0.28 | 0.41 | 1.56 |

---

## 11. Model Applications

The calculated risk map can be used for:

### 11.1 Patrol Route Optimization
Prioritize patrols in high-risk areas.

### 11.2 Drone Monitoring
Drone priority coverage:
- Nighttime
- High-risk areas

### 11.3 Station Site Selection
Select locations with:
- High-risk centers
- Maximum coverage area

### 11.4 Emergency Rescue
Deploy rescue personnel in areas with high animal injury probability.

---

## 12. Model Advantages

Compared to traditional static models, this model offers:

### 12.1 Dynamic Risk Assessment
Considers both:
- Spatial factors
- Temporal factors

### 12.2 Ecological Consistency
Animal behavior changes with seasons.

### 12.3 Scheduling Algorithm Ready
Can directly serve as **input variables for DSSA scheduling algorithms**.
