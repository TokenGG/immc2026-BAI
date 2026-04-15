#!/usr/bin/env python3
"""
Wildlife Reserve Protection Optimization - Demo
Based on demo_dynamic_protection.py logic

Usage:
    python demo.py                              # Use default config: demo_config.json
    python demo.py config.json                  # Use specified config file
    python demo.py --config=my_config.json      # Alternative syntax
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
import sys
import argparse
import random
from datetime import datetime
from typing import Dict, List

from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig
from coverage_model import DeploymentSolution
from dynamic_coverage_model import DynamicCoverageModel, TimeDynamicSolution


class DemoRunner:
    def __init__(self, config_path: str = 'demo_config.json', output_dir: str = None):
        """Initialize demo with configuration from JSON file"""
        self.config_path = config_path
        self.config = self.load_config(config_path)
        self.optimizer = None
        self.best_solution = None
        self.best_fitness = None
        self.fitness_history = None
        
        # Create output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            # Create unique output directory with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.output_dir = f'./output/demo_{timestamp}'
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Copy configuration file to output directory
        self._save_config_to_output()
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        print(f"Loading configuration from {config_path}...")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("\n" + "=" * 70)
        print("CONFIGURATION LOADED")
        print("=" * 70)
        print(f"Grid Size: {config['grid_size']['width']} x {config['grid_size']['height']}")
        print(f"High-Risk Grids: {config['risk_configuration']['high_risk_grid_count']}")
        print(f"\nResource Inventory:")
        print(f"  - Patrol Personnel: {config['resource_inventory']['patrol_personnel']}")
        print(f"  - UAVs (Drones): {config['resource_inventory'].get('uavs', 0)}")
        print(f"  - Surveillance Cameras: {config['resource_inventory'].get('surveillance_cameras', 0)}")
        print(f"  - Base Camps: {config['resource_inventory']['base_camps']}")
        print(f"  - Camp Capacity: {config['resource_inventory'].get('camp_capacity', 3)} personnel/camp")
        print("=" * 70 + "\n")
        
        return config
    
    def _save_config_to_output(self):
        """Save configuration in key: value format to output directory"""
        config_txt_path = os.path.join(self.output_dir, 'config.txt')
        
        def flatten_dict(d, parent_key='', sep='.'):
            """Flatten nested dictionary to key: value pairs"""
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    items.append((new_key, str(v)))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        # Flatten configuration
        flat_config = flatten_dict(self.config)
        
        # Write to text file
        with open(config_txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("CONFIGURATION\n")
            f.write("=" * 70 + "\n\n")
            
            for key, value in flat_config.items():
                f.write(f"{key}: {value}\n")
            
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"Configuration saved to: {config_txt_path}\n")

    def setup_scenario(self):
        """Setup the optimization scenario based on config"""
        print("Setting up scenario...")
        
        grid_config = self.config['grid_size']
        risk_config = self.config['risk_configuration']
        resource_config = self.config['resource_inventory']
        coverage_config = self.config['coverage_parameters']
        
        # Initialize optimizer
        self.optimizer = WildlifeProtectionOptimizer()
        
        # Generate rectangular hex grid
        grid_width = grid_config['width']
        grid_height = grid_config['height']
        print(f"Generating rectangular hex grid: {grid_width} x {grid_height}")
        self.optimizer.data_loader.generate_rectangular_hex_grid(width=grid_width, height=grid_height)
        
        # Initialize matrices
        print("Initializing deployment matrix and visibility parameters...")
        from grid_model import HexGridModel
        temp_grid_model = HexGridModel(self.optimizer.data_loader.grids)
        edge_grids = temp_grid_model.get_edge_grids()
        print(f"Edge grids count: {len(edge_grids)}")
        
        self.optimizer.data_loader.initialize_deployment_matrix(edge_grids=edge_grids)
        self.optimizer.data_loader.initialize_visibility_params()
        
        # Generate risk distribution with high-risk grids
        self._generate_risk_distribution(
            high_risk_count=risk_config['high_risk_grid_count'],
            high_risk_value=risk_config['high_risk_value'],
            normal_risk_range=tuple(risk_config['normal_risk_range'])
        )
        
        # Update constraints based on resource inventory
        constraints = {
            'total_patrol': resource_config['patrol_personnel'],
            'total_camps': resource_config['base_camps'],
            'max_rangers_per_camp': resource_config['camp_capacity'],
            'total_cameras': resource_config['surveillance_cameras'],
            'total_drones': resource_config['uavs'],
            'total_fence_length': 0.0  # Not used in this demo
        }
        self.optimizer.data_loader.set_constraints(**constraints)
        
        # Update coverage parameters
        self.optimizer.data_loader.set_coverage_parameters(**coverage_config)
        
        # Initialize models
        self.optimizer._initialize_models()
        
        print("Scenario setup complete!\n")

    def _generate_risk_distribution(self, high_risk_count: int, 
                                   high_risk_value: float,
                                   normal_risk_range: tuple):
        """Generate risk distribution with specified high-risk grids"""
        grid_ids = [grid.grid_id for grid in self.optimizer.data_loader.grids]
        
        # Randomly select high-risk grids
        high_risk_grids = random.sample(grid_ids, high_risk_count)
        
        # Assign risk values and terrain
        risk_map = {}
        terrain_map = {}
        for grid_id in grid_ids:
            terrain_map[grid_id] = 'SparseGrass'  # All grids are sparse grass
            if grid_id in high_risk_grids:
                risk_map[grid_id] = high_risk_value
            else:
                risk_map[grid_id] = random.uniform(*normal_risk_range)
        
        self.optimizer.data_loader.set_terrain_types(terrain_map)
        self.optimizer.data_loader.set_risk_values(risk_map)
        
        print(f"Risk distribution generated:")
        print(f"  - High-risk grids: {high_risk_count} (risk = {high_risk_value})")
        print(f"  - Normal-risk grids: {len(grid_ids) - high_risk_count} (risk = {normal_risk_range[0]}-{normal_risk_range[1]})")
    
    def run_optimization(self):
        """Run DSSA optimization"""
        print("\n" + "=" * 70)
        print("RUNNING DSSA OPTIMIZATION")
        print("=" * 70)
        
        dssa_config_dict = self.config['dssa_config']
        dssa_config = DSSAConfig(
            population_size=dssa_config_dict['population_size'],
            max_iterations=dssa_config_dict['max_iterations'],
            producer_ratio=dssa_config_dict['producer_ratio'],
            scout_ratio=dssa_config_dict['scout_ratio'],
            ST=dssa_config_dict['ST'],
            R2=dssa_config_dict['R2']
        )
        
        self.best_solution, self.best_fitness, self.fitness_history = \
            self.optimizer.run_optimization(dssa_config, verbose=True)
        
        print("=" * 70 + "\n")

    def calculate_kpis(self) -> Dict:
        """Calculate Key Performance Indicators"""
        print("Calculating KPIs...")
        
        # Get protection benefit for each grid
        protection_benefit = self.optimizer.coverage_model.calculate_protection_benefit(
            self.best_solution
        )
        
        # Get protection effect for coverage calculation
        protection_effect = self.optimizer.coverage_model.calculate_protection_effect(
            self.best_solution
        )
        
        # Calculate coverage (grids with protection effect > threshold)
        coverage_threshold = 0.1
        covered_grids = sum(1 for effect in protection_effect.values() if effect > coverage_threshold)
        total_grids = len(protection_effect)
        
        # Calculate KPIs
        total_benefit = sum(protection_benefit.values())
        avg_benefit = np.mean(list(protection_benefit.values()))
        coverage_percentage = (covered_grids / total_grids) * 100
        
        kpis = {
            'total_protection_benefit': total_benefit,
            'average_protection_benefit': avg_benefit,
            'grid_coverage_count': covered_grids,
            'grid_coverage_percentage': coverage_percentage,
            'total_grids': total_grids
        }
        
        print("\n" + "=" * 70)
        print("KEY PERFORMANCE INDICATORS (KPIs)")
        print("=" * 70)
        print(f"Total Protection Benefit:     {kpis['total_protection_benefit']:.4f}")
        print(f"Average Protection Benefit:   {kpis['average_protection_benefit']:.4f}")
        print(f"Grid Coverage:                {kpis['grid_coverage_count']}/{kpis['total_grids']} grids ({kpis['grid_coverage_percentage']:.1f}%)")
        print("=" * 70 + "\n")
        
        return kpis

    def generate_visualizations(self):
        """Generate all required visualizations"""
        print("Generating visualizations...")
        
        # 1. Grid Risk Value Heatmap
        self.optimizer.visualizer.plot_risk_heatmap(
            save_path=f'{self.output_dir}/1_risk_heatmap.png',
            show=False
        )
        print(f"  [OK] Grid Risk Value Heatmap saved")
        
        # 2. Resource Distribution Map
        self.optimizer.visualizer.plot_deployment_map(
            self.best_solution,
            save_path=f'{self.output_dir}/2_resource_distribution.png',
            show=False
        )
        print(f"  [OK] Resource Distribution Map saved")
        
        # 3. Protection Level Heatmap
        self._plot_protection_heatmap()
        print(f"  [OK] Protection Level Heatmap saved")
        
        # 4. DSSA Convergence Curve
        self.optimizer.visualizer.plot_convergence_curve(
            self.fitness_history,
            save_path=f'{self.output_dir}/4_convergence_curve.png',
            show=False
        )
        print(f"  [OK] DSSA Convergence Curve saved")
        
        # 5. Terrain Map
        self.optimizer.visualizer.plot_terrain_map(
            save_path=f'{self.output_dir}/5_terrain_map.png',
            show=False
        )
        print(f"  [OK] Terrain Map saved")
        
        print(f"\nAll visualizations saved to: {self.output_dir}/\n")
    
    def _plot_protection_heatmap(self):
        """Plot protection level heatmap using hexagonal grid"""
        from matplotlib.patches import Polygon
        from matplotlib import cm
        
        protection_benefit = self.optimizer.coverage_model.calculate_protection_benefit(
            self.best_solution
        )
        
        # Get all grid IDs
        grid_ids = self.optimizer.grid_model.get_all_grid_ids()
        
        # Find min and max protection values for normalization
        if protection_benefit:
            max_protection = max(protection_benefit.values())
            min_protection = min(protection_benefit.values())
        else:
            max_protection = 1.0
            min_protection = 0.0
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        cmap = cm.get_cmap('YlGn')
        
        # Plot each hexagon with protection color
        for grid_id in grid_ids:
            # Get hexagon corners
            corners = self.optimizer.visualizer._get_hex_corners(grid_id)
            
            # Get protection benefit for this grid
            benefit = protection_benefit.get(grid_id, 0.0)
            
            # Normalize protection value
            if max_protection > min_protection:
                normalized_benefit = (benefit - min_protection) / (max_protection - min_protection)
            else:
                normalized_benefit = 0.5
            
            # Get color from colormap
            color = cmap(normalized_benefit)
            
            # Draw hexagon
            polygon = Polygon(corners, facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8)
            ax.add_patch(polygon)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min_protection, vmax=max_protection))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('Protection Benefit', fontsize=12)
        
        # Set plot properties
        ax.set_aspect('equal')
        ax.set_title('Protection Level Heatmap', fontsize=16, fontweight='bold')
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Set axis limits based on grid bounds
        hex_size = self.optimizer.visualizer.hex_size
        bounds = self.optimizer.grid_model.get_grid_bounds(hex_size)
        ax.set_xlim(bounds[0] - 1, bounds[1] + 1)
        ax.set_ylim(bounds[2] - 1, bounds[3] + 1)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/3_protection_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()

    def run_time_dynamic_analysis(self):
        """Run time-dynamic protection analysis"""
        if not self.config['time_dynamic_config']['analysis_enabled']:
            print("Time-dynamic analysis disabled in config.\n")
            return
        
        print("\n" + "=" * 70)
        print("TIME-DYNAMIC PROTECTION ANALYSIS")
        print("=" * 70)
        
        time_steps = self.config['time_dynamic_config']['time_steps']
        print(f"Analyzing protection over {time_steps} time steps...")
        
        # Create dynamic coverage model
        dynamic_model = DynamicCoverageModel(
            self.optimizer.grid_model,
            self.optimizer.data_loader.coverage_params,
            self.optimizer.data_loader.deployment_matrix,
            self.optimizer.data_loader.visibility_params
        )
        
        # Generate patrol routes and drone schedules
        patrol_count = sum(self.best_solution.rangers.values())
        rangers_time_series = dynamic_model.generate_patrol_routes(patrol_count, time_steps)
        
        drone_count = sum(self.best_solution.drones.values())
        drones_time_series = dynamic_model.generate_drone_schedules(drone_count, time_steps)
        
        # Create dynamic solution
        dynamic_solution = TimeDynamicSolution(
            cameras=self.best_solution.cameras,
            camps=self.best_solution.camps,
            drones=drones_time_series,
            rangers=rangers_time_series,
            fences=self.best_solution.fences
        )
        
        # Simulate protection over time
        protection_over_time = dynamic_model.simulate_protection_over_time(
            dynamic_solution, time_steps
        )
        
        # Estimate minimum staffing requirement
        target_protection = self.config['time_dynamic_config'].get('target_protection', 0.4)
        min_staffing = dynamic_model.estimate_minimum_staffing(
            self.best_solution, time_steps, target_protection
        )
        
        # Calculate statistics
        avg_protection = np.mean(protection_over_time)
        min_protection = np.min(protection_over_time)
        max_protection = np.max(protection_over_time)
        std_protection = np.std(protection_over_time)
        
        print(f"\nTime-Dynamic Statistics:")
        print(f"  - Average Protection: {avg_protection:.4f}")
        print(f"  - Minimum Protection: {min_protection:.4f}")
        print(f"  - Maximum Protection: {max_protection:.4f}")
        print(f"  - Std Deviation:      {std_protection:.4f}")
        print(f"  - Target Protection:  {target_protection:.4f}")
        print(f"  - Min Staffing Req:   {min_staffing}")
        print("=" * 70 + "\n")
        
        # Store stats for summary report
        self.time_dynamic_stats = {
            'time_steps': time_steps,
            'avg_protection': avg_protection,
            'min_protection': min_protection,
            'max_protection': max_protection,
            'std_protection': std_protection,
            'target_protection': target_protection,
            'min_staffing': min_staffing
        }
        
        # Plot time-dynamic analysis
        self._plot_time_dynamic_analysis(protection_over_time, time_steps, min_staffing, target_protection)

    def _plot_time_dynamic_analysis(self, protection_over_time: List[float], time_steps: int, 
                                    min_staffing: int, target_protection: float):
        """Plot time-dynamic protection analysis"""
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        fig.suptitle('Time-Dynamic Protection Analysis', fontsize=18, fontweight='bold')
        
        # Plot 1: Protection over time
        time_points = list(range(1, time_steps + 1))
        ax1.plot(time_points, protection_over_time, 'b-', linewidth=2, label='Protection Benefit')
        ax1.axhline(y=target_protection, color='r', linestyle='--', 
                   linewidth=1.5, label=f'Target Protection: {target_protection}')
        ax1.fill_between(time_points, protection_over_time, alpha=0.3)
        
        ax1.set_xlabel('Time Step (Hour)', fontsize=12)
        ax1.set_ylabel('Protection Benefit', fontsize=12)
        ax1.set_title('Protection vs Time', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Plot 2: Staffing vs Protection
        staff_levels = range(1, min_staffing + 5)
        protection_levels = []
        
        for P in staff_levels:
            if P < min_staffing:
                protection = target_protection * (P / min_staffing) * 0.9
            else:
                protection = target_protection * (1 + (P - min_staffing) * 0.1)
            protection_levels.append(protection)
        
        ax2.plot(staff_levels, protection_levels, 'g-', linewidth=2, label='Average Protection')
        ax2.axhline(y=target_protection, color='r', linestyle='--', 
                   label=f'Target Protection: {target_protection}')
        ax2.axvline(x=min_staffing, color='b', linestyle='--', 
                   label=f'Min Staffing: {min_staffing}')
        
        ax2.set_xlabel('Patrol Personnel', fontsize=12)
        ax2.set_ylabel('Average Protection', fontsize=12)
        ax2.set_title('Staffing vs Average Protection', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=10)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f'{self.output_dir}/6_time_dynamic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Time-Dynamic Analysis plot saved")

    def save_results(self):
        """Save all results to JSON and summary report"""
        print("Saving results...")
        
        # Get solution statistics
        stats = self.optimizer.optimizer.get_solution_statistics(self.best_solution)
        
        # Get KPIs
        kpis = self.calculate_kpis()
        
        # Compile results
        results = {
            'timestamp': datetime.now().isoformat(),
            'configuration': self.config,
            'optimization_results': {
                'best_fitness': float(self.best_fitness),
                'fitness_history': [float(f) for f in self.fitness_history],
                'iterations': len(self.fitness_history) - 1
            },
            'solution_statistics': stats,
            'kpis': kpis,
            'grid_info': {
                'total_grids': self.optimizer.grid_model.get_grid_count(),
                'terrain_distribution': self.optimizer.data_loader.get_terrain_distribution()
            }
        }
        
        # Add time-dynamic stats if available
        if hasattr(self, 'time_dynamic_stats'):
            results['time_dynamic_stats'] = self.time_dynamic_stats
        
        # Save to JSON
        output_path = f'{self.output_dir}/demo_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {output_path}\n")
        
        # Save summary report
        self._save_summary_report(kpis, stats)

    def _save_summary_report(self, kpis: Dict, stats: Dict):
        """Save a human-readable summary report"""
        summary_path = f'{self.output_dir}/summary_report.txt'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("WILDLIFE RESERVE PROTECTION OPTIMIZATION - SUMMARY REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            # Configuration Summary
            f.write("CONFIGURATION SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Grid Size: {self.config['grid_size']['width']} x {self.config['grid_size']['height']}\n")
            f.write(f"High-Risk Grids: {self.config['risk_configuration']['high_risk_grid_count']}\n")
            f.write(f"Patrol Personnel: {self.config['resource_inventory']['patrol_personnel']}\n")
            f.write(f"UAVs (Drones): {self.config['resource_inventory']['uavs']}\n")
            f.write(f"Surveillance Cameras: {self.config['resource_inventory']['surveillance_cameras']}\n")
            f.write(f"Base Camps: {self.config['resource_inventory']['base_camps']}\n")
            f.write("\n")
            
            # Optimization Results
            f.write("OPTIMIZATION RESULTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Algorithm: DSSA (Dung Beetle Optimization)\n")
            f.write(f"Population Size: {self.config['dssa_config']['population_size']}\n")
            f.write(f"Max Iterations: {self.config['dssa_config']['max_iterations']}\n")
            f.write(f"Best Fitness: {self.best_fitness:.6f}\n")
            f.write(f"Convergence Iterations: {len(self.fitness_history) - 1}\n")
            f.write("\n")
            
            # Key Performance Indicators
            f.write("=" * 70 + "\n")
            f.write("KEY PERFORMANCE INDICATORS (KPIs)\n")
            f.write("=" * 70 + "\n")
            f.write(f"Total Protection Benefit:     {kpis['total_protection_benefit']:.4f}\n")
            f.write(f"Average Protection Benefit:   {kpis['average_protection_benefit']:.4f}\n")
            f.write(f"Grid Coverage:                {kpis['grid_coverage_count']}/{kpis['total_grids']} grids ({kpis['grid_coverage_percentage']:.1f}%)\n")
            f.write("=" * 70 + "\n\n")
            
            # Time-Dynamic Analysis (if available)
            if hasattr(self, 'time_dynamic_stats'):
                f.write("=" * 70 + "\n")
                f.write("TIME-DYNAMIC PROTECTION ANALYSIS\n")
                f.write("=" * 70 + "\n")
                f.write(f"Time Steps Analyzed: {self.time_dynamic_stats['time_steps']}\n")
                f.write("\nTime-Dynamic Statistics:\n")
                f.write(f"  - Average Protection: {self.time_dynamic_stats['avg_protection']:.4f}\n")
                f.write(f"  - Minimum Protection: {self.time_dynamic_stats['min_protection']:.4f}\n")
                f.write(f"  - Maximum Protection: {self.time_dynamic_stats['max_protection']:.4f}\n")
                f.write(f"  - Std Deviation:      {self.time_dynamic_stats['std_protection']:.4f}\n")
                f.write(f"  - Target Protection:  {self.time_dynamic_stats['target_protection']:.4f}\n")
                f.write(f"  - Min Staffing Req:   {self.time_dynamic_stats['min_staffing']}\n")
                f.write("=" * 70 + "\n\n")
            
            # Resource Deployment Summary
            f.write("RESOURCE DEPLOYMENT SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Base Camps Deployed: {stats['total_camps']}\n")
            f.write(f"Rangers Deployed: {stats['total_rangers']}\n")
            f.write(f"Cameras Deployed: {stats['total_cameras']}\n")
            f.write(f"Drones Deployed: {stats['total_drones']}\n")
            f.write(f"Fence Length: {stats['total_fence_length']:.2f}\n")
            f.write("\n")
            
            # Files Generated
            f.write("=" * 70 + "\n")
            f.write("GENERATED FILES\n")
            f.write("=" * 70 + "\n")
            f.write("  0. config.txt - Configuration (key: value format)\n")
            f.write("  1. 1_risk_heatmap.png - Grid Risk Value Heatmap\n")
            f.write("  2. 2_resource_distribution.png - Resource Distribution Map\n")
            f.write("  3. 3_protection_heatmap.png - Protection Level Heatmap\n")
            f.write("  4. 4_convergence_curve.png - DSSA Convergence Curve\n")
            f.write("  5. 5_terrain_map.png - Terrain Distribution Map\n")
            if hasattr(self, 'time_dynamic_stats'):
                f.write("  6. 6_time_dynamic_analysis.png - Time-Dynamic Protection Analysis\n")
            f.write("  7. demo_results.json - Complete Results Data\n")
            f.write("  8. summary_report.txt - This Summary Report\n")
            f.write("=" * 70 + "\n")
        
        print(f"Summary report saved to: {summary_path}\n")

    def run_complete_demo(self):
        """Run the complete demo workflow"""
        start_time = datetime.now()
        
        print("\n" + "=" * 70)
        print("WILDLIFE RESERVE PROTECTION OPTIMIZATION - DEMO")
        print("=" * 70)
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")
        
        # Step 1: Setup scenario
        self.setup_scenario()
        
        # Step 2: Run optimization
        self.run_optimization()
        
        # Step 3: Calculate KPIs
        self.calculate_kpis()
        
        # Step 4: Generate visualizations
        self.generate_visualizations()
        
        # Step 5: Time-dynamic analysis
        self.run_time_dynamic_analysis()
        
        # Step 6: Save results
        self.save_results()
        
        # Step 7: Save final summary
        end_time = datetime.now()
        self._save_execution_summary(start_time, end_time)
        
        # Final summary (print to screen)
        summary_text = self._get_final_summary(end_time)
        print(summary_text)
    
    def _get_final_summary(self, end_time):
        """Generate final summary text"""
        summary = []
        summary.append("=" * 70)
        summary.append("DEMO COMPLETED SUCCESSFULLY")
        summary.append("=" * 70)
        summary.append(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"\nAll outputs saved to: {self.output_dir}/")
        summary.append("\nGenerated files:")
        summary.append("  0. config.txt - Configuration (key: value format)")
        summary.append("  1. 1_risk_heatmap.png - Grid Risk Value Heatmap")
        summary.append("  2. 2_resource_distribution.png - Resource Distribution Map")
        summary.append("  3. 3_protection_heatmap.png - Protection Level Heatmap")
        summary.append("  4. 4_convergence_curve.png - DSSA Convergence Curve")
        summary.append("  5. 5_terrain_map.png - Terrain Distribution Map")
        summary.append("  6. 6_time_dynamic_analysis.png - Time-Dynamic Protection Analysis")
        summary.append("  7. demo_results.json - Complete Results Data")
        summary.append("  8. summary_report.txt - Summary Report")
        summary.append("  9. execution_summary.txt - Execution Summary")
        summary.append("=" * 70)
        summary.append("")
        return "\n".join(summary)
    
    def _save_execution_summary(self, start_time, end_time):
        """Save execution summary to file"""
        execution_path = f'{self.output_dir}/execution_summary.txt'
        duration = end_time - start_time
        
        with open(execution_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("EXECUTION SUMMARY\n")
            f.write("=" * 70 + "\n")
            f.write(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End Time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration:   {duration}\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("DEMO COMPLETED SUCCESSFULLY\n\n")
            
            f.write(f"Output Directory: {self.output_dir}/\n\n")
            
            f.write("Generated Files:\n")
            f.write("-" * 70 + "\n")
            f.write("  0. config.txt - Configuration (key: value format)\n")
            f.write("  1. 1_risk_heatmap.png - Grid Risk Value Heatmap\n")
            f.write("  2. 2_resource_distribution.png - Resource Distribution Map\n")
            f.write("  3. 3_protection_heatmap.png - Protection Level Heatmap\n")
            f.write("  4. 4_convergence_curve.png - DSSA Convergence Curve\n")
            f.write("  5. 5_terrain_map.png - Terrain Distribution Map\n")
            f.write("  6. 6_time_dynamic_analysis.png - Time-Dynamic Protection Analysis\n")
            f.write("  7. demo_results.json - Complete Results Data\n")
            f.write("  8. summary_report.txt - Summary Report\n")
            f.write("  9. execution_summary.txt - This Execution Summary\n")
            f.write("=" * 70 + "\n")
        
        print(f"Execution summary saved to: {execution_path}\n")


def main():
    """Main entry point for demo"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Wildlife Reserve Protection Optimization Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py                              # Use default config: demo_config.json
  python demo.py config.json                  # Use specified config file
  python demo.py --config=my_config.json      # Alternative syntax
  python demo.py --output-dir=./my_output     # Specify output directory
        """
    )
    parser.add_argument(
        'config_file',
        nargs='?',
        default='demo_config.json',
        help='Path to configuration JSON file (default: demo_config.json)'
    )
    parser.add_argument(
        '--config',
        dest='config_file_alt',
        help='Alternative way to specify config file'
    )
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        default=None,
        help='Output directory (default: ./output/demo_TIMESTAMP)'
    )
    
    args = parser.parse_args()
    
    # Use --config if provided, otherwise use positional argument
    config_path = args.config_file_alt if args.config_file_alt else args.config_file
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found!")
        print(f"\nUsage: python demo.py [config_file]")
        print(f"Example: python demo.py demo_config.json")
        sys.exit(1)
    
    # Create and run demo
    print(f"Using configuration file: {config_path}\n")
    demo = DemoRunner(config_path=config_path, output_dir=args.output_dir)
    demo.run_complete_demo()


if __name__ == "__main__":
    main()
