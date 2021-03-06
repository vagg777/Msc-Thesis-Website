import os
import urllib
import cv2
from flask import *
import MySQLdb
from time import gmtime, strftime
import numpy as np
import time
from EnglishLanguage import *
from GreekLanguage import *
import ctypes
from PIL import Image

face_cascade = cv2.CascadeClassifier("static/haarcascade/haarcascade_frontalface_default.xml")
mydb = MySQLdb.connect(db="criminal_detection", host="localhost", user="root", passwd="", charset='utf8')
camera_feed_1_location = "Floor 0 - Camera 1"
camera_feed_2_location = "Floor 0 - Camera 2"
last_known_location = ""
iterations = 0
total = 0
sourceURL = ""
query_input = ""


# Image Filters
def apply_invert(image):
    return cv2.bitwise_not(image)

def verify_alpha_channel(image):
    try:
        image.shape[3]
    except IndexError:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    return image

def apply_sepia(image, intensity=0.5):
    image = verify_alpha_channel(image)
    image_h, image_w, image_c = image.shape
    blue = 20
    green = 66
    red = 112
    sepia_bgra = (blue, green, red, 1)
    overlay = np.full((image_h, image_w, 4), sepia_bgra, dtype='uint8')
    cv2.addWeighted(overlay, intensity, image, 1.0, 0, image)
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image

def apply_color_overlay(image, intensity=0.5, blue=0, green=0, red=0):
    image = verify_alpha_channel(image)
    image_h, image_w, image_c = image.shape
    color_bgra = (blue, green, red, 1)
    overlay = np.full((image_h, image_w, 4), color_bgra, dtype='uint8')
    cv2.addWeighted(overlay, intensity, image, 1.0, 0, image)
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image

def alpha_blend(f_1, f_2, mask):
    alpha = mask / 255.0
    image = cv2.convertScaleAbs(f_1 * (1 - alpha) + f_2 * alpha)
    return image

def apply_circle_blur(image, intensity=0.5):
    image = verify_alpha_channel(image)
    image_h, image_w, image_c = image.shape
    y = int(image_h / 2)
    x = int(image_w / 2)
    radius = int(y / 2)
    center = (x, y)
    mask = np.zeros((image_h, image_w, 4), dtype='uint8')
    cv2.circle(mask, center, radius, (255, 255, 255), -1, cv2.LINE_AA)
    mask = cv2.GaussianBlur(mask, (21, 21), 11)
    blured = cv2.GaussianBlur(image, (21, 21), 11)
    blended = alpha_blend(image, blured, 255 - mask)
    image = cv2.cvtColor(blended, cv2.COLOR_BGRA2BGR)
    return image

