import numpy as np
from matplotlib import pyplot as plt
import SCSO


'''定义目标函数用户可选fun1 - fun4 , 也可以自己定义自己的目标函数'''
def fun1(X):
        O=np.sum(X*X)
        return O

def fun2(X):
    O=np.sum(np.abs(X))+np.prod(np.abs(X))
    return O

def fun3(X):
    O=0
    for i in range(len(X)):
        O=O+np.square(np.sum(X[0:i+1]))   
    return O

def fun4(X):
    O=np.max(np.abs(X))
    return O





'''主函数 '''
#设置参数
pop = 30 #种群数量
MaxIter = 500#最大迭代次数
dim = 10 #维度
lb = -100*np.ones([dim, 1]) #下边界
ub = 100*np.ones([dim, 1])#上边界
#选择适应度函数
fobj = fun3
#原始算法
GbestScore,GbestPositon,Curve = SCSO.SCSO(pop,dim,lb,ub,MaxIter,fobj)


print('------#改进算法--------------')
print('最优适应度值：',GbestScore)
print('最优解：',GbestPositon)


#绘制适应度曲线
plt.figure(1)
plt.semilogy(Curve,'b--',linewidth=2)
plt.xlabel('Iteration',fontsize='medium')
plt.ylabel("Fitness",fontsize='medium')
plt.grid()
plt.title('SCSO',fontsize='large')
plt.legend(['SCSO'], loc='upper right')
plt.show()

