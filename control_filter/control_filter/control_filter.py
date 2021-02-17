#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
import math
import numpy as np

#Message imports
# from std_msgs.msg import String
from geometry_msgs.msg import Twist
from geometry_msgs.msg import Vector3
from geometry_msgs.msg import PoseArray
from geometry_msgs.msg import Point
from std_msgs.msg import Bool


class Node_filter(Node):

    def __init__(self):
        super().__init__('node_filter')
        
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(Twist, 'cmd_vel1',self.listener_callback,10)

    def listener_callback(self, msg):
        cmd = Twist()
        v = msg.linear.x
        u =  msg.angular.z
        print(u," ",v)
        
        new_u, new_v = self.command_filter(u,v)
        
        
        cmd = Twist()
        cmd.linear.x, cmd.linear.y, cmd.linear.z = new_v,0.,0.
        cmd.angular.x, cmd.angular.y, cmd.angular.z = 0.,0.,new_u
        self.publisher_.publish(msg)
        
    def command_filter(self,u,v):
        new_v, new_u = v, u
        if abs(u) > 2:
            new_u = np.sign(u)*min(abs(u),3)
        if abs(u) <0.5:
            new_v = 1.5*v
            
        if abs(u-new_u)> 7.5:
            new_v = 1
            print("--------------------------")
        return(new_u,new_v)


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = Node_filter()

    rclpy.spin(minimal_publisher)


    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
