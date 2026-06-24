import numpy as np
import random
import math
import copy

''' 种群初始化函数 '''


def initial(pop, dim, ub, lb):
    X = np.zeros([pop, dim])
    for i in range(pop):
        for j in range(dim):
            X[i, j] = random.random() * (ub[j] - lb[j]) + lb[j]

    return X, lb, ub


'''边界检查函数'''


def BorderCheck(X, ub, lb, pop, dim):
    for i in range(pop):
        for j in range(dim):
            if X[i, j] > ub[j]:
                X[i, j] = ub[j]
            elif X[i, j] < lb[j]:
                X[i, j] = lb[j]
    return X


'''计算适应度函数'''


def CaculateFitness(X, fun):
    pop = X.shape[0]
    fitness = np.zeros([pop, 1])
    for i in range(pop):
        fitness[i] = fun(X[i, :])
    return fitness


'''适应度排序'''


def SortFitness(Fit):
    fitness = np.sort(Fit, axis=0)
    index = np.argsort(Fit, axis=0)
    return fitness, index


'''根据适应度对位置进行排序'''


def SortPosition(X, index):
    Xnew = np.zeros(X.shape)
    for i in range(X.shape[0]):
        Xnew[i, :] = X[index[i], :]
    return Xnew


'''沙猫群优化算法'''


def SCSO(pop, dim, lb, ub, MaxIter, fun):
    # 参数
    X, lb, ub = initial(pop, dim, ub, lb)  # 初始化种群
    fitness = CaculateFitness(X, fun)  # 计算适应度值
    indexBest = np.argmin(fitness)
    GbestScore = copy.copy(fitness[indexBest])
    GbestPositon = np.zeros([1, dim])
    GbestPositon[0, :] = copy.copy(X[indexBest, :])
    Curve = np.zeros([MaxIter, 1])
    for t in range(MaxIter):
        SM=2  #敏感度
        rg=SM-(SM*t/MaxIter)
        for i in range(pop):
            r=np.random.random()*rg
            R=2*rg*np.random.random()-rg # 探索利用转换参数
            for j in range(dim):
                theta = np.random.random()*2*np.pi #[0-360]
                if np.abs(R)<=1:
                    RandPos = np.abs(np.random.random()*GbestPositon[0,j]-X[i,j])
                    X[i,j] = GbestPositon[0,j]-r*RandPos*np.cos(theta)
                else:
                    Rindex=int(pop*np.random.random())
                    X[i,j]=r*(X[Rindex,j]-np.random.random()*X[i,j])
        X = BorderCheck(X, ub, lb, pop, dim)
        fitness = CaculateFitness(X, fun)
        indexBest = np.argmin(fitness)
        if fitness[indexBest] <= GbestScore:  # 更新全局最优
            GbestScore = copy.copy(fitness[indexBest])
            GbestPositon[0, :] = copy.copy(X[indexBest, :])
        Curve[t] = GbestScore

    return GbestScore, GbestPositon, Curve
