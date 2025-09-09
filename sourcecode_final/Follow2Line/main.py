from time import sleep
import CarMove
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import cv2
import io
import time
#import ActionClientRead
from ultrasonic import UltraSonic
US=UltraSonic()
m1=CarMove.move()

dat=[0,0,0,0,0]
def driver(D):
    c=0
    #D=ActionClientRead.Tcp_Read()
    print("distance=")
    for b in D:
        dat[c]=b
        c+=1
    left=dat[0]  # number of left lines detected
    right=dat[1] # number of right lines detected
    red=dat[2]   # Indicate whether red Color Marker present (1) or Not (0)

    dis=20#US.Distance() #Get current Distance from US sensor
    print("distance=",dis)
    print("left=",left)
    print("right=",right)
    
    speedR,speedL,setback=0,0,0

    if red or dis<15 : # Stop the car if condition is true 
        #speedR=-1*CarMove.initialvaluespeed
        #speedL=-1*CarMove.initialvaluespeed
        m1.stop()
    elif(left>right): # if left is more ==> move left by stopping the left wheel.
        #speedR=10
        #speedL=-1*CarMove.initialvaluespeed
        m1.Lspeed(speedL)
        #time.sleep(0.1)
    elif(right>left): # if right is more==> move right by stopping the right wheel.
        #speedL=10
        #speedR=-1*CarMove.initialvaluespeed
        m1.Rspeed(speedR)
        #time.sleep(0.1)
    else:
        m1.forward()
        
#     m1.Rspeed(speedR)
#     m1.Lspeed(speedL)
#     m1.forward()

def sendinfoback(l,r,red):
    D=b''
    D+=bytes([l,r,red])
    print('here inside sendinfo',D)
    #send_data_pi.Tcp_Write(D)
    driver(D)
    
def checkforred(image):
    font = cv2.FONT_HERSHEY_SIMPLEX
    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    #Red HSV Range
    low_red=np.array([157,56,0])
    high_red=np.array([179,255,255])
        
    mask=cv2.inRange(hsv,low_red,high_red)
    blur=cv2.GaussianBlur(mask,(15,15),0)
    contours,_=cv2.findContours(blur,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    status=0
    for contour in contours:
        area=cv2.contourArea(contour)
        if area>20000:
            status=1
            cv2.drawContours(image,contour,-1,(0,0,255),3)
            cv2.putText(image,'RED STOP',(240,320), font, 2,(0,0,255),2,cv2.LINE_AA)     
    return (image,status)

def average_slope_intercept(lines,image):
    left_fit=[]
    right_fit=[]
    if lines is not None:
        for line in lines:
            x1,y1,x2,y2=line.reshape(4)
            parameters=np.polyfit((x1,x2),(y1,y2),1)
            slope=parameters[0]
            intercept=parameters[1]
            if slope<0:
                right_fit.append((slope,intercept))
            else:
                left_fit.append((slope,intercept))
                    
    left_fitavg=np.average(left_fit, axis=0)
    right_fitavg=np.average(right_fit, axis=0)
    print("left slope",left_fitavg,"rigt slope",right_fitavg)
    sendinfoback(len(left_fit), len(right_fit),red=0) # Send number of left and right lines detected.
    
def canny1(image):
    gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    blur=cv2.GaussianBlur(gray, (7,7), 0)
    canny=cv2.Canny(blur,50,150)  # lowerThreshold=50 UpperThreshold=150
    return canny

def region_of_interest(image):
    height=image.shape[0]
    width=image.shape[1]
    region=np.array([[(100,height),(width-100,height),(width-100,height-120),(100,height-120)]])
    mask=np.zeros_like(image)
    cv2.fillPoly(mask,region, 255)
    return mask
    
def display_lines(lines,image):
    line_image=np.zeros_like(image)
    if lines is not None:
        for line in lines:
            if len(line)>0:                    
                x1,y1,x2,y2=line.reshape(4)
                cv2.line(line_image,(x1,y1),(x2,y2),[0,255,0],10)
    return line_image

camera = PiCamera()

image_width = 640
image_height = 480
camera.resolution = (image_width, image_height)
camera.framerate = 15
rawCapture = PiRGBArray(camera, size=(image_width, image_height))

stream = io.BytesIO()
for foo in camera.capture_continuous(stream, 'jpeg', use_video_port = True):
     # return current frame
    stream.seek(0)
    _stream = stream.getvalue()
    data = np.fromstring(_stream, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    #yield img

    # reset stream for next frame
    stream.seek(0)
    stream.truncate()
    
    #image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

    lane_image=np.copy(image)
    lane_image,red=checkforred(lane_image)
    if red:
        sendinfoback(0,0,1)
    else:
        canny=canny1(lane_image)
        roi=region_of_interest(canny)
        lane=cv2.bitwise_and(canny,roi)
        lines=cv2.HoughLinesP(lane,1,np.pi/180,30,np.array([]),minLineLength=20,maxLineGap=5)                    
        average_slope_intercept(lines,lane_image) 
        line_image=display_lines(lines,lane_image)                    
        lane_image=cv2.addWeighted(lane_image,1,line_image,1,0)

        cv2.imshow('canny',canny)
        cv2.imshow('roi',roi)
        cv2.imshow('lane',lane)
        cv2.imshow('line',line_image)
        cv2.imshow('frame',lane_image) #display image    
        key=cv2.waitKey(1) & 0xFF
#         if  key == ord('q'):
#             send_data_pi.Tcp_Close()
#             break        