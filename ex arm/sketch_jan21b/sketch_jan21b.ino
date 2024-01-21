#include "tools.h"
void setup() {
  // 初始化串口通信
  Serial.begin(115200);
  Timer_Setup();
  Ir_Setup();
  Stepper_Setup(); 
  Servo_Setup(); 
  Servo1_Setup();
}

bool BoardLED = LOW;
//int num1,num2;
bool pendown = false;

void loop() {
  Timer_Loop();
  Stepper_Loop();
  Servo_Loop();
  Servo1_Loop();
  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    Serial.print(receivedChar);
    if (receivedChar == 's'){
      Serial.print('s');
    }
    if (receivedChar == 'i'){
      int com = readNumberFromSerial();
      servo1_move(com);
    }
    //Serial.print('a');
    if (receivedChar == 'p') {
      int num1 = readNumberFromSerial(); // 读取第一个值
      int num2 = readNumberFromSerial(); // 读取第二个值
      servo_move(num2); // 控制舵机移动
      stepper_move(num1); // 控制步进电机移动
      delay(100);
      Serial.print('e');
      Serial.print(num1);
      Serial.print(num2);
    }

  }
  if (Ir_Check() == true) {
  Serial.println(Ir_Data);
  switch(Ir_Data){
    case 24: Stepper_Go(GO_FAR,300); break; //电机
    case 74: Stepper_Go(GO_NEAR,300); break; 
    case 56: if (pendown==false){Servo1_Turn(DOWN);}else{Servo1_Turn(UP);}pendown =! pendown;break;
    case 16: Servo_Turn(CW,2); break; //舵机c
    case 90: Servo_Turn(CCW,2); break; 
    }
  }
}

int readNumberFromSerial() {
  char numberChars[10]; // 存储数字字符的数组
  int index = 0;
  delay(10);
  while (Serial.available() > 0) {
    char digit = Serial.read();
    Serial.print('i');
    if (isdigit(digit) || digit == '-') {
      numberChars[index++] = digit;
    } else if (digit == ',') {
      break;
    }
  }
  numberChars[index] = '\0'; // 添加字符串终止符
  //Serial.print('h');
  return atoi(numberChars); // 将字符数组转换为整数
}



void servo_move(int angle) {
  /*if (angle == 0) {
    if (BoardLED == LOW) {
      digitalWrite(13, HIGH);
      BoardLED = HIGH;
    } else {
      digitalWrite(13, LOW);
      BoardLED = LOW;
    }
  }*/
  Serial.print(angle);
  if (angle != 0){
      if (angle > 0){
        Servo_Turn(CW,angle);
      }
      if (angle < 0){
        Servo_Turn(CCW,-angle);
      }
  }
}

void stepper_move(int steps) {
    /*if (steps == 1) {
    if (BoardLED == LOW) {
      digitalWrite(13, HIGH);
      BoardLED = HIGH;
    } else {
      digitalWrite(13, LOW);
      BoardLED = LOW;
  // 控制步进电机移动的逻辑
  // 使用接收到的步数值来控制步进电机的运动
    }
    }*/
    Serial.print(steps);
    if (steps != 0){
      if (steps > 0){
        Stepper_Go(GO_FAR,steps*50);
      }
      if (steps < 0){
        Stepper_Go(GO_NEAR,-steps*50);
      }
    Stepper_Loop();
    }
}

void servo1_move(int com){
  Serial.print(com);
  if (com == 0){
    Servo1_Turn(DOWN);
  }
  else{
    Servo1_Turn(UP);
  }
}

