typedef unsigned char  BYTE;                    // ..
typedef unsigned short  WORD;                   // ..
typedef unsigned long   DWORD;                  // ..

#define PIN_IR       2                          // Remoter
#define PIN_LED      4                          // LED
#define PIN_SERVO    6                         // servo
#define PIN_SERVO1  7
#define PIN_STEPPER1 9                          // stepper1
#define PIN_STEPPER2 10                         //        2
#define PIN_STEPPER3 11                         //        3
#define PIN_STEPPER4 12                         //        4

#define TIMER_PERIOD  25                          // 25us
#define TIMER_LOAD    (65536-16*TIMER_PERIOD)     // 65536 - 16M/1*25/M

// servo motor  ==============================================================
#define SERVO_PERIOD (20000/TIMER_PERIOD)         // 20ms --> 800
#define SERVO_MAX    (2500/TIMER_PERIOD)          // 2ms (2.5ms --> 100)
#define SERVO_MIN    ( 500/TIMER_PERIOD)          // 1ms (500us --> 20)
#define SERVO_GRIDS  50                           // 10               
#define SERVO_STEP   ((SERVO_MAX-SERVO_MIN)/SERVO_GRIDS) // 4
#define CW           1
#define CCW          0
BYTE Servo_Angle = (SERVO_MIN+SERVO_MAX)/2;//SERVO_MIN + 5*SERVO_STEP;      // 初始位置
WORD Servo_Counter = 0;                           // 
BYTE Servo_Flag = 0;
WORD ServoMotionCountDown = 0;

// servo motor 1 ==============================================================
#define SERVO1_PERIOD (20000/TIMER_PERIOD)         // 20ms --> 800
#define SERVO1_MAX    (2500/TIMER_PERIOD)          // 2ms (2.5ms --> 100)
#define SERVO1_MIN    ( 500/TIMER_PERIOD)          // 1ms (500us --> 20)
#define SERVO1_GRIDS  10                           // 10               
#define SERVO1_STEP   ((SERVO1_MAX-SERVO1_MIN)/SERVO1_GRIDS) // 4
#define UP           1
#define DOWN          0
BYTE Servo1_Angle = SERVO1_MIN + 1*SERVO1_STEP;      // 
WORD Servo1_Counter = 0;                           // 
BYTE Servo1_Flag = 0;
WORD Servo1MotionCountDown = 0;

// stepper motor ===========================================================
#define STEPPER_INTERVAL   (800/TIMER_PERIOD)    // action takes more than 1.5ms
#define GO_NEAR       0
#define GO_FAR        1
WORD Stepper_CounterDown = 0;                     // 
WORD Stepper_StepsToGo = 0;                       // 
int Stepper_Direction = true;                     // 
int Radius_Position = 0;                         // 
BYTE Stepper_Phase = 0;                           // 
BYTE Stepper_Flag = 0;

// Ir Remote ===============================================================
#define TL_U_TIMEOUT  (15000/TIMER_PERIOD)      // Time out limit 15ms
#define TL_L_9ms      ( 5000/TIMER_PERIOD)      // 9ms low bound: 5ms
#define TL_U_9ms      (15000/TIMER_PERIOD)      // 9ms up bound: 15ms
#define TL_L_4ms5     ( 2200/TIMER_PERIOD)      // 4.5ms low bound: 2.2ms
#define TL_U_4ms5     ( 7500/TIMER_PERIOD)      // 4.5ms up bound: 7.5ms
#define TL_L_BIT      (  300/TIMER_PERIOD)      // 1bit low bound: 300us
#define TL_M_BIT      (  800/TIMER_PERIOD)      // 0/1 threshold: 800us
#define TL_U_BIT      ( 3200/TIMER_PERIOD)      // 1bit up bound: 3.2ms
int  Ir_CurLevel = LOW;                         // Current level 
int  Ir_LastLevel = LOW;                        // Saved level
WORD Ir_TickLog = 0;                            // Last Time the Pin Changed
WORD Ir_Interval = 0;                           // The time interval 
BYTE Ir_Stage = 0;                              //
BYTE Ir_BitPos = 0;                             //
BYTE Ir_BitIsHigh = false;                      //
BYTE Ir_Data = 0;                           //

// =============================================================================
volatile WORD Global_Tick = 0;                  //
volatile BYTE Global_1usFlag = 0;               // 1us reached

