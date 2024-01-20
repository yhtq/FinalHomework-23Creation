#读入的部分是两个坐标，将他们转化成一连串的极坐标
#10cm*10cm
#servo:+-12 -0.7+0.7弧度
#stepper:l+70 240-640 (8)
#35、36行的分别是起始点和向量
import math
#import UI
import serial
from time import sleep
port = r'/dev/cu.usbserial-1410'
ser = serial.Serial(port, 115200, timeout=0)
gridwide = 10

def coor_to_polar(x,y):
    realy = y - 200 # Settings.WIDTH*Settings.NUM_BLOCKS_y/2
    realx = x + 240 # Settings.HEIGHT * Settings.NUM_BLOCKS_x / 10 * 6
    # (0,0)->(0,L)

    r = round(math.sqrt(realx*realx+realy*realy))
    theta = round(math.atan2(realy,realx),3)
    polar = (r,theta)
    serv = int(theta*12/0.7)
    step = int((r-240)/8)
    machine = (step,serv)
    return machine

def polar_to_machine(r,theta):
    serv = int(theta*12/0.7)
    step = int((r-240)/8)
    machine = (step,serv)
    return tuple((step, serv))

def tran(polarcoor):
    info = polarcoor
    if info == 1 or info == 0:
        print('send up' if info else 'send down')
    else:
        print(f'发送极坐标{info}')
    ser.write(str(info).encode())
    # ser.close()
    #sleep(0.5)


startpoint = (0,200)
direction = (400,0)
endpoint = (startpoint[0]+direction[0],startpoint[1]+direction[1])
delta_x = endpoint[0]-startpoint[0]
delta_y = endpoint[1]-startpoint[1]
grid_num = max(abs(delta_x // gridwide), abs(delta_y // gridwide))
points = []

for pointnum in range(grid_num):
    points += [(startpoint[0]+pointnum/grid_num*delta_x, startpoint[1]+(pointnum/grid_num)*delta_y)]
points += [endpoint]


for poin in points:
    i = points.index(poin)
    points[i] = coor_to_polar(poin[0],poin[1])
    #point = polar_to_machine(point[0],point[1])
    if i == 0:
        continue
    #else:
        #points[i] = (points[i][0]-points[i-1][0],points[i][1]-points[i-1][1])

tran(grid_num + 2)

for _ in range(len(points)):
    tran(points[_])
    if _ == 0:
        tran(0)
    if _ == len(points)-1:
        tran(1)

