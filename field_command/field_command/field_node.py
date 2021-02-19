#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Twist, PoseArray
from sensor_msgs import Imu
from tf.transformations import euler_from_quaternion
from roblib import *  # available at https://www.ensta-bretagne.fr/jaulin/roblib.py

def model_wall(p, p1, p2):
    def isLeft(a, b, c):
        return -sign((c[0, 0] - a[0, 0]) * (b[1, 0] - a[1, 0]) - (c[1, 0] - a[1, 0]) * (b[0, 0] - a[0, 0]))

    def isInBox(a, b, c):
        if a[0, 0] == b[0, 0]:
            dir = "vertical"
        else:
            dir = "horizontal"
        
        if dir == "horizontal":
            xmin, xmax = min(a[0, 0], b[0, 0]), max(a[0, 0], b[0, 0])
            return (xmin <= c[0, 0] <= xmax)
        else:
            ymin, ymax = min(a[1, 0], b[1, 0]), max(a[1, 0], b[1, 0])
            return (ymin <= c[1, 0] <= ymax)

    dx, dy = p2[0, 0] - p1[0, 0], p2[1, 0] - p1[1, 0]
    ng, nd = array([[-dy], [dx]]), array([[dy], [-dx]])
    ng, nd = ng/norm(ng), nd/norm(nd)
    BA = p1 - p
    u = p2 - p1
    d = norm(cross(BA.flatten(), u.flatten())) / norm(u)

    if isInBox(p1, p2, p) and (isLeft(p, p1, p2) == 1):
        res = (1/d**3) * ng #+ ((p-p1) / norm(p-p1) ** 3 + (p-p2) / norm(p-p2) ** 3)
    elif isInBox(p1, p2, p) and (isLeft(p, p1, p2) == -1):
        res = (1/d**3) * nd #+ ((p-p1) / norm(p-p1) ** 3 + (p-p2) / norm(p-p2) ** 3)
    else:
        res = array([[0], [0]]) #+ (p-p1) / norm(p-p1) ** 3 + (p-p2) / norm(p-p2) ** 3

    return res 

def model_box(p, xmin, xmax, ymin, ymax, M):
    if (xmin < p[0, 0] < xmax) and (ymin < p[1, 0] < ymax):
        return M
    else:
        return array([[0], [0]])

def model_objective(p, p_obj):
    N1, N2 = p[0, 0] - p_obj[0, 0], p[1, 0] - p_obj[1, 0]
    obj_x = - 50 * N1 / (N1**2 + N2**2)**(3/2)
    obj_y = - 50 * Nq2 / (N1**2 + N2**2)**(3/2)

    return obj_x, obj_y

def model_player(p, p_j):
    N1, N2 = X1 - p_j[0, 0], X2 - p_j[1, 0]
    j_x = 100 * N1 / (N1**2 + N2**2)**(14/2)
    j_y = 100 * N2 / (N1**2 + N2**2)**(14/2)

    return j_x, j_y

def model_const(p_obj):
    if p_obj[0, 0] < 15:
        return -1
    else:
        return 1

