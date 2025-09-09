import RPi.GPIO as GPIO          
from time import sleep

in1 = 13
in2 = 12
in3 = 21
in4 = 20
en1 = 6
en2 = 26
temp1=1

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)
GPIO.setup(in3,GPIO.OUT)
GPIO.setup(in4,GPIO.OUT)
GPIO.setup(en1,GPIO.OUT)
GPIO.setup(en2,GPIO.OUT)
GPIO.output(in1,GPIO.LOW)
GPIO.output(in2,GPIO.LOW)
GPIO.output(in3,GPIO.LOW)
GPIO.output(in4,GPIO.LOW)
p=GPIO.PWM(en1,1000)
q=GPIO.PWM(en2,1000)

p.start(75)
q.start(75)
print("\n")
print("The default speed & direction of motor is LOW & Forward.....")
print("r-run x-stop w-forward s-backward a-left d-right m-medium e-exit f-front")
print("\n")    

while(1):

    x=input()
    
    if x=='r':
        print("run")
        if(temp1==1):
         GPIO.output(in1,GPIO.LOW)
         GPIO.output(in2,GPIO.HIGH)
         GPIO.output(in3,GPIO.HIGH)
         GPIO.output(in4,GPIO.LOW)
         
         print("forward")
         x='z'
        else:
         GPIO.output(in1,GPIO.HIGH)
         GPIO.output(in2,GPIO.LOW)
         GPIO.output(in3,GPIO.LOW)
         GPIO.output(in4,GPIO.HIGH)
         
         print("backward")
         x='z'


    elif x=='x':
        print("stop")
        GPIO.output(in1,GPIO.LOW)
        GPIO.output(in2,GPIO.LOW)
        GPIO.output(in3,GPIO.LOW)
        GPIO.output(in4,GPIO.LOW)
        
        x='z'

    elif x=='w':
        print("forward")
        GPIO.output(in1,GPIO.LOW)
        GPIO.output(in2,GPIO.HIGH)
        GPIO.output(in3,GPIO.HIGH)
        GPIO.output(in4,GPIO.LOW)
        temp1=1
        x='z'

    elif x=='s':
        print("backward")
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        GPIO.output(in3,GPIO.LOW)
        GPIO.output(in4,GPIO.HIGH)
        temp1=0
        x='z'
    
    elif x=='d':
        print("right")
        GPIO.output(in1,GPIO.LOW)
        GPIO.output(in2,GPIO.LOW)
        GPIO.output(in3,GPIO.LOW)
        GPIO.output(in4,GPIO.HIGH)
        temp1=1
        x='z'
     
    elif x=='a':
        print("left")
        GPIO.output(in1,GPIO.HIGH)
        GPIO.output(in2,GPIO.LOW)
        GPIO.output(in3,GPIO.LOW)
        GPIO.output(in4,GPIO.LOW)
        temp1=0
        x='z'
          
    else:
        print("<<<  wrong data  >>>")
        print("please enter the defined data to continue.....")