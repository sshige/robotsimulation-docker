#!/usr/bin/env python

from __future__ import print_function

import rospy

from sensor_msgs.msg import Joy

import sys, select, termios, tty

msg = """

"""

class JoyPub:
    def __init__(self):
        self.settings_ = termios.tcgetattr(sys.stdin)
        self.pub_ = rospy.Publisher('key_joy', Joy, queue_size = 1)
        self.stop_ = rospy.get_param("~stop", 0.5)
        self.rate = rospy.Rate(10)

    def main(self):
        prev1 = None
        prev2 = None
        try:
            while not rospy.is_shutdown():
                key = self.getKey()
                msg = Joy()
                msg.axes = [0]*8
                msg.buttons = [0]*11
                msg.axes[1] = -1
                self.pub_.publish(msg)
                self.rate.sleep()
        except Exception as e:
            print(e)
        finally:
            msg = Joy()
            msg.axes = [0]*8
            msg.buttons = [0]*11
            self.pub_.publish(msg)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings_)

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        keys = []
        key = None
        while(True):
            ret = select.select([sys.stdin], [], [], 0)
            key = sys.stdin.read(1)
            keys.append(key)
            if len(key) >= 1:
                break

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings_)
        return key

if __name__=="__main__":
    rospy.init_node('keyboard_joy', anonymous=True)
    jp = JoyPub()
    jp.main()