class WrenchSubPub(Node):

    def __init__(self):
        super().__init__('wrench_pub')
        self.position = array([[0.], [0.], [0.]])
        self.objective = array([[0.], [0.]])
        self.players = [array([[5], [5]]), array([[25], [5]])]
        self.avg_speed = 4

        self.const_V = self.const_V()
        self.current_V = self.const_V + self.var_V()
        self.Mx, self.My = arange(0, 30, 0.5), arange(0, 15, 0.3)
        self.X, self.Y = meshgrid(Mx, My)
        self.const_V_array = self.array_const_V()
        self.current_V_array = self.const_V_array + self.array_var_V()

        self.publisher_ = self.create_timer(Twist, '/cmd_yaw', 10)
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.subscription1 = self.create_subscription(Point,'/robot_objective', self.objective_callback,10)
        self.subscription2 = self.create_subscription(PoseArray,'/joueurs_coords', self.players_callback,10)
        self.subscription3 = self.create_subscription(Twist,'/aruco_twist', self.pos_callback,10)
        self.subscription4 = self.create_subscription(Twist,'/imu/data', self.ang_callback,10)

    def objective_callback(self, msg):
        self.objective [0, 0], self.objective[1, 0] = msg.x, msg.z

    def players_callback(self, msg):
        self.players[0][0, 0], self.players[0][1, 0] = msg.poses[0].position.x, msg.poses[0].position.y
        self.players[1][0, 0], self.players[1][1, 0] = msg.poses[1].position.x, msg.poses[1].position.y

    def pos_callback(self, msg):
        self.position[0, 0], self.position[1 ,0] = msg.position.x, msg.position.y

    def ang_callback(self, msg):
        self.position[2, 0] = euler_from_quaternion(msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w)[2]

    def timer_callback(self):
        self.current_V = self.const_V + self.var_V()
        cmd_msg = Twist()
        if (msg.z == 0) or (msg.z == 1):
            d = sqrt((self.objective[0, 0] - self.position[0, 0])**2 + (self.objective[1, 0] - self.position[1, 0])**2)
            if d < 1:
                cmd_msg.linear.x = self.avg_speed * d
            else:
                cmd_msg.linear.x = self.avg_speed
            cmd_msg.angular.z = arctan2(self.current_V[1, 0], self.current_V[0, 0])
        else:
            cmd_msg.linear.x = 0.
            cmd_msg.angular.z = self.position[2, 0]
        self.publisher.publish(cmd_msg)
        plt.clf()
        self.draw_field()

    def const_V(self):
        #gestion des murs
        p1, p2 = array([[0], [0]]), array([[30], [0]])
        Nwall1, Nwall2 = model_wall(self.position, p1, p2)
        p3, p4 = array([[0], [16]]), array([[30], [16]])
        Nwall3, Nwall4 = model_wall(self.position, p3, p4)
        p5, p6 = array([[0], [0]]), array([[0], [16]])
        Nwall5, Nwall6 = model_wall(self.position, p5, p6)
        p7, p8 = array([[30], [0]]), array([[30], [16]])
        Nwall7, Nwall8 = model_wall(self.position, p7, p8)
        p9, p10 = array([[15], [2.5]]), array([[15], [13.5]])
        Nwall9, Nwall10 = model_wall(self.position, p9, p10)
        p11, p12 = array([[0], [13.5]]), array([[2], [13.5]])
        Nwall11, Nwall12 = model_wall(self.position, p11, p12)
        p13, p14 = array([[2.7], [14]]), array([[2.7], [16]])
        Nwall13, Nwall14 = model_wall(self.position, p13, p14)
        p15, p16 = array([[27.3], [0]]), array([[27.3], [2]])
        Nwall15, Nwall16 = model_wall(self.position, p15, p16)
        p17, p18 = array([[28], [2.5]]), array([[28], [2.5]])
        Nwall17, Nwall18 = model_wall(self.position, p17, p18)
        # gestion du filet
        net_x_bot, net_y_bot = model_box(self.position, 13, 17, 1, 8, array([[0], [-1]]))
        net_x_top, net_y_top = model_box(self.position, 13, 17, 8, 15, array([[0], [1]]))

        const_V_x = net_x_bot + net_x_top + Nwall1 + Nwall3 + Nwall5 + Nwall7 + Nwall9 + Nwall11 + Nwall13 + Nwall15 + Nwall17
        const_V_y = net_y_bot + net_y_top + Nwall2 + Nwall4 + Nwall6 + Nwall8 + Nwall10 + Nwall12 + Nwall14 + Nwall16 + Nwall18

        return array([[const_V_x], [const_V_y]])

    def var_V(self):
        obj_x, obj_y = model_objective(self.position, self.objective)
        j_x, j_y = model_player(self.position, self.players[0]) + model_player(self.position, self.players[1])
        const = model_const(self.objective)

        current_V_x = const + obj_x + j_x
        current_V_y = obj_y + j_y

        return array([[current_V_x], [current_V_y]])

    def array_const_V(self):
        n, m = self.X.shape
        VX, VY = np.zeros((n, m)), np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                p = array([[self.X[i, j]], [self.Y[i, j]]])
                VX[i, j], VY[i, j] = self.const_V(p, p1, p2)
        return VX, VY

    def array_var_V(self):
        n, m = self.X.shape
        VX, VY = np.zeros((n, m)), np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                p = array([[self.X[i, j]], [self.Y[i, j]]])
                VX[i, j], VY[i, j] = self.var_V(p, p1, p2)
        return VX, VY

    def draw_field(self):
        self.current_V_array = self.const_V_array + self.array_var_V()
        R = sqrt(VX ** 2 + VY ** 2)
        quiver(self.Mx, self.My, self.current_V_array[0] / R, self.current_V_array[1] / R)
        plt.plot(self.position[0, 0], self.position[1, 0], '.b')
        plt.arrow(self.position[0, 0], self.position[1, 0], self.position[0, 0] + cos(self.position[2, 0]), self.position[1, 0] + sin(self.position[2, 0]), '.b')
        plt.plot(self.objective[0, 0], self.objective[1, 0], '.g')
        plt.plot(self.players[0][0, 0], self.players[0][1, 0], '.r')
        plt.plot(self.players[1][0, 0], self.players[1][1, 0], '.r')

def main(args=None):
    plt.figure()
    rclpy.init(args=args)

    node_ = WrenchSubPub()
    rclpy.spin(node_)

    node_.destroy_node()
    rclpy.shutdown()
    plt.show()


if __name__ == '__main__':
    main()
