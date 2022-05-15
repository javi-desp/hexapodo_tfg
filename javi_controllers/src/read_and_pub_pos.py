#!/usr/bin/env python3

import rospy
import time
from dynamixel_sdk import *
from javi_controllers.srv import *
from javi_controllers.msg import *

from sensor_msgs.msg import JointState
from std_msgs.msg import Header

import math

class service_to_joint_state: 
    def __init__(self, array_tibia_ids, array_femur_ids, array_coxa_ids):
        rospy.init_node('pub_motor_data')
        self.leg_lenghts = {'coxa': 0.0, 'femur': 0.1, 'tibia': 0.15049059936089032}
        self.pub_joint_state = rospy.Publisher('joint_states', JointState, queue_size=10)
        self.rate = rospy.Rate(100) # 50hz

        self.message_joint_state = JointState()
        self.message_joint_state.header = Header()
        self.message_joint_state.name = ['tibia_joint_LB', 'tibia_joint_LM', 'tibia_joint_LF', 
                        'tibia_joint_RB', 'tibia_joint_RM', 'tibia_joint_RF', 
                        'femur_joint_LB', 'femur_joint_LM', 'femur_joint_LF', 
                        'femur_joint_RB', 'femur_joint_RM', 'femur_joint_RF', 
                        'coxa_joint_LB', 'coxa_joint_LM', 'coxa_joint_LF', 
                        'coxa_joint_RB', 'coxa_joint_RM', 'coxa_joint_RF']
        self.message_joint_state.position = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.message_joint_state.velocity = []
        self.message_joint_state.effort = []
    
        self.array_tibia_ids = array_tibia_ids
        self.array_femur_ids = array_femur_ids
        self.array_coxa_ids = array_coxa_ids

        rospy.wait_for_service('get_dinamixel_motor_group_data')
        self.motor_group_service = rospy.ServiceProxy('get_dinamixel_motor_group_data', GetGroupMotorData)

    def update_joint_state_message(self):
        self.message_joint_state.position = [
                self.tibia_group_current_position.motor1_data*2*(math.pi/4095) - math.pi,
                self.tibia_group_current_position.motor2_data*2*math.pi/4095 - math.pi,
                self.tibia_group_current_position.motor3_data*2*math.pi/4095 - math.pi,
                -self.tibia_group_current_position.motor4_data*2*math.pi/4095 + math.pi,
                -self.tibia_group_current_position.motor5_data*2*math.pi/4095 + math.pi,
                -self.tibia_group_current_position.motor6_data*2*math.pi/4095 + math.pi, 

                -self.femur_group_current_position.motor1_data*2*math.pi/4095 + math.pi,
                -self.femur_group_current_position.motor2_data*2*math.pi/4095 + math.pi,
                -self.femur_group_current_position.motor3_data*2*math.pi/4095 + math.pi,
                self.femur_group_current_position.motor4_data*2*math.pi/4095 - math.pi,
                self.femur_group_current_position.motor5_data*2*math.pi/4095 - math.pi,
                self.femur_group_current_position.motor6_data*2*math.pi/4095 - math.pi,  

                -self.coxa_group_current_position.motor1_data*2*math.pi/4095 + math.pi,
                -self.coxa_group_current_position.motor2_data*2*math.pi/4095 + math.pi,
                -self.coxa_group_current_position.motor3_data*2*math.pi/4095 + math.pi,
                -self.coxa_group_current_position.motor4_data*2*math.pi/4095 + math.pi,
                -self.coxa_group_current_position.motor5_data*2*math.pi/4095 + math.pi,
                -self.coxa_group_current_position.motor6_data*2*math.pi/4095 + math.pi
        ]

    def forward_kinematics(self, q_coxa, q_femur, q_tibia):
        x = math.cos(q_coxa) * (self.leg_lenghts["femur"] * math.cos(q_femur) + self.leg_lenghts["tibia"] * math.cos(q_femur + q_tibia))
        y = math.sin(q_coxa) *(self.leg_lenghts["femur"] * math.cos(q_femur) + self.leg_lenghts["tibia"] * math.cos(q_femur + q_tibia))
        z = self.leg_lenghts["coxa"] + self.leg_lenghts["femur"] * math.sin(q_femur) + self.leg_lenghts["tibia"] * math.sin(q_femur + q_tibia)

        return ([x, y, z])

    def inverse_kinematics(self, x, y, z):
        try:
            theta_1 = math.atan2(y, x)
            cos_theta3 = ((x**2 + y+ (z- self.leg_lenghts["coxa"])**2 - self.leg_lenghts["femur"]**2 - self.leg_lenghts["tibia"]**2) / (2 * self.leg_lenghts["femur"] * self.leg_lenghts["tibia"]))
            theta_3 = math.atan2( math.sqrt(1 -cos_theta3**2), cos_theta3)
            theta_2 = (math.atan2(z - self.leg_lenghts["coxa"], math.sqrt(x**2 + y**2)) - math.atan2((self.leg_lenghts["tibia"] * math.sin(theta_3)) , (self.leg_lenghts["femur"] + self.leg_lenghts["tibia"] * math.cos(theta_3))))

            return ([theta_1 , theta_2, theta_3])

        except Exception as e:
            print(e)
            return ([0 , 0, 0])

    def run(self):
        while not rospy.is_shutdown():
            start = time.time()        
            
            self.tibia_group_current_position = self.motor_group_service(self.array_tibia_ids[0],self.array_tibia_ids[1],self.array_tibia_ids[2],
                                                    self.array_tibia_ids[3],self.array_tibia_ids[4],self.array_tibia_ids[5],"position")

            self.femur_group_current_position = self.motor_group_service(self.array_femur_ids[0],self.array_femur_ids[1],self.array_femur_ids[2],
                                                    self.array_femur_ids[3],self.array_femur_ids[4],self.array_femur_ids[5],"position")

            self.coxa_group_current_position = self.motor_group_service(self.array_coxa_ids[0],self.array_coxa_ids[1],self.array_coxa_ids[2],
                                                    self.array_coxa_ids[3],self.array_coxa_ids[4],self.array_coxa_ids[5],"position")


            self.update_joint_state_message()

            self.message_joint_state.header.stamp = rospy.Time.now()
            self.pub_joint_state.publish(self.message_joint_state)
            self.rate.sleep()

            print("F_KIN = ", self.forward_kinematics(self.message_joint_state.position[12], self.message_joint_state.position[6], self.message_joint_state.position[0]))
            
            """
            print("tibia 1: ", self.message_joint_state.position[0])
            print("tibia 2: ", self.message_joint_state.position[3])
            print("femur 1: ", self.message_joint_state.position[6])
            print("femur 2: ", self.message_joint_state.position[9])
            print("coxa 1: ", self.message_joint_state.position[12])
            print("coxa 2: ", self.message_joint_state.position[15])

            print("--------------")
            end = time.time()
            print("RESPONSE IN ", end-start)
            """

def main():
    ID_tibia = [1,2,3,4,5,6]
    ID_femur = [11,21,31,41,51,61]
    ID_coxa = [10,20,30,40,50,60]
    hexapod = service_to_joint_state(ID_tibia, ID_femur, ID_coxa)

    hexapod.run()

if __name__ == '__main__':
    main()

