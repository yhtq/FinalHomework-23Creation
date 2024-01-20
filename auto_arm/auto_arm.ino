#include "tools.h"
#include<Servo.h>
void setup(){
Serial.begin(115200);
Timer_Setup();
Ir_Setup();
Stepper_Setup(); 
Servo_Setup(); 
Servo1_Setup();
}

bool pendown = false;
char Buffer[20];
char fengefu[] = ",";
int Len = 0;
float stepper_move;
float servo_move;
int pen;


void loop(){
  Timer_Loop();
  Stepper_Loop();
  Servo_Loop();
  Servo1_Loop();
  while (Serial.available()) 
  {   
    Buffer[Len] = Serial.read();   
    if ((Buffer[Len] == 'p') || (Len >= 18))
    {
      Buffer[Len] = 0;
      //Serial.println(Buffer);
      
      Len = 0;
    }
    else
        Len ++;
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



if (Ir_Check() == true) {
  Serial.println(Ir_Data);
switch(Ir_Data){
case 24: Stepper_Go(GO_FAR,100); break; //电机
case 74: Stepper_Go(GO_NEAR,300); break; 
case 56: if (pendown==true){Servo1_Turn(DOWN);}else{Servo1_Turn(UP);}pendown =! pendown;break;
case 16: Servo_Turn(CW,1); break; //舵机
case 90: Servo_Turn(CCW,1); break; 
}
}
}
