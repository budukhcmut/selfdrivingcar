import numpy as np
import cv2
import RPi.GPIO as GPIO
video_capture = cv2.VideoCapture(-1)
video_capture.set(3, 160)
video_capture.set(4, 120)
from ultrasonic import UltraSonic
US=UltraSonic()
# Thiết lập chân cấm

in1 = 13
in2 = 12
in3 = 21
in4 = 20
en1 = 6
en2 = 26

initialvaluespeed=30 # This should be between 0 to 100
speed_turn = 60
speed = 100


GPIO.setmode(GPIO.BCM)
GPIO.setup(en1, GPIO.OUT)
GPIO.setup(en2, GPIO.OUT)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
p1 = GPIO.PWM(en1, 100)
p2 = GPIO.PWM(en2, 100)
# Thiết lập tốc độ(nguồn cung)
# p1.start(15)
# p2.start(15)
p1.start(initialvaluespeed)
p2.start(initialvaluespeed)
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)

def changeSpeed():
    p1.start(speed_turn)
    p2.start(speed_turn)

def changeSpeedTurn():
    p1.start(speed)
    p2.start(speed)

def setSpeedDefault():
    p1.start(initialvaluespeed)
    p2.start(initialvaluespeed)

while(True):
    # Chụp khung hình
    ret, frame = video_capture.read()
    # Cắt hình ảnh nửa dưới
    crop_img = frame[60:120, 0:160]
    # Chuyển sang thang độ xám
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    # Gaussian mờ
    blur = cv2.GaussianBlur(gray,(5,5),0)
    # Ngưỡng màu
    ret,thresh1 = cv2.threshold(blur,25,255,cv2.THRESH_BINARY_INV)
    # Erode và giãn ra để loại bỏ các phát hiện đường ngẫu nhiên
    mask = cv2.erode(thresh1, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    # Tìm đường viền của khung
    contours,hierarchy = cv2.findContours(mask.copy(), 1, cv2.CHAIN_APPROX_NONE)
    #Tìm đường bao lớn nhất
    dis = US.Distance()
    if len(contours) > 0 :
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        cv2.line(crop_img,(cx,0),(cx,720),(255,0,0),1)
        cv2.line(crop_img,(0,cy),(1280,cy),(255,0,0),1)
        cv2.drawContours(crop_img, contours, -1, (0,255,0), 1)
        print (cx)
        print (cy)
        if cx >= 120:
            print("Turn Right")
            changeSpeed()

            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)
            GPIO.output(in3, GPIO.LOW)
            GPIO.output(in4, GPIO.HIGH)
        if cx < 120 and cx > 50:
            print("On Track!")
            setSpeedDefault()
            GPIO.output(in1,GPIO.LOW)
            GPIO.output(in2,GPIO.HIGH)
            GPIO.output(in3,GPIO.HIGH)
            GPIO.output(in4,GPIO.LOW)
        if cx <= 50:
            print("Turn Left")
            changeSpeed()
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
            GPIO.output(in3, GPIO.LOW)
            GPIO.output(in4, GPIO.LOW)
    else:
        print("Don't see the line")
        changeSpeedTurn()
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
    #Hiển thị hình ảnh kết quả của camera
    cv2.imshow('frame',crop_img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
        break