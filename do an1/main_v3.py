import cv2
import numpy as np
from picamera2 import Picamera2
import time
import spidev
import RPi.GPIO as GPIO
import imutils

from time import sleep
from imutils.perspective import four_point_transform #cai thien kha nang nhan dien va phan tich hinh anh

in1 = 13
in2 = 12
in3 = 21
in4 = 20
ena = 6
enb = 26

# Setup Output Pins
GPIO.setmode(GPIO.BCM) #so do chan BROADCOM SOC cua Pi
GPIO.setwarnings(False)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(ena, GPIO.OUT)
pA = GPIO.PWM(ena, 250) #tan so 250hz

GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
GPIO.setup(enb, GPIO.OUT)
pB = GPIO.PWM(enb, 250)

pA.start(55)#55%
pB.start(55)
# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)  # Open bus 0, device 0
spi.max_speed_hz = 500000  # Set SPI speed
GPIO.setmode(GPIO.BCM)

piCam = Picamera2()
piCam.preview_configuration.main.size = (480, 240) #thong so pixel
piCam.preview_configuration.main.format = "RGB888" #8bit
piCam.preview_configuration.controls.FrameRate = 60#toc do khung hinh
piCam.preview_configuration.align() #can chinh sao cho phu hop
piCam.configure("preview") #xem truoc
piCam.start()

isStop=False #kiem soat stop camera

def picam(): #luu hinh anh vào frame
    global frame #bien toan cuc frame
    frame = piCam.capture_array() #tra hinh anh ve dang mang numpy


def canny():
    global canny_edge #khai bao bien toan cuc canny_edge
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (11, 11), 0) #dung bo loc blur lam min anh , giam nhieu 
    #(11,11) la thong so mang kernel , muc dich lam min , 0 la gia tri cua ham blur
    thresh_low = 150#gia tri cuong do gradient de xac dinh bien va canh
    thresh_high = 200
    canny_edge = cv2.Canny(blur, thresh_low, thresh_high)


def warpImg():
    global imgWarp, frameFinal #khai bao bien toan cuc
    h, w, c = frame.shape # chieu cao , chieu rong va so kenh mau luu vao bien frane
    pts1 = np.float32(points) 
    pts2 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgWarp = cv2.warpPerspective(canny_edge, matrix, (w, h))
    frameFinal = imgWarp
# thực hiện phép biến đổi phối cảnh (perspective transform) trên một khung hình hoặc một hình ảnh

def nothing(a):
    pass


def initializeTrackbars(intialTracbarVals, wT=480, hT=240):
    cv2.namedWindow("Trackbars")
    cv2.resizeWindow("Trackbars", 360, 240)
    cv2.createTrackbar("Width Top", "Trackbars", intialTracbarVals[0], wT // 2, nothing)
    cv2.createTrackbar("Height Top", "Trackbars", intialTracbarVals[1], hT, nothing)
    cv2.createTrackbar(
        "Width Bottom", "Trackbars", intialTracbarVals[2], wT // 2, nothing
    )
    cv2.createTrackbar("Height Bottom", "Trackbars", intialTracbarVals[3], hT, nothing)


def valTrackbars(wT=480, hT=240):
    global points
    widthTop = cv2.getTrackbarPos("Width Top", "Trackbars")
    heightTop = cv2.getTrackbarPos("Height Top", "Trackbars")
    widthBottom = cv2.getTrackbarPos("Width Bottom", "Trackbars")
    heightBottom = cv2.getTrackbarPos("Height Bottom", "Trackbars")
    points = np.float32(
        [
            (widthTop, heightTop),
            (wT - widthTop, heightTop),
            (widthBottom, heightBottom),
            (wT - widthBottom, heightBottom),
        ]
    )


def drawPoints():
    for x in range(4):
        cv2.circle(
            frame, (int(points[x][0]), int(points[x][1])), 15, (0, 0, 255), cv2.FILLED
        )


def find_left_right_points():
    global left_point, right_point

    im_height, im_width = imgWarp.shape[:2]

    interested_line_y = int(im_height * 0.9)
    cv2.line(
        frame, (0, interested_line_y), (im_width, interested_line_y), (0, 0, 255), 2
    )
    interested_line = imgWarp[interested_line_y, :]

    left_point = -1
    right_point = -1
    lane_width = 400
    center = im_width // 2

    for x in range(center, 0, -1):
        if interested_line[x] > 0:
            left_point = x
            break
    for x in range(center + 1, im_width):
        if interested_line[x] > 0:
            right_point = x
            break

    # Predict right point when only see the left point
    if left_point != -1 and right_point == -1:
        right_point = left_point + lane_width

    # Predict left point when only see the right point
    if right_point != -1 and left_point == -1:
        left_point = right_point - lane_width

    # Draw two points on the image
    if left_point != -1:
        cv2.circle(frame, (left_point, interested_line_y), 10, (255, 255, 0), -1)
    if right_point != -1:
        cv2.circle(frame, (right_point, interested_line_y), 10, (0, 255, 0), -1)


def calculate_control_signal():
    """Calculate speed and steering angle"""
    global center_diff, im_center, center_point
    center_diff = 0
    center_point = 0

    im_center = frame.shape[1] // 2

    if left_point != -1 and right_point != -1:
        center_point = (right_point + left_point) // 2
        center_diff = -(im_center - center_point)
    cv2.putText(
        frame,
        f"Result: {center_diff}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2,
    )

    cv2.line(frameFinal, (center_point, 250), (center_point, 350), (0, 0, 255), 3)

    cv2.line(frameFinal, (im_center, 250), (im_center, 350), (255, 0, 0), 3)


def SPI():
    key = center_diff
    if -30 < key < 30:
        spi.xfer([3])
        pA.ChangeDutyCycle(50)
        pB.ChangeDutyCycle(50)
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        print("TIEN")
        cv2.putText(
            frame, "tien", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4
        )
    elif 30 < key < 500:
        spi.xfer([4])
        pA.ChangeDutyCycle(65)
        pB.ChangeDutyCycle(65)
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        print("PHAI")
        cv2.putText(
            frame, "Phai", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4
        )
    elif -500 < key < -30:
        spi.xfer([2])
        pA.ChangeDutyCycle(65)
        pB.ChangeDutyCycle(65)
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        print("TRAI")
        cv2.putText(
            frame, "Trai", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4
        )


def straight():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)


