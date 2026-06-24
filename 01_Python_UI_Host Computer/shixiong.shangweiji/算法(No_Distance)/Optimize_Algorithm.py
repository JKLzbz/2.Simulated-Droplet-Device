# 麻雀优化算法
import numpy as np


class SparrowSearchAlgorithm:
    def __init__(self, n_sparrows, n_iter, bounds):
        self.n_sparrows = n_sparrows
        self.n_iter = n_iter
        self.bounds = bounds
        self.sparrows = np.random.uniform(bounds[0], bounds[1], (n_sparrows, len(bounds[0])))
        self.best_sparrow = None
        self.best_fitness = float('inf')

    def optimize(self, fitness_func):
        for i in range(self.n_iter):
            for j in range(self.n_sparrows):
                fitness = fitness_func(self.sparrows[j])
                if fitness < self.best_fitness:
                    self.best_fitness = fitness
                    self.best_sparrow = self.sparrows[j]
            self.sparrows = self.update_sparrows()
        return self.best_sparrow

    def update_sparrows(self):
        new_sparrows = np.zeros_like(self.sparrows)
        for i in range(self.n_sparrows):
            new_sparrows[i] = self.sparrows[i] + np.random.uniform(-1, 1, len(self.bounds[0])) * (self.best_sparrow - self.sparrows[i])
            new_sparrows[i] = np.clip(new_sparrows[i], self.bounds[0], self.bounds[1])
        return new_sparrows
