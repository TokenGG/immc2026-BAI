import numpy as np
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
import random
from coverage_model import CoverageModel, DeploymentSolution


@dataclass
class DSSAConfig:
    population_size: int = 50
    max_iterations: int = 100
    producer_ratio: float = 0.2
    scout_ratio: float = 0.2
    ST: float = 0.8
    R2: float = 0.5


class DSSAOptimizer:
    def __init__(self, coverage_model: CoverageModel, constraints: Dict[str, any],
                 config: DSSAConfig = None, fixed_fences: Dict[Tuple[int, int], int] = None):
        self.coverage_model = coverage_model
        self.constraints = constraints
        self.config = config or DSSAConfig()
        self.grid_model = coverage_model.grid_model
        self.grid_ids = self.grid_model.get_all_grid_ids()
        self.fencing_edges = self.grid_model.get_fencing_edges()
        # 固定围栏：不参与优化，每个解都使用相同的围栏部署
        self.fixed_fences = fixed_fences or {}

        self.population = []
        self.fitness_history = []
        self.best_solution = None
        self.best_fitness = float('-inf')

    def _initialize_solution(self) -> DeploymentSolution:
        cameras = {}
        camps = {}
        drones = {}
        rangers = {}
        fences = {}

        grid_ids_shuffled = self.grid_ids.copy()
        random.shuffle(grid_ids_shuffled)

        cameras_to_deploy = min(self.constraints['total_cameras'], len(grid_ids_shuffled))
        for i in range(cameras_to_deploy):
            grid_id = grid_ids_shuffled[i]
            if self.coverage_model.deployment_matrix['camera'][grid_id] == 1:
                cameras[grid_id] = 1

        drones_to_deploy = min(self.constraints['total_drones'], len(grid_ids_shuffled))
        for i in range(drones_to_deploy):
            grid_id = grid_ids_shuffled[(i + cameras_to_deploy) % len(grid_ids_shuffled)]
            if self.coverage_model.deployment_matrix['drone'][grid_id] == 1:
                drones[grid_id] = 1

        camps_to_deploy = min(self.constraints['total_camps'], len(grid_ids_shuffled))
        for i in range(camps_to_deploy):
            grid_id = grid_ids_shuffled[(i + cameras_to_deploy + drones_to_deploy) % len(grid_ids_shuffled)]
            if self.coverage_model.deployment_matrix['camp'][grid_id] == 1:
                camps[grid_id] = 1
                rangers[grid_id] = min(random.randint(1, self.constraints['max_rangers_per_camp']),
                                      self.constraints['total_patrol'])
        
        # 直接部署巡逻人员（不需要营地）
        if self.constraints['total_patrol'] > 0 and len(rangers) < self.constraints['total_patrol']:
            remaining_rangers = self.constraints['total_patrol'] - sum(rangers.values())
            for i in range(remaining_rangers):
                # 找到一个未部署资源的网格
                for grid_id in grid_ids_shuffled:
                    if (grid_id not in cameras and 
                        grid_id not in drones and 
                        grid_id not in camps and
                        self.coverage_model.deployment_matrix['patrol'][grid_id] == 1):
                        rangers[grid_id] = 1
                        break

        edges_shuffled = self.fencing_edges.copy()
        random.shuffle(edges_shuffled)

        # 围栏固定部署，直接使用 fixed_fences
        fences = dict(self.fixed_fences)

        solution = DeploymentSolution(
            cameras=cameras,
            camps=camps,
            drones=drones,
            rangers=rangers,
            fences=fences
        )

        return self.coverage_model.repair_solution(solution, self.constraints)

    def initialize_population(self):
        self.population = []
        for _ in range(self.config.population_size):
            solution = self._initialize_solution()
            self.population.append(solution)

    def evaluate_fitness(self, solution: DeploymentSolution) -> float:
        is_valid, violations = self.coverage_model.validate_solution(solution, self.constraints)
        if not is_valid:
            penalty = len(violations) * 1000
            return -penalty

        benefit = self.coverage_model.calculate_total_benefit(solution)
        return benefit

    def _solution_to_vector(self, solution: DeploymentSolution) -> np.ndarray:
        vector = []
        for grid_id in self.grid_ids:
            vector.append(solution.cameras.get(grid_id, 0))
        for grid_id in self.grid_ids:
            vector.append(solution.camps.get(grid_id, 0))
        for grid_id in self.grid_ids:
            vector.append(solution.drones.get(grid_id, 0))
        for grid_id in self.grid_ids:
            vector.append(solution.rangers.get(grid_id, 0))
        # 围栏不参与向量编码
        return np.array(vector)

    def _vector_to_solution(self, vector: np.ndarray) -> DeploymentSolution:
        cameras = {}
        camps = {}
        drones = {}
        rangers = {}

        idx = 0
        for grid_id in self.grid_ids:
            if vector[idx] > 0.5:
                cameras[grid_id] = 1
            idx += 1
        for grid_id in self.grid_ids:
            if vector[idx] > 0.5:
                camps[grid_id] = 1
            idx += 1
        for grid_id in self.grid_ids:
            if vector[idx] > 0.5:
                drones[grid_id] = 1
            idx += 1
        for grid_id in self.grid_ids:
            val = int(round(vector[idx]))
            if val > 0 and self.coverage_model.deployment_matrix['patrol'][grid_id] == 1:
                rangers[grid_id] = val
            idx += 1

        # 围栏固定，不从向量恢复
        return DeploymentSolution(
            cameras=cameras,
            camps=camps,
            drones=drones,
            rangers=rangers,
            fences=dict(self.fixed_fences)
        )

    def _update_producers(self, iteration: int):
        num_producers = int(self.config.population_size * self.config.producer_ratio)
        producers = self.population[:num_producers]

        for i, solution in enumerate(producers):
            if i == 0:
                current_vector = self._solution_to_vector(solution)
                best_vector = self._solution_to_vector(self.best_solution)
                new_vector = current_vector + np.random.uniform(0, 1, current_vector.shape) * (best_vector - current_vector)
            else:
                current_vector = self._solution_to_vector(solution)
                new_vector = current_vector + np.random.uniform(-1, 1, current_vector.shape)

            new_solution = self._vector_to_solution(new_vector)
            new_solution = self.coverage_model.repair_solution(new_solution, self.constraints)

            current_fitness = self.evaluate_fitness(solution)
            new_fitness = self.evaluate_fitness(new_solution)

            if new_fitness > current_fitness:
                self.population[i] = new_solution

    def _update_followers(self):
        num_producers = int(self.config.population_size * self.config.producer_ratio)
        num_followers = int(self.config.population_size * (1 - self.config.producer_ratio))
        followers = self.population[num_producers:num_producers + num_followers]

        for i, solution in enumerate(followers):
            if i > self.config.population_size / 2:
                current_vector = self._solution_to_vector(solution)
                best_vector = self._solution_to_vector(self.best_solution)
                new_vector = np.abs(best_vector - current_vector) * np.random.uniform(0, 1, current_vector.shape)
            else:
                idx = random.randint(0, num_producers - 1)
                producer = self.population[idx]
                current_vector = self._solution_to_vector(solution)
                producer_vector = self._solution_to_vector(producer)
                new_vector = current_vector + np.random.uniform(0, 1, current_vector.shape) * (producer_vector - current_vector)

            new_solution = self._vector_to_solution(new_vector)
            new_solution = self.coverage_model.repair_solution(new_solution, self.constraints)

            current_fitness = self.evaluate_fitness(solution)
            new_fitness = self.evaluate_fitness(new_solution)

            if new_fitness > current_fitness:
                self.population[num_producers + i] = new_solution

    def _update_scouts(self):
        num_scouts = int(self.config.population_size * self.config.scout_ratio)
        start_idx = self.config.population_size - num_scouts

        for i in range(start_idx, self.config.population_size):
            solution = self.population[i]
            fitness = self.evaluate_fitness(solution)

            if fitness < self.config.ST * self.best_fitness:
                new_solution = self._initialize_solution()
                self.population[i] = new_solution

    def _update_best_solution(self):
        for solution in self.population:
            fitness = self.evaluate_fitness(solution)
            if fitness > self.best_fitness:
                self.best_fitness = fitness
                self.best_solution = solution

    def optimize(self, callback: Callable[[int, float, DeploymentSolution], None] = None) -> Tuple[DeploymentSolution, float, List[float]]:
        import time

        self.initialize_population()

        for solution in self.population:
            fitness = self.evaluate_fitness(solution)
            if fitness > self.best_fitness:
                self.best_fitness = fitness
                self.best_solution = solution

        self.fitness_history = [self.best_fitness]

        total_start = time.time()
        iter_times = []

        for iteration in range(self.config.max_iterations):
            iter_start = time.time()

            self._update_producers(iteration)
            self._update_followers()
            self._update_scouts()
            self._update_best_solution()

            iter_elapsed = time.time() - iter_start
            iter_times.append(iter_elapsed)

            self.fitness_history.append(self.best_fitness)

            if callback:
                callback(iteration, self.best_fitness, self.best_solution)

            avg_iter = sum(iter_times) / len(iter_times)
            print(f"Iter {iteration+1:>4}/{self.config.max_iterations}"
                  f"  fitness={self.best_fitness:.6f}"
                  f"  iter={iter_elapsed*1000:.1f}ms"
                  f"  avg={avg_iter*1000:.1f}ms")

        total_elapsed = time.time() - total_start
        print(f"\nOptimization completed."
              f"  Best Fitness = {self.best_fitness:.6f}"
              f"  Total = {total_elapsed:.2f}s"
              f"  Avg/iter = {total_elapsed/self.config.max_iterations*1000:.1f}ms")

        return self.best_solution, self.best_fitness, self.fitness_history

    def get_solution_statistics(self, solution: DeploymentSolution) -> Dict[str, any]:
        stats = {
            'total_cameras': sum(solution.cameras.values()),
            'total_drones': sum(solution.drones.values()),
            'total_camps': sum(solution.camps.values()),
            'total_rangers': sum(solution.rangers.values()),
            'total_fence_length': sum(solution.fences.values()),
            'camera_locations': [grid_id for grid_id, count in solution.cameras.items() if count > 0],
            'drone_locations': [grid_id for grid_id, count in solution.drones.items() if count > 0],
            'ranger_locations': [grid_id for grid_id, count in solution.rangers.items() if count > 0],
            'camp_locations': [grid_id for grid_id, count in solution.camps.items() if count > 0],
            'fence_edges': [edge for edge, count in solution.fences.items() if count > 0]
        }
        return stats
