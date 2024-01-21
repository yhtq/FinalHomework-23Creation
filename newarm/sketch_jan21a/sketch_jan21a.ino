#include "tools.h"
void setup() {
  // 初始化串口通信
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    if (receivedChar == 'p') {
      int num1 = readNumberFromSerial(); // 读取第一个值
      int num2 = readNumberFromSerial(); // 读取第二个值
      servo_move(num1); // 控制舵机移动
      stepper_move(num2); // 控制步进电机移动
    }
  }
}

int readNumberFromSerial() {
  char numberChars[10]; // 存储数字字符的数组
  int index = 0;
  while (Serial.available() > 0) {
    char digit = Serial.read();
    if (isdigit(digit) || digit == '-') {
      numberChars[index++] = digit;
    } else if (digit == ',') {
      break;
    }
  }
  numberChars[index] = '\0'; // 添加字符串终止符
  return atoi(numberChars); // 将字符数组转换为整数
}

void servo_move(int angle) {
  // 控制舵机移动的逻辑
  // 使用接收到的角度值来控制舵机的位置
}

void stepper_move(int steps) {
  // 控制步进电机移动的逻辑
  // 使用接收到的步数值来控制步进电机的运动
}

#include "tools.h"
#include<Servo.h>
void setup(){
Serial.begin(115200);
Timer_Setup();
Ir_Setup();
Stepper_Setup(); 
Servo_Setup(); 
Servo1_Setup();
pinMode(13,OUTPUT);
}

bool pendown = false;
char Buffer[20];
char fengefu[] = ",";
int Len = 0;
float stepper_move;
float servo_move;
int pen;
char BoardLED = 1;


void loop(){
  Timer_Loop();
  Stepper_Loop();
  Servo_Loop();
  Servo1_Loop();
  while (Serial.available()) {   
    Buffer[Len] = Serial.read();   
    if ((Buffer[Len] == 'p') || (Len >= 18))
    {
      Buffer[Len] = 0;
      //Serial.println(Buffer);
      
      Len = 0;
    }
    else{
      if(Buffer[Len]==0){
        digitalWrite(13, BoardLED);
        BoardLED = 1 - BoardLED;
        delay(10);
      }
      Len ++;
    }

        
  }
  if (strchr(Buffer, ',') == NULL){
    sscanf(Buffer,'%d',&pen);
    if (pen == 1){
      Servo1_Turn(UP);
    }
    if (pen == 0){
      Servo1_Turn(DOWN);
    }
  }
  else{
    char* tokens;
    tokens = strtok(Buffer,fengefu[0]);
    int i = 0;
    while (tokens[i] != NULL){
      stepper_move = atof(tokens[i]);
      servo_move = atof(tokens[i+1]);
      i++;
    }
    if (stepper_move != 0){
        if (stepper_move > 0){
          Stepper_Go(GO_FAR,stepper_move);
        }
        if (stepper_move < 0){
          Stepper_Go(GO_NEAR,-stepper_move);
        }
    }
    if (servo_move != 0){
      if (servo_move > 0){
        Servo_Turn(CW,servo_move);
      }
      if (servo_move < 0){
        Servo_Turn(CCW,-servo_move);
      }
    }
  }



//if (Ir_Check() == true) {
//  Serial.println(Ir_Data);
//switch(Ir_Data){
//case 24: Stepper_Go(GO_FAR,100); break; //电机
//case 74: Stepper_Go(GO_NEAR,300); break; 
//case 56: if (pendown==true){Servo1_Turn(DOWN);}else{Servo1_Turn(UP);}pendown =! pendown;break;
//case 16: Servo_Turn(CW,1); break; //舵机
//case 90: Servo_Turn(CCW,1); break; 
//}
//}
}


