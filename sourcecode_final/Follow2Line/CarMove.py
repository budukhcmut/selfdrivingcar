import RPi.GPIO as GPIO
#import RPi.GPIO as gpiozero

from time import sleep

#import more


#Connections from Motor Driver to Pi GPIO
# Rin1 = 21
# Rin2 = 20
# Ren = 12 # Right Enable
# Lin1 = 13
# Lin2 = 19
# Len = 26 #left Enable

Rin1 = 13
Rin2 = 12
Ren = 6 # Right Enable
Lin1 = 21
Lin2 = 20
Len = 26 #left Enable

in1 = 13
in2 = 12
in3 = 21
in4 = 20
en1 = 6
en2 = 26

initialvaluespeed=18 # This should be between 0 to 100
speed_turn = 40

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#Initialization for right motor
GPIO.setup(Rin1,GPIO.OUT)
GPIO.setup(Rin2,GPIO.OUT)
GPIO.setup(Ren,GPIO.OUT)
GPIO.output(Rin1,GPIO.LOW)
GPIO.output(Rin2,GPIO.LOW)
Rp=GPIO.PWM(Ren,1000)
Rp.start(initialvaluespeed)
#Initialization for left motor
GPIO.setup(Lin1,GPIO.OUT)
GPIO.setup(Lin2,GPIO.OUT)
GPIO.setup(Len,GPIO.OUT)
GPIO.output(Lin1,GPIO.LOW)
GPIO.output(Lin2,GPIO.LOW)
Lp=GPIO.PWM(Len,1000)
Lp.start(initialvaluespeed)

def changeSpeed():
    Rp.start(speed_turn)
    Lp.start(speed_turn)
    
def setSpeedDefault():
    Rp.start(initialvaluespeed)
    Lp.start(initialvaluespeed)

def forward1():
    setSpeedDefault()
    GPIO.output(in1,GPIO.LOW)
    GPIO.output(in2,GPIO.HIGH)
    GPIO.output(in3,GPIO.HIGH)
    GPIO.output(in4,GPIO.LOW)
    
    
def turning_right():
    changeSpeed()
    GPIO.output(in1,GPIO.LOW)
    GPIO.output(in2,GPIO.LOW)
    GPIO.output(in3,GPIO.LOW)
    GPIO.output(in4,GPIO.HIGH)
    
def turning_left():
    changeSpeed()
    GPIO.output(in1,GPIO.HIGH)
    GPIO.output(in2,GPIO.LOW)
    GPIO.output(in3,GPIO.LOW)
    GPIO.output(in4,GPIO.LOW)
    
def stop1():
    GPIO.output(in1,GPIO.LOW)
    GPIO.output(in2,GPIO.LOW)
    GPIO.output(in3,GPIO.LOW)
    GPIO.output(in4,GPIO.LOW)

class move():
    def __init__(self):
        print("starting")
        
    def Rspeed(self,val):
        #Rp.ChangeDutyCycle(initialvaluespeed+val)
        turning_right()
 
    def Lspeed(self,val):
        #Lp.ChangeDutyCycle(initialvaluespeed+val)
        turning_left()

    def forward(self):
        forward1()
#         GPIO.output(Rin2,GPIO.LOW)
#         GPIO.output(Rin1,GPIO.HIGH)
#         GPIO.output(Lin1,GPIO.LOW)
#         GPIO.output(Lin2,GPIO.HIGH)
    def stop(self):
         stop1()   
    
    def escape():
        GPIO.cleanup()
