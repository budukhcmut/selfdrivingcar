import cv2
import numpy as np
import time
from imutils.perspective import four_point_transform
import imutils
from picamera2 import Picamera2
import RPi.GPIO as GPIO

# GPIO pin setup for motor control
in1 = 13
in2 = 12
in3 = 21
in4 = 20
ena = 6
enb = 26

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(ena, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
GPIO.setup(enb, GPIO.OUT)

# Initialize PWM for motor control
pwm_left = GPIO.PWM(ena, 250)
pwm_right = GPIO.PWM(enb, 250)
pwm_left.start(40)
pwm_right.start(40)

# Initialize Picamera2
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": "RGB888"}))
camera.start()


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
    # define range HSV for blue color of the traffic sign
    lower_blue = np.array([85, 100, 70])
    upper_blue = np.array([115, 255, 255])
    lower_red = np.array([0, 70, 50])
    upper_red = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])



    while True:
        # grab the current frame
        frame = camera.capture_array()

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

            # Control the robot based on the detected sign
            if detectedTrafficSign == "Move Straight":
                # Move straight
                straight()
                time.sleep(2)
            elif detectedTrafficSign == "Turn Left":
                stop()
                time.sleep(1)
                # Turn left
                pwm_left.ChangeDutyCycle(85)
                pwm_right.ChangeDutyCycle(85)
                turn_left()
                time.sleep(1)
                # Move straight
                pwm_left.ChangeDutyCycle(40)
                pwm_right.ChangeDutyCycle(40)
                straight()
                time.sleep(2)
            elif detectedTrafficSign == "Turn Right":
                stop()
                time.sleep(1)
                # Turn right
                pwm_left.ChangeDutyCycle(85)
                pwm_right.ChangeDutyCycle(85)
                turn_right()
                time.sleep(1)
                # Move straight
                pwm_left.ChangeDutyCycle(40)
                pwm_right.ChangeDutyCycle(40)
                straight()
                time.sleep(2)
            elif detectedTrafficSign == "Turn Back":
                # Turn back
                pwm_left.ChangeDutyCycle(80 + 5)
                pwm_right.ChangeDutyCycle(80 + 5)
                GPIO.output(in1, GPIO.LOW)
                GPIO.output(in2, GPIO.HIGH)
                GPIO.output(in3, GPIO.LOW)
                GPIO.output(in4, GPIO.HIGH)
                time.sleep(0.75)
                pwm_left.ChangeDutyCycle(80 + 5)
                pwm_right.ChangeDutyCycle(80 + 5)
                GPIO.output(in1, GPIO.LOW)
                GPIO.output(in2, GPIO.HIGH)
                GPIO.output(in3, GPIO.LOW)
                GPIO.output(in4, GPIO.HIGH)
                time.sleep(0.75)
                # Move straight
                pwm_left.ChangeDutyCycle(80)
                GPIO.output(in1, GPIO.HIGH)
                GPIO.output(in2, GPIO.LOW)
                pwm_right.ChangeDutyCycle(80)
                GPIO.output(in3, GPIO.LOW)
                GPIO.output(in4, GPIO.HIGH)
                time.sleep(2)
            elif detectedTrafficSign == "Stop":
                # Stop
                stop()
            else:
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
            break


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
    findTrafficSign()


if __name__ == '__main__':
    main()