def turn_right():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(in3, GPIO.HIGH)
    GPIO.output(in4, GPIO.LOW)


def turn_left():
    GPIO.output(in1, GPIO.HIGH)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)


def stop():
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)


def findTrafficSign():
    '''
    This function find blobs with blue color on the image.
    After blobs were found it detects the largest square blob, that must be the sign.
    '''
    global isStop
    # define range HSV for blue color of the traffic sign
    lower_blue = np.array([85, 100, 70])
    upper_blue = np.array([115, 255, 255])
    lower_red = np.array([0, 70, 50])
    upper_red = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    # grab the current frame
    frame = piCam.capture_array()

    frame = imutils.resize(frame, width=500)
    frameArea = frame.shape[0] * frame.shape[1]

    # convert color image to HSV color scheme
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # define kernel for smoothing
    kernel = np.ones((3, 3), np.uint8)
    # extract binary image with active blue regions
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_red1 = cv2.inRange(hsv, lower_red, upper_red)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    # morphological operations
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)

    # find contours in the mask
    cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_red, _ = cv2.findContours(mask_red.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # defite string variable to hold detected sign description
    detectedTrafficSign = None

    # define variables to hold values during loop
    largestArea = 0
    largestRect = None

    # only proceed if at least one contour was found
    if len(cnts) > 0:
        for cnt in cnts:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.intp(box) 

            # count euclidian distance for each side of the rectangle
            sideOne = np.linalg.norm(box[0] - box[1])
            sideTwo = np.linalg.norm(box[0] - box[3])
            # count area of the rectangle
            area = sideOne * sideTwo
            # find the largest rectangle within all contours
            if area > largestArea:
                largestArea = area
                largestRect = box

    # draw contour of the found rectangle on  the original image
    if largestArea > frameArea * 0.02:
        cv2.drawContours(frame, [largestRect], 0, (0, 0, 255), 2)

        # if largestRect is not None:
        # cut and warp interesting area
        warped = four_point_transform(mask, [largestRect][0])

        # use function to detect the sign on the found rectangle
        detectedTrafficSign = identifyTrafficSign(warped)
        print(detectedTrafficSign)

        if detectedTrafficSign == "Stop":
            # Stop
            
            print("Stop_ne")
            isStop=True
            stop()
            
            
        elif detectedTrafficSign == "Move Straight":
            print("Chay thang ne")
            # Stop
            isStop = False
            time.sleep(3.0)
            #straight()
            
            #pA.ChangeDutyCycle(60)
            #pB.ChangeDutyCycle(60)
        else:
            stop()
            print("None")

        # write the description of the sign on the original image
        cv2.putText(frame, detectedTrafficSign, tuple(largestRect[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0),
                    2)

    largestArea = 0
    largestRect = None

    if len(contours_red) > 0:
        for cnt in contours_red:
            area = cv2.contourArea(cnt)
            if area > largestArea:
                largestArea = area
                largestRect = cnt

    if largestArea > frameArea * 0.02:
        approx = cv2.approxPolyDP(largestRect, 0.02 * cv2.arcLength(largestRect, True), True)
        if len(approx) == 6:  # Check for hexagon
            cv2.drawContours(frame, [approx], 0, (0, 0, 255), 2)
            detectedTrafficSign = 'Stop'

            print('Stop1')
            cv2.putText(frame, detectedTrafficSign, tuple(approx[0][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (0, 255, 0), 2)
    # show original image
    cv2.imshow("Original", frame)

    # if the `q` key was pressed, break from the loop
    if cv2.waitKey(1) & 0xFF is ord('q'):
        cv2.destroyAllWindows()
        print("Stop programm and close all windows")


def identifyTrafficSign(image):
    '''
    In this function we select some ROI in which we expect to have the sign parts. If the ROI has more active pixels than threshold we mark it as 1, else 0
    After path through all four regions, we compare the tuple of ones and zeros with keys in dictionary SIGNS_LOOKUP
    '''

    # define the dictionary of signs segments so we can identify
    # each signs on the image
    SIGNS_LOOKUP = {
        (1, 0, 0, 1): 'Turn Right',
        (0, 0, 1, 1): 'Turn Left',
        (0, 1, 0, 1): 'Move Straight',
        (1, 0, 1, 1): 'Turn Back',
        (1, 1, 1, 0): 'Stop'
    }

    THRESHOLD = 150

    image = cv2.bitwise_not(image)
    # (roiH, roiW) = roi.shape
    # subHeight = thresh.shape[0]/10
    # subWidth = thresh.shape[1]/10
    (subHeight, subWidth) = np.divide(image.shape, 20)
    subHeight = int(subHeight)
    subWidth = int(subWidth)

    # mark the ROIs borders on the image
    cv2.rectangle(image, (3 * subWidth, 8 * subHeight), (7 * subWidth, 14 * subHeight), (0, 255, 0), 2)  # left block
    cv2.rectangle(image, (9 * subWidth, 8 * subHeight), (13 * subWidth, 14 * subHeight), (0, 255, 0), 2)  # center block
    cv2.rectangle(image, (15 * subWidth, 8 * subHeight), (19 * subWidth, 14 * subHeight), (0, 255, 0), 2)  # right block
    cv2.rectangle(image, (7 * subWidth, 4 * subHeight), (15 * subWidth, 8 * subHeight), (0, 255, 0), 2)  # top block

    # substract 5 ROI of the sign thresh image
    leftBlock = image[8 * subHeight:14 * subHeight, 3 * subWidth: 7 * subWidth]
    centerBlock = image[8 * subHeight:14 * subHeight, 9 * subWidth:13 * subWidth]
    rightBlock = image[8 * subHeight:14 * subHeight, 15 * subWidth:19 * subWidth]
    topBlock = image[4 * subHeight: 8 * subHeight, 7 * subWidth:15 * subWidth]

    # we now track the fraction of each ROI
    leftFraction = np.sum(leftBlock) / (leftBlock.shape[0] * leftBlock.shape[1])
    centerFraction = np.sum(centerBlock) / (centerBlock.shape[0] * centerBlock.shape[1])
    rightFraction = np.sum(rightBlock) / (rightBlock.shape[0] * rightBlock.shape[1])
    topFraction = np.sum(topBlock) / (topBlock.shape[0] * topBlock.shape[1])

    segments = (leftFraction, centerFraction, rightFraction, topFraction)
    segments = tuple(1 if segment > THRESHOLD else 0 for segment in segments)

    cv2.imshow("Warped", image)

    if segments in SIGNS_LOOKUP:
        return SIGNS_LOOKUP[segments]
    else:
        return None


def main():
    intialTracbarVals = [18, 59, 0, 139]
    initializeTrackbars(intialTracbarVals)
    while True:
        if isStop == False:
            picam()
            valTrackbars()
            drawPoints()
            canny()
            warpImg()
            find_left_right_points()
            calculate_control_signal()
            SPI()
            findTrafficSign()
            print(isStop)
        else:
            print("Else ne")
            findTrafficSign()

        cv2.circle(frame, (center_point, 175), 10, (0, 0, 255), 3)
        cv2.line(frame, (im_center, 150), (im_center, 230), (255, 0, 0), 3)
        cv2.imshow("Original", frame)
        cv2.imshow("Perspective", imgWarp)
        cv2.imshow("Final", frameFinal)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
