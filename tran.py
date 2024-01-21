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
timeflag = 0

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


def tran(polarcoor):
    info = polarcoor
    if type(info) == int:
        if info == 1:
            print('send up')
        elif info == 0:
            print('send down')
        else:
            print(f'数量是{info}个')
        mess = 'i'+str(info)
        print(mess)
        ser.write(mess.encode())
    elif type(info) == tuple:
        print(f'发送调整极坐标{info}')
        mess = 'p'+str(info[0])+','+str(info[1])
        print(mess)
        ser.write(mess.encode())
    elif type(info) == str:
        print('发送开始信号')
        print(info)
        ser.write(info.encode())
    # ser.close()
    sleep(0.5)
    global timeflag
    timeflag += 1
    if timeflag > 3:
        while True:
            data = ser.read(9999)
            if len(data) > 0:
                print('Got:', data)
            sleep(0.1)
            print('idling')
            if len(data) >= 1:
                break


startpoint = (0,0)
direction = (-40,-20)
endpoint = (startpoint[0]+direction[0],startpoint[1]+direction[1])
delta_x = endpoint[0]-startpoint[0]
delta_y = endpoint[1]-startpoint[1]
grid_num = max(abs(delta_x // gridwide), abs(delta_y // gridwide))
points = []
del_points = []

for pointnum in range(grid_num):
    points += [(startpoint[0]+pointnum/grid_num*delta_x, startpoint[1]+(pointnum/grid_num)*delta_y)]
points += [endpoint]


for poin in points:
    i = points.index(poin)
    points[i] = coor_to_polar(poin[0],poin[1])
    #point = polar_to_machine(point[0],point[1])
    if i == 0:
        del_points += [points[0]]
    else:
        del_points += [(points[i][0]-points[i-1][0],points[i][1]-points[i-1][1])]

#tran(grid_num + 2) # c传送数据总数
# print(del_points)
# tran('s')

for _ in range(len(points)):
    tran(del_points[_])
    if _ == 0:
        tran(0)
        pass
    if _ == len(points)-1:
        tran(1)
        pass