// =============================================================================
#define TYPE_FAR      1
#define TYPE_FAR_CW   2
#define TYPE_FAR_CCW  3
#define TYPE_NEAR     4
#define TYPE_NEAR_CW  5
#define TYPE_NEAR_CCW 6
#define TYPE_CW       7
#define TYPE_CCW      8

BYTE QueueAngle [256];
BYTE QueueRadius [256];
BYTE QueueLight [256];
BYTE QueueHead = 0;
BYTE QueueTail = 0;
int AngleMoveDone = true;
int RadiusMoveDone = true;

void Queue(BYTE angle, WORD radius, BYTE light)  // 添加队列，不查溢出
{
  QueueHead ++;   // auto loopback
  QueueAngle[QueueHead] = angle;                      // 20~100
  QueueRadius[QueueHead] = radius;
  QueueLight[QueueHead] = light;
}

void Queue_Clear()  // 清除队列
{
  QueueTail = QueueHead;    //
  //Stepper_Stop();    
}

BYTE TempByte;
int TempWord;

void Queue_Loop()   // 
{
  if ((AngleMoveDone == false) || (RadiusMoveDone ==  false)) return;
  if (QueueTail == QueueHead) return;

  QueueTail ++;   // auto loopback

//  Serial.print(QueueTail);
//  Serial.print(" : ");
//  Serial.print(QueueAngle[QueueTail]);
//  Serial.print(":");
//  Serial.print(QueueRadius[QueueTail]);
//  Serial.print(":");
//  Serial.println(QueueLight[QueueTail]);

  TempByte = ((float)QueueAngle[QueueTail]) / 9 * 4 + SERVO_MIN;
  if (TempByte != Servo_Angle)
  {
    ServoMotionCountDown = abs(TempByte - Servo_Angle) * 400;    // 200ms / 25us for 90degree
    Servo_Angle = TempByte;
    AngleMoveDone = false;    
  }
  TempByte = ((float)QueueAngle[QueueTail]) / 9 * 4 + SERVO1_MIN;
  if (TempByte != Servo1_Angle)
  {
    Servo1MotionCountDown = abs(TempByte - Servo1_Angle) * 400;    // 200ms / 25us for 90degree
    Servo1_Angle = TempByte;
    AngleMoveDone = false;    
  }

  if (QueueLight[QueueTail] == true) digitalWrite(PIN_LED,LOW);
  else                               digitalWrite(PIN_LED,HIGH);

  TempWord = QueueRadius[QueueTail];
  TempWord = TempWord * 20;           // 0
  if (TempWord != Radius_Position)
  {
    if (TempWord < Radius_Position)
    {
      Stepper_Direction = true;
      Stepper_StepsToGo = (Radius_Position - TempWord);
      Serial.println(Radius_Position);      
      Serial.print(":N:");
      Serial.println( Radius_Position - TempWord);      
    }
    else
    {
      Stepper_Direction = false;
      Stepper_StepsToGo = TempWord - Radius_Position;
      Serial.print(Radius_Position);      
      Serial.print(":F:");
      Serial.println( TempWord - Radius_Position);      
    }
    Stepper_CounterDown = STEPPER_INTERVAL;  // reset
    RadiusMoveDone = false;  
  }

}

// =============================================================================
void Servo_Setup()                              // 
{
  pinMode(PIN_SERVO, OUTPUT);
  Servo_Counter = 0;
  digitalWrite(PIN_SERVO, HIGH);   
}

void Servo_Loop()
{
  if (Servo_Flag == 0) return;
  Servo_Flag = 0;

  if (ServoMotionCountDown != 0) ServoMotionCountDown --;
  else AngleMoveDone = true;
  
  if (Servo_Counter < SERVO_PERIOD) Servo_Counter ++;
  else Servo_Counter = 0;
      
  if (Servo_Counter == 0) 
    digitalWrite(PIN_SERVO, HIGH);              // level go high
  else 
    if (Servo_Counter == Servo_Angle) 
      digitalWrite(PIN_SERVO, LOW);              // level go low
}

void Servo_Turn(int dir, int angle)
{
  if (dir == CW)
  {
    if (Servo_Angle >= SERVO_MIN + angle) Servo_Angle = Servo_Angle - angle;
  }
  else
  {
    if (Servo_Angle + angle < SERVO_MAX) Servo_Angle = Servo_Angle + angle;
  }
}



// =============================================================================
void Servo1_Setup()                              // 
{
  pinMode(PIN_SERVO1, OUTPUT);
  Servo1_Counter = 0;
  digitalWrite(PIN_SERVO1, HIGH);   
}

void Servo1_Loop()
{
  if (Servo1_Flag == 0) return;
  Servo1_Flag = 0;

  if (Servo1MotionCountDown != 0) Servo1MotionCountDown --;
  else AngleMoveDone = true;
  
  if (Servo1_Counter < SERVO1_PERIOD) Servo1_Counter ++;
  else Servo1_Counter = 0;
      
  if (Servo1_Counter == 0) 
    digitalWrite(PIN_SERVO1, HIGH);              // level go high
  else 
    if (Servo1_Counter == Servo1_Angle) 
      digitalWrite(PIN_SERVO1, LOW);              // level go low
}

void Servo1_Turn(int dir)
{
  if (dir == DOWN) Servo1_Angle = SERVO1_MAX-SERVO1_STEP; 

  else
  {
    Servo1_Angle = SERVO1_MIN+SERVO1_STEP;
  }
}



// =============================================================================

void Ir_Setup()                                  // 
{
  pinMode(PIN_IR, INPUT);
}

int Ir_Check()                                     //
{
  Ir_CurLevel = digitalRead(PIN_IR);                      // Wait for change       
  if (Ir_CurLevel == Ir_LastLevel) return false;          // 
  Ir_LastLevel = Ir_CurLevel;                             // 

  if (Global_Tick < Ir_TickLog)                           // GlobalTick will loop round in 655ms
    Ir_Interval = 0xFFFF - (Ir_TickLog - Global_Tick);    //
  else                                                    //
    Ir_Interval = Global_Tick - Ir_TickLog;               //
  Ir_TickLog = Global_Tick;                               //
  
  if ((Ir_CurLevel == LOW) && (Ir_Interval > TL_U_TIMEOUT))  Ir_Stage = 0; // Time Out Reset

  switch(Ir_Stage)                                        // React According to Stage
  {
    case 0:
      if (Ir_CurLevel == LOW)                              // low level: initialize data
      {
        Ir_Stage = 1;
        Ir_Data = 0;
        Ir_BitIsHigh = false;
        Ir_BitPos = 0;
      }
    break;

    case 1:                                               // Low Level should be around 9ms
      if ((Ir_CurLevel == HIGH) && (Ir_Interval > TL_L_9ms) && (Ir_Interval < TL_U_9ms))  Ir_Stage = 2;
      else Ir_Stage = 0;
    break;

    case 2:                                               // High Level should be around 4.5ms
      if ((Ir_CurLevel == LOW) && (Ir_Interval > TL_L_4ms5) && (Ir_Interval < TL_U_4ms5)) Ir_Stage = 3;
      else Ir_Stage = 0;
    break;

    case 3:                                               // Data Bits
      if (Ir_BitIsHigh == false)                          // 0.56ms 
        Ir_BitIsHigh = true;    
      else
      {
        Ir_BitIsHigh = false;                             // new
        if ((Ir_Interval > TL_L_BIT) && (Ir_Interval < TL_U_BIT))    // 0.56ms --> 0; 1.68ms --> 1
        {
          Ir_BitPos ++;
          
          if ((Ir_BitPos > 16) && (Ir_BitPos < 25))
          {
            Ir_Data = (Ir_Data << 1);
            
            if (Ir_Interval > TL_M_BIT)
              Ir_Data = (Ir_Data | 0x01);         // default is 0, longer is 1
          } 
          else if (Ir_BitPos >= 32)                       // Finished 
          {
            Ir_Stage = 0;
            return true;
          }
        }
        else
          Ir_Stage = 0;                                   // abnormal length
      }
      
    break;
  }
  return false;
}

// =============================================================================
void Stepper_Setup()
{
  pinMode(PIN_STEPPER1,OUTPUT); 
  pinMode(PIN_STEPPER2,OUTPUT); 
  pinMode(PIN_STEPPER3,OUTPUT); 
  pinMode(PIN_STEPPER4,OUTPUT); 
  digitalWrite(PIN_STEPPER1,LOW);
  digitalWrite(PIN_STEPPER2,LOW);
  digitalWrite(PIN_STEPPER3,LOW);
  digitalWrite(PIN_STEPPER4,LOW);
}

void Stepper_Loop()
{
  if (Stepper_Flag == 0) return;
  Stepper_Flag = 0;

  if (Stepper_StepsToGo == 0) 
  {
    if (RadiusMoveDone == false)
    {
      RadiusMoveDone = true; 
      digitalWrite(PIN_STEPPER1,LOW);
      digitalWrite(PIN_STEPPER2,LOW);
      digitalWrite(PIN_STEPPER3,LOW);
      digitalWrite(PIN_STEPPER4,LOW);
    }
    return;
  }
 
  Stepper_CounterDown --;
  if (Stepper_CounterDown > 0) return;

  //Serial.print('.');

  Stepper_StepsToGo --;
  Stepper_CounterDown = STEPPER_INTERVAL;

  if (Stepper_Direction == true)
  {
    Stepper_Phase = (Stepper_Phase + 1) % 8;  //
    Radius_Position = Radius_Position - 1;
  }
  else
  {
    Stepper_Phase = (Stepper_Phase + 7) % 8;  //
    Radius_Position = Radius_Position + 1;
  }

  switch (Stepper_Phase)
    {
        case 0:
            digitalWrite(PIN_STEPPER1, HIGH);
            digitalWrite(PIN_STEPPER2, LOW);
            digitalWrite(PIN_STEPPER3, LOW);
            digitalWrite(PIN_STEPPER4, LOW);
            break;
        case 1:
            digitalWrite(PIN_STEPPER1, HIGH);
            digitalWrite(PIN_STEPPER2, HIGH);
            digitalWrite(PIN_STEPPER3, LOW);
            digitalWrite(PIN_STEPPER4, LOW);
            break;
        case 2:
            digitalWrite(PIN_STEPPER1, LOW);
            digitalWrite(PIN_STEPPER2, HIGH);
            digitalWrite(PIN_STEPPER3, LOW);
            digitalWrite(PIN_STEPPER4, LOW);
            break;
        case 3:
            digitalWrite(PIN_STEPPER1, LOW);
            digitalWrite(PIN_STEPPER2, HIGH);
            digitalWrite(PIN_STEPPER3, HIGH);
            digitalWrite(PIN_STEPPER4, LOW);
            break;
        case 4:
            digitalWrite(PIN_STEPPER1, LOW);
            digitalWrite(PIN_STEPPER2, LOW);
            digitalWrite(PIN_STEPPER3, HIGH);
            digitalWrite(PIN_STEPPER4, LOW);
            break;
        case 5:
            digitalWrite(PIN_STEPPER1, LOW);
            digitalWrite(PIN_STEPPER2, LOW);
            digitalWrite(PIN_STEPPER3, HIGH);
            digitalWrite(PIN_STEPPER4, HIGH);
            break;
        case 6:
            digitalWrite(PIN_STEPPER1, LOW);
            digitalWrite(PIN_STEPPER2, LOW);
            digitalWrite(PIN_STEPPER3, LOW);
            digitalWrite(PIN_STEPPER4, HIGH);
            break;
        case 7:
            digitalWrite(PIN_STEPPER1, HIGH);
            digitalWrite(PIN_STEPPER2, LOW);
            digitalWrite(PIN_STEPPER3, LOW);
            digitalWrite(PIN_STEPPER4, HIGH);
            break;
    }
}

void Stepper_Go(int dir, int distance)
{
  if (dir == GO_NEAR) Stepper_Direction = true;
  else Stepper_Direction = false;
  Stepper_StepsToGo = distance;
  Stepper_CounterDown = STEPPER_INTERVAL;
}

void Stepper_Stop()
{
  Stepper_StepsToGo = 0;
  Stepper_CounterDown = 0;
}

// =============================================================================
ISR(TIMER1_OVF_vect)                    // timer handle
{
  Global_Tick ++;
  Global_1usFlag = 1;                       
  TCNT1 = TIMER_LOAD;
}

void Timer_Setup()                      // set to 100us
{
  noInterrupts();
  TCCR1A = 0x00;                        
  TCCR1B = 0x01;                  
  TCNT1 = TIMER_LOAD;   
  TIMSK1 |= (1 << TOIE1); 
  interrupts();
}

void Timer_Loop()
{
  if (Global_1usFlag == 0) return;
  Global_1usFlag = 0;
  Stepper_Flag = 1;
  Servo_Flag = 1;
  Servo1_Flag = 1;
}

// =============================================================================
 
