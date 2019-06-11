#!/usr/bin/env python

from __future__ import print_function

import rospy

import time

from sensor_msgs.msg import Joy
from sensor_msgs.msg import Image

import sys, select, termios, tty

import cv2

import cv_bridge

import numpy as np

msg = """

"""

class JoyPub:
    def __init__(self):
        self.pub_ = rospy.Publisher('/AizuSpider/joy', Joy, queue_size = 2)
        self.rate = rospy.Rate(30)
        rospy.Subscriber("/AizuSpider/FRONT_CAMERA/image", Image, self.vision_cb)
        self.pub_view_ = rospy.Publisher('/debug_view', Image, queue_size = 1)
        self.left_flag = rospy.get_param('~left_flag', False)
        self.helper_flag = rospy.get_param('~helper_flag', False)
        self.offset = 200
        self.helper_cnt = 0
        self.endflag = False
        
    def vision_cb(self, msg):
        bridge = cv_bridge.CvBridge()
        img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        lower = np.array([0,100,200])
        higher = np.array([150,200,255])
        mask = cv2.inRange(img, lower, higher)
        mask[480:, :] = 0
        mask[:, 960:] = 0
        mask[:, :320] = 0
        mask_msg = bridge.cv2_to_imgmsg(mask, encoding='8UC1')
        mask_msg.header = msg.header
        self.pub_view_.publish(mask_msg)

        threshold = 255 * 15
        helper_threshold = 250
        
        if self.helper_flag:
            tmp_left = -1
            tmp_right = -1
            for i in range(mask.shape[1]):
                if sum(mask[:,i]) > threshold:
                    tmp_left = i
                    break
            for i in range(mask.shape[1]-1, -1, -1):
                if sum(mask[:,i]) > threshold:
                    tmp_right = i
                    break

            if tmp_left != -1 and tmp_right != -1:
                tmp = (tmp_left + tmp_right) / 2.0
                if tmp_right - tmp_left > helper_threshold:
                    self.helper_cnt += 1
                    if self.helper_cnt == 5:
                        self.endflag = True
                else:
                    self.helper_cnt = 0
            else:
                tmp = mask.shape[1] / 2.0
                self.helper_cnt = 0

        else:
            if self.left_flag:
                for i in range(mask.shape[1]):
                    if sum(mask[:,i]) > threshold:
                        tmp = i
                        tmp -= self.offset
                        break
            else:
                for i in range(mask.shape[1]-1, -1, -1):
                    if sum(mask[:,i]) > threshold:
                        tmp = i
                        tmp += self.offset
                        break

        self.angle = (tmp - (mask.shape[1] / 2.0)) / mask.shape[1]

        self.vision_pub_.publish(mask_msg)

    def main(self):
        try:
            self.angle = 0
            while not rospy.is_shutdown():
                msg = Joy()
                msg.axes = [0]*8
                msg.buttons = [0]*11
                # [3] if 1 arm above, -1 arm down
                # [5] if 1 buck and -1 forward
                # [4] if -1 left, 1 right
                msg.axes[5] = -1.0
                msg.axes[4] = self.angle * 2

                if self.endflag:
                    msg.axes = [0]*8
                    msg.buttons = [0]*11
                    msg.axes[4] = -1

                self.pub_.publish(msg)
                self.rate.sleep()


        except Exception as e:
            print(e)
        finally:
            msg = Joy()
            msg.axes = [0]*8
            msg.buttons = [0]*11
            self.pub_.publish(msg)

if __name__=="__main__":
    rospy.init_node('keyboard_joy', anonymous=True)
    jp = JoyPub()
    jp.main()

