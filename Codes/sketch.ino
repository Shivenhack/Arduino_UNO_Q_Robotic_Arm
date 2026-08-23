

/*orignal code
  ARDUINO UNO Q - SKETCH SIDE (MCU / STM32U585)
  App Lab folder: sketch/sketch.ino

  Servo control remains here. This exposes the "pick_and_place"
  function through Bridge so that it can be called from the
  Python side (python/main.py) running on the same board.

  colorCode:
    1 -> RED   -> pick from center, place LEFT
    2 -> BLUE  -> pick from center, place RIGHT
*/

#include <Servo.h>
#include <Arduino_RouterBridge.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo gripper;

int basePos = 90;
int shoulderPos = 90;
int elbowPos = 90;
int gripperPos = 90;

const int MOVE_DELAY = 5;

volatile bool armBusy = false;

//------------------------------------------------
void smoothMove(Servo &servo, int &currentPos, int targetPos)
{
  if (currentPos < targetPos)
  {
    for (int pos = currentPos; pos <= targetPos; pos++)
    {
      servo.write(pos);
      delay(MOVE_DELAY);
    }
  }
  else
  {
    for (int pos = currentPos; pos >= targetPos; pos--)
    {
      servo.write(pos);
      delay(MOVE_DELAY);
    }
  }
  currentPos = targetPos;
  delay(200);
}

//------------------------------------------------
void pickObject()
{
  smoothMove(gripper, gripperPos, 180);
  delay(300);
  smoothMove(elbow, elbowPos, 120);
  smoothMove(shoulder, shoulderPos, 60);
  smoothMove(gripper, gripperPos, 90);
  delay(500);
  smoothMove(shoulder, shoulderPos, 90);
  smoothMove(elbow, elbowPos, 90);
}

//------------------------------------------------
void placeLeft()
{
  smoothMove(base, basePos, 140);
  delay(300);
  smoothMove(elbow, elbowPos, 120);
  smoothMove(shoulder, shoulderPos, 60);
  smoothMove(gripper, gripperPos, 180);
  delay(500);
  smoothMove(shoulder, shoulderPos, 90);
  smoothMove(elbow, elbowPos, 90);
  smoothMove(base, basePos, 90);
  base.write(90);
}

//------------------------------------------------
void placeRight()
{
  smoothMove(base, basePos, 40);
  delay(300);
  smoothMove(elbow, elbowPos, 120);
  smoothMove(shoulder, shoulderPos, 60);
  smoothMove(gripper, gripperPos, 180);
  delay(500);
  smoothMove(shoulder, shoulderPos, 90);
  smoothMove(elbow, elbowPos, 90);
  smoothMove(base, basePos, 90);
  base.write(90);
}

//------------------------------------------------
// RPC FUNCTION - called from Python (python/main.py) via Bridge.call()
//------------------------------------------------
int pick_and_place(int colorCode)
{
  Serial.print("RPC RECEIVED, colorCode = ");
  Serial.println(colorCode);   // Visible only when USB-C is connected

  if (armBusy)
  {
    Serial.println("ARM BUSY - ignoring request");
    return -1;
  }

  if (colorCode != 1 && colorCode != 2)
  {
    Serial.println("INVALID colorCode - ignoring request");
    return -2;
  }

  armBusy = true;

  if (colorCode == 1)
  {
    Serial.println("Executing RED pick & place...");
    pickObject();
    placeLeft();
  }
  else if (colorCode == 2)
  {
    Serial.println("Executing BLUE pick & place...");
    pickObject();
    placeRight();
  }

  armBusy = false;
  Serial.println("DONE");
  return 1;
}

//------------------------------------------------
void setup()
{
  Serial.begin(9600);
  base.attach(3);
  shoulder.attach(5);
  elbow.attach(6);
  gripper.attach(9);

  base.write(90);
  shoulder.write(90);
  elbow.write(90);
  gripper.write(90);

  delay(1000);

  Bridge.begin();
  Bridge.provide("pick_and_place", pick_and_place);
}

void loop()
{
}