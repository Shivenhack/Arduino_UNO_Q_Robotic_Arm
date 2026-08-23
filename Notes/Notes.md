# Project Notes – Robotic Arm Waste Segregator

## Motivation
As a 7th grader, I wanted to challenge myself by building a prototype that combines robotics and computer vision. This is one of my first projects at such a complex level.

## Challenges
- Servo calibration was tricky, and the arm sometimes moved jerkily.
- Color detection failed in low light or when multiple objects appeared.
- WiFi communication between PC and Arduino had small delays.

## Solutions
- Added an armBusy flag and cooldown timer to prevent double sorting.
- Tuned HSV ranges for red and blue detection.
- Adjusted servo angles for smoother motion.

## Learnings
- Learned basics of OpenCV and HSV thresholding.
- Understood how servos are controlled by Arduino UNO Q.
- Gained experience in debugging both hardware and software.

## Future Improvements
- Add onboard camera to remove PC dependency.
- Upgrade detection to AI-based material recognition.
- Improve mechanical design for smoother and faster sorting.
