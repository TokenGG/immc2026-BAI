#!/usr/bin/env python3
"""
Batch Run Script for Resource Inventory Analysis
批量运行脚本，用于分析不同资源配置的影响

Usage:
    python batch_run.py --runs 10
    python batch_run.py --runs 5 --start 2 --min 3
    python batch_run.py --runs 10 --min 2 --range 4
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
import random
from datetime import datetime
from typing import Dict, List
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed


class BatchRunner:
    def __init__(self, base_config_path: str, output_dir: str,
                 runs: int, start: int, min_step: int, step_range: int, max_workers: int = 4):
        """Initialize batch runner"""
        self.base_config_path = base_config_path
        self.output_dir = output_dir
        self.runs = runs
        self.start = start
        self.min_step = min_step
        self.step_range = step_range
        self.max_workers = max_workers

        # Resource types to test
        self.resource_types = [
            'patrol_personnel',
            'uavs',
            'surveillance_cameras',
            'base_camps',
            'fence_inventory'
        ]

        # Load base configuration
        self.base_config = self.load_base_config()

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Results storage
        self.results = {resource: [] for resource in self.resource_types}
        # Store step information
        self.step_info = {resource: [] for resource in self.resource_types}
        # Store task info for each run
        self.task_infos = {resource: [] for resource in self.resource_types}

    def load_base_config(self) -> Dict:
        """Load base configuration file"""
        print(f"Loading base configuration from {self.base_config_path}...")
        with open(self.base_config_path, 'r') as f:
            config = json.load(f)
        return config

    def create_config(self, resource_type: str, value: int) -> Dict:
        """Create configuration with specified resource value"""
        config = json.loads(json.dumps(self.base_config))  # Deep copy

        # Set all resources to 1
        config['resource_inventory']['patrol_personnel'] = 1
        config['resource_inventory']['uavs'] = 1
        config['resource_inventory']['surveillance_cameras'] = 1
        config['resource_inventory']['base_camps'] = 1
        config['resource_inventory']['fence_inventory'] = 1
        config['resource_inventory']['camp_capacity'] = 3  # Keep camp capacity constant

        # Set the target resource to specified value
        config['resource_inventory'][resource_type] = value

        return config

    def generate_values(self, resource_type: str) -> List[int]:
        """Generate resource values based on random step mode"""
        values = []
        steps_used = []

        current_value = self.start
        values.append(current_value)
        steps_used.append(0)  # first step has no increment

        for i in range(1, self.runs):
            step_size = random.randint(self.min_step, self.min_step + self.step_range)
            current_value += step_size
            values.append(current_value)
            steps_used.append(step_size)

        # Save step info for this resource
        self.step_info[resource_type] = steps_used

        return values

    def prepare_configs_for_resource(self, resource_type: str):
        """Prepare all config files for a single resource type"""
        print(f"Preparing configurations for {resource_type}...")

        resource_dir = os.path.join(self.output_dir, resource_type)
        os.makedirs(resource_dir, exist_ok=True)

        values = self.generate_values(resource_type)
        task_infos = []

        for i in range(self.runs):
            value = values[i]
            step_used = self.step_info[resource_type][i]

            # Create run-specific directory
            run_dir = os.path.join(resource_dir, f"run_{i+1:03d}_value_{value}")
            os.makedirs(run_dir, exist_ok=True)

            # Create configuration
            config = self.create_config(resource_type, value)

            # Save temporary config
            temp_config_path = os.path.join(run_dir, 'temp_config.json')
            with open(temp_config_path, 'w') as f:
                json.dump(config, f, indent=2)

            task_info = {
                'resource_type': resource_type,
                'run_number': i + 1,
                'value': value,
                'step_used': step_used,
                'config_path': temp_config_path,
                'run_dir': run_dir
            }
            task_infos.append(task_info)

        self.task_infos[resource_type] = task_infos
        print(f"  [OK] Prepared {self.runs} configurations for {resource_type}")

    def prepare_all_configs(self):
        """Prepare all config files for all resource types"""
        print("\n" + "=" * 70)
        print("PREPARING CONFIGURATIONS")
        print("=" * 70)
        for resource_type in self.resource_types:
            self.prepare_configs_for_resource(resource_type)

    @staticmethod
    def run_single_task_static(task_info: Dict) -> Dict:
        """Static method to run a single demo.py task (for concurrent execution)"""
        config_path = task_info['config_path']
        run_dir = task_info['run_dir']

        result = {
            'task_info': task_info,
            'success': False,
            'metrics': None,
            'error': None
        }

        try:
            # Run demo.py as subprocess with output directory
            proc_result = subprocess.run(
                [sys.executable, 'demo.py', config_path, '--output-dir', run_dir],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if proc_result.returncode != 0:
                result['error'] = proc_result.stderr
                return result

            # Extract results
            results_file = os.path.join(run_dir, 'demo_results.json')
            if not os.path.exists(results_file):
                result['error'] = f"Results file not found: {results_file}"
                return result

            with open(results_file, 'r') as f:
                data = json.load(f)

            # Extract key metrics
            metrics = {
                'best_fitness': data['optimization_results']['best_fitness'],
                'total_protection_benefit': data['kpis']['total_protection_benefit'],
                'average_protection_benefit': data['kpis']['average_protection_benefit'],
                'grid_coverage_percentage': data['kpis']['grid_coverage_percentage'],
                'iterations': data['optimization_results']['iterations']
            }

            # Add time-dynamic stats if available
            if 'time_dynamic_stats' in data:
                metrics['avg_protection'] = data['time_dynamic_stats']['avg_protection']
                metrics['min_staffing'] = data['time_dynamic_stats']['min_staffing']

            result['metrics'] = metrics
            result['success'] = True

        except subprocess.TimeoutExpired:
            result['error'] = "Timeout: demo.py took longer than 10 minutes"
        except Exception as e:
            result['error'] = str(e)

        return result

    def run_resource_concurrent(self, resource_type: str):
        """Run all tasks for a single resource type concurrently"""
        print(f"\n{'=' * 70}")
        print(f"Testing: {resource_type.upper()} (concurrent)")
        print(f"{'=' * 70}")
        print(f"Concurrent workers: {self.max_workers}")
        print(f"{'=' * 70}")

        task_infos = self.task_infos[resource_type]
        resource_results = []

        # Use ProcessPoolExecutor with max_workers
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.run_single_task_static, task_info): task_info
                for task_info in task_infos
            }

            # Process results as they complete
            completed = 0
            for future in as_completed(future_to_task):
                task_info = future_to_task[future]
                completed += 1

                try:
                    result = future.result()
                    if result['success']:
                        metrics = result['metrics']
                        metrics['resource_type'] = resource_type
                        metrics['resource_value'] = task_info['value']
                        metrics['run_number'] = task_info['run_number']
                        metrics['step_used'] = task_info['step_used']
                        resource_results.append((task_info['run_number'], metrics))

                        print(f"[{completed}/{self.runs}] Run {task_info['run_number']}: "
                              f"{resource_type} = {task_info['value']} (step = +{task_info['step_used']}) "
                              f"[OK] fitness = {metrics['best_fitness']:.4f}")
                    else:
                        print(f"[{completed}/{self.runs}] Run {task_info['run_number']}: "
                              f"{resource_type} = {task_info['value']} [ERROR] {result['error']}")
                except Exception as e:
                    print(f"[{completed}/{self.runs}] Run {task_info['run_number']}: "
                          f"{resource_type} = {task_info['value']} [EXCEPTION] {e}")

        # Sort results by run number and store
        resource_results.sort(key=lambda x: x[0])
        self.results[resource_type] = [r for (_, r) in resource_results]

        success_count = len(self.results[resource_type])
        print(f"\n{resource_type.upper()} completed: {success_count}/{self.runs} successful runs")

    def run_batch(self):
        """Run batch experiments"""
        print("\n" + "=" * 70)
        print("BATCH RUN - RESOURCE INVENTORY ANALYSIS")
        print("=" * 70)
        print(f"Configuration:")
        print(f"  - Runs per resource: {self.runs}")
        print(f"  - Start value: {self.start}")
        print(f"  - Step range: {self.min_step} - {self.min_step + self.step_range}")
        print(f"  - Concurrent workers: {self.max_workers}")
        print(f"  - Output directory: {self.output_dir}")
        print("=" * 70)

        # Prepare all configurations first
        self.prepare_all_configs()

        # Run each resource type sequentially, with concurrent runs within each
        for resource_type in self.resource_types:
            self.run_resource_concurrent(resource_type)

        print(f"\n{'=' * 70}")
        print("BATCH RUN COMPLETED")
        print(f"{'=' * 70}\n")

    def generate_summary(self):
        """Generate summary report"""
        print("Generating summary report...")

        summary = {
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'runs_per_resource': self.runs,
                'start_value': self.start,
                'min_step': self.min_step,
                'step_range': self.step_range,
                'step_min': self.min_step,
                'step_max': self.min_step + self.step_range,
                'base_config': self.base_config_path
            },
            'results_by_resource': {}
        }

        # Analyze each resource type
        for resource_type in self.resource_types:
            if not self.results[resource_type]:
                continue

            results = self.results[resource_type]

            # Extract values and metrics
            values = [r['resource_value'] for r in results]
            fitness_values = [r['best_fitness'] for r in results]
            protection_values = [r['total_protection_benefit'] for r in results]
            coverage_values = [r['grid_coverage_percentage'] for r in results]

            # Calculate statistics
            resource_summary = {
                'total_runs': len(results),
                'value_range': [min(values), max(values)],
                'values': values,
                'steps_used': self.step_info[resource_type],
                'fitness': {
                    'values': fitness_values,
                    'mean': float(np.mean(fitness_values)),
                    'std': float(np.std(fitness_values)),
                    'min': float(np.min(fitness_values)),
                    'max': float(np.max(fitness_values))
                },
                'protection_benefit': {
                    'values': protection_values,
                    'mean': float(np.mean(protection_values)),
                    'std': float(np.std(protection_values)),
                    'min': float(np.min(protection_values)),
                    'max': float(np.max(protection_values))
                },
                'coverage': {
                    'values': coverage_values,
                    'mean': float(np.mean(coverage_values)),
                    'std': float(np.std(coverage_values)),
                    'min': float(np.min(coverage_values)),
                    'max': float(np.max(coverage_values))
                },
                'detailed_results': results
            }

            summary['results_by_resource'][resource_type] = resource_summary

        # Save JSON summary
        summary_json_path = os.path.join(self.output_dir, 'batch_summary.json')
        with open(summary_json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  [OK] JSON summary saved: {summary_json_path}")

        # Save text summary
        self._save_text_summary(summary)

    def _save_text_summary(self, summary: Dict):
        """Save human-readable text summary"""
        summary_txt_path = os.path.join(self.output_dir, 'batch_summary.txt')

        with open(summary_txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("BATCH RUN SUMMARY REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            # Configuration
            f.write("CONFIGURATION\n")
            f.write("-" * 70 + "\n")
            f.write(f"Runs per resource: {summary['configuration']['runs_per_resource']}\n")
            f.write(f"Start value: {summary['configuration']['start_value']}\n")
            f.write(f"Step range: {summary['configuration']['step_min']} - {summary['configuration']['step_max']}\n")
            f.write(f"Base config: {summary['configuration']['base_config']}\n")
            f.write("\n")

            # Results for each resource
            for resource_type, data in summary['results_by_resource'].items():
                f.write("=" * 70 + "\n")
                f.write(f"{resource_type.upper().replace('_', ' ')}\n")
                f.write("=" * 70 + "\n")
                f.write(f"Total runs: {data['total_runs']}\n")
                f.write(f"Value range: {data['value_range'][0]} - {data['value_range'][1]}\n")
                f.write("\n")

                f.write("Best Fitness:\n")
                f.write(f"  Mean:   {data['fitness']['mean']:.4f}\n")
                f.write(f"  Std:    {data['fitness']['std']:.4f}\n")
                f.write(f"  Min:    {data['fitness']['min']:.4f}\n")
                f.write(f"  Max:    {data['fitness']['max']:.4f}\n")
                f.write("\n")

                f.write("Protection Benefit:\n")
                f.write(f"  Mean:   {data['protection_benefit']['mean']:.4f}\n")
                f.write(f"  Std:    {data['protection_benefit']['std']:.4f}\n")
                f.write(f"  Min:    {data['protection_benefit']['min']:.4f}\n")
                f.write(f"  Max:    {data['protection_benefit']['max']:.4f}\n")
                f.write("\n")

                f.write("Grid Coverage (%):\n")
                f.write(f"  Mean:   {data['coverage']['mean']:.2f}%\n")
                f.write(f"  Std:    {data['coverage']['std']:.2f}%\n")
                f.write(f"  Min:    {data['coverage']['min']:.2f}%\n")
                f.write(f"  Max:    {data['coverage']['max']:.2f}%\n")
                f.write("\n")

                # Detailed results table
                f.write("Detailed Results:\n")
                f.write("-" * 70 + "\n")
                f.write(f"{'Run':<6} {'Value':<8} {'Step':<6} {'Fitness':<12} {'Protection':<12} {'Coverage':<10}\n")
                f.write("-" * 70 + "\n")
                for idx, result in enumerate(data['detailed_results']):
                    step_display = f"+{data['steps_used'][idx]}" if idx > 0 else "-"
                    f.write(f"{result['run_number']:<6} "
                           f"{result['resource_value']:<8} "
                           f"{step_display:<6} "
                           f"{result['best_fitness']:<12.4f} "
                           f"{result['total_protection_benefit']:<12.4f} "
                           f"{result['grid_coverage_percentage']:<10.2f}%\n")
                f.write("\n")

            f.write("=" * 70 + "\n")

        print(f"  [OK] Text summary saved: {summary_txt_path}")

    def run(self):
        """Main execution method"""
        start_time = datetime.now()

        # Run batch experiments
        self.run_batch()

        # Generate summary
        self.generate_summary()

        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n{'=' * 70}")
        print("EXECUTION COMPLETE")
        print(f"{'=' * 70}")
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'=' * 70}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Batch run demo.py with different resource configurations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_run.py --runs 10
  python batch_run.py --runs 5 --start 2 --min 3
  python batch_run.py --runs 10 --min 2 --range 4
  python batch_run.py --runs 8 --start 1 --min 1 --output-dir ./my_batch_output

  # Random step mode: step in [min, min+range]
  # min=2, range=4 → random step in [2,6]
        """
    )

    parser.add_argument(
        '--runs',
        type=int,
        default=10,
        help='Number of runs per resource type (default: 10)'
    )
    parser.add_argument(
        '--start',
        type=int,
        default=1,
        help='Starting value for resource quantity (default: 1)'
    )
    parser.add_argument(
        '--min',
        type=int,
        default=2,
        help='Minimum step size for random increment (default: 2)'
    )
    parser.add_argument(
        '--range',
        type=int,
        default=4,
        help='Step range size: step_max = min + range (default: 4)'
    )
    parser.add_argument(
        '--base-config',
        type=str,
        default='demo_config.json',
        help='Path to base configuration file (default: demo_config.json)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./batch_output',
        help='Output directory for batch results (default: ./batch_output)'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Maximum number of concurrent workers (default: 4, recommended: 2-8)'
    )

    args = parser.parse_args()

    # Check if base config exists
    if not os.path.exists(args.base_config):
        print(f"Error: Base configuration file '{args.base_config}' not found!")
        sys.exit(1)

    # Check if demo.py exists
    if not os.path.exists('demo.py'):
        print(f"Error: demo.py not found in current directory!")
        print(f"Please run this script from the same directory as demo.py")
        sys.exit(1)

    # Validate parameters
    if args.runs < 1:
        print(f"Error: --runs must be at least 1, got {args.runs}")
        sys.exit(1)
    if args.start < 1:
        print(f"Error: --start must be at least 1, got {args.start}")
        sys.exit(1)
    if args.min < 1:
        print(f"Error: --min must be at least 1, got {args.min}")
        sys.exit(1)
    if args.range < 0:
        print(f"Error: --range must be at least 0, got {args.range}")
        sys.exit(1)
    if args.max_workers < 1:
        print(f"Error: --max-workers must be at least 1, got {args.max_workers}")
        sys.exit(1)
    
    # Warning for very high concurrency
    if args.max_workers > 8:
        print(f"Warning: --max-workers={args.max_workers} is very high")
        print(f"Recommended range: 2-4 for CPU version to avoid OpenBLAS errors")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted")
            sys.exit(0)

    # Create and run batch runner
    try:
        runner = BatchRunner(
            base_config_path=args.base_config,
            output_dir=args.output_dir,
            runs=args.runs,
            start=args.start,
            min_step=args.min,
            step_range=args.range,
            max_workers=args.max_workers
        )

        runner.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user (Ctrl+C)")
        print("Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