def faceRecognition(sourceURL, video_filter, global_full_name):
    video_capture = cv2.VideoCapture(sourceURL)
    if video_capture is None or not video_capture.isOpened():
        if sourceURL == "http://192.168.1.122:8080/video":
            print("Alert - Camera 1 disconnected!!!")
        if sourceURL == "http://192.168.1.111:8080/video":
            print("Alert - Camera 2 disconnected!!!")
    else:
        if sourceURL == "http://192.168.1.122:8080/video":
            print("Connected to Camera 1...\nReceiving Feed...")
        if sourceURL == "http://192.168.1.111:8080/video":
            print("Connected to Camera 2...\nReceiving Feed...")
        screenshotsPath = os.path.abspath("static/Screenshots")
        cameraFeedPath = ""
        if sourceURL == "http://192.168.1.122:8080/video":
            cameraFeedPath = os.path.join(screenshotsPath, global_full_name, camera_feed_1_location)
        if sourceURL == "http://192.168.1.111:8080/video":
            cameraFeedPath = os.path.join(screenshotsPath, global_full_name, camera_feed_2_location)
        if not os.path.exists(cameraFeedPath):
            os.makedirs(cameraFeedPath)
        criminalPath = os.path.join(screenshotsPath, global_full_name)
        if not os.path.exists(criminalPath):
            os.makedirs(criminalPath)
        while True:
            ret, frame = video_capture.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #frame = cv2.resize(frame, interpolation=cv2.INTER_AREA)
            faces = face_cascade.detectMultiScale(gray, 2.5, 4)
            for (x, y, w, h) in faces:
                timestr = time.strftime("%d-%m-%Y, %H-%M-%S")
                if video_filter == "no":
                    cv2.imwrite(os.path.join(cameraFeedPath, timestr + '.jpg'), frame)
                    cv2.imwrite(os.path.join(criminalPath, 'comparison.jpg'), frame)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if video_filter == "gray":
                    cv2.imwrite(os.path.join(cameraFeedPath, timestr + '(GRAY).jpg'), gray)
                    cv2.imwrite(os.path.join(criminalPath, 'comparison.jpg'), gray)
                    cv2.rectangle(gray, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if video_filter == "invert":
                    invert = apply_invert(frame)
                    cv2.imwrite(os.path.join(cameraFeedPath, timestr + '(INVERT).jpg'), invert)
                    cv2.imwrite(os.path.join(criminalPath, 'comparison.jpg'), invert)
                    cv2.rectangle(invert, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if video_filter == "sepia":
                    sepia = apply_sepia(frame)
                    cv2.imwrite(os.path.join(cameraFeedPath, timestr + '(SEPIA).jpg'), sepia)
                    cv2.imwrite(os.path.join(criminalPath, 'comparison.jpg'), sepia)
                    cv2.rectangle(sepia, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if video_filter == "redish":
                    redish = apply_color_overlay(frame, intensity=0.5, red=230, blue=10)
                    cv2.imwrite(os.path.join(cameraFeedPath, timestr + '(REDISH).jpg'), redish)
                    cv2.imwrite(os.path.join(criminalPath, 'comparison.jpg'), redish)
                    cv2.rectangle(redish, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if video_filter == "blur":
                    circle_blur = apply_circle_blur(frame)
                    cv2.imwrite(os.path.join(cameraFeedPath, timestr + '(BLUR).jpg'), circle_blur)
                    cv2.imwrite(os.path.join(criminalPath, 'comparison.jpg'), circle_blur)
                    cv2.rectangle(circle_blur, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if sourceURL == "http://192.168.1.122:8080/video":
                    cv2.imwrite(os.path.join(criminalPath, 'Camera1-last-updated.jpg'), frame)
                if sourceURL == "http://192.168.1.111:8080/video":
                    cv2.imwrite(os.path.join(criminalPath, 'Camera2-last-updated.jpg'), frame)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if sourceURL == "http://192.168.1.122:8080/video":
                cv2.imshow(camera_feed_1_location, frame)
                camera_handle = ctypes.windll.user32.FindWindowW(None, camera_feed_1_location)
                ctypes.windll.user32.ShowWindow(camera_handle, 6)
            if sourceURL == "http://192.168.1.111:8080/video":
                cv2.imshow(camera_feed_2_location, frame)
                camera_handle = ctypes.windll.user32.FindWindowW(None, camera_feed_2_location)
                ctypes.windll.user32.ShowWindow(camera_handle, 6)
            comparisonImagePath = os.path.join(criminalPath, 'comparison.jpg')
            databaseImagePath = os.path.join(criminalPath, 'database_image_resized.jpg')
            img_bgr = cv2.imread(comparisonImagePath)
            img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            template = cv2.imread(databaseImagePath, 0)
            res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.5
            loc = np.where(res >= threshold)
            detected = "false"
            for pt in zip(*loc[::-1]):
                detected = "true"
            if detected == "true":
                # delete first
                if os.path.exists(os.path.join(criminalPath, 'detected.jpg')):
                    os.remove(os.path.join(criminalPath, 'detected.jpg'))
                cv2.imwrite(os.path.join(criminalPath, 'detected.jpg'), img_bgr)
                sql = mydb.cursor()
                query = """UPDATE criminals SET last_location= %s WHERE full_name = %s"""
                global_full_name = global_full_name.replace("_", " ")
                global last_known_location
                if sourceURL == "http://192.168.1.122:8080/video":
                    query_input = (camera_feed_1_location, global_full_name)
                    last_known_location = camera_feed_1_location
                if sourceURL == "http://192.168.1.111:8080/video":
                    query_input = (camera_feed_2_location, global_full_name)
                    last_known_location = camera_feed_2_location
                sql.execute(query, query_input)
                mydb.commit()
                sql.close()
            if cv2.waitKey(1) & 0xFF == ord('q') or 0xFF == ord('Q'):
                break
    video_capture.release()
    cv2.destroyAllWindows()