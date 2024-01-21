//#include "tools.h"
void setup() {
  // 初始化串口通信
  Serial.begin(115200);
}

bool BoardLED = LOW;

void loop() {
  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    if (receivedChar == 'p') {
      int num1 = readNumberFromSerial(); // 读取第一个值
      int num2 = readNumberFromSerial(); // 读取第二个值
      //servo_move(num2); // 控制舵机移动
      stepper_move(num1); // 控制步进电机移动
      delay(10);
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
  if (angle == 0) {
    if (BoardLED == LOW) {
      digitalWrite(13, HIGH);
      BoardLED = HIGH;
    } else {
      digitalWrite(13, LOW);
      BoardLED = LOW;
    }
  }
}

void stepper_move(int steps) {
    if (steps == -1) {
    if (BoardLED == LOW) {
      digitalWrite(13, HIGH);
      BoardLED = HIGH;
    } else {
      digitalWrite(13, LOW);
      BoardLED = LOW;
  // 控制步进电机移动的逻辑
  // 使用接收到的步数值来控制步进电机的运动
}
    }
    }

