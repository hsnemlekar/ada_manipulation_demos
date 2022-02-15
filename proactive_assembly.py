#!/usr/bin/env python3

import pdb
import sys
import time
import pickle
import numpy as np
from copy import deepcopy
from threading import Thread

import adapy
import rospy
from std_msgs.msg import Float64MultiArray
from moveit_ros_planning_interface._moveit_roscpp_initializer import roscpp_init

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import common


# set to False if operating real robot
IS_SIM = False

# directory path for each machine
directory_syspath = "/home/icaros/ros_ws/src/ada_manipulation_demos"

# urdf files path 
urdf_filepath = "package://ada_manipulation_demos/urdf_collection"


# ------------------------------------------------------- MAIN ------------------------------------------------------- #

class AssemblyController(QMainWindow):

    def __init__(self):
        super(AssemblyController, self).__init__()

        # initialize robot
        self.ada = adapy.Ada(IS_SIM)

        # ------------------------------------------ Create sim environment ---------------------------------------------- #

        # objects in airplane assembly
        storageURDFUri = urdf_filepath + "/storage.urdf"
        storagePose = [0., -0.3, -0.77, 0, 0, 0, 0]

        wingURDFUri = urdf_filepath + "/abstract_main_wing.urdf"
        wingPose = [0.75, -0.3, 0., 0.5, 0.5, 0.5, 0.5]

        tailURDFUri = urdf_filepath + "/abstract_tail_wing.urdf"
        tailPose = [-0.7, -0.25, 0.088, 0.5, 0.5, 0.5, 0.5]

        container1URDFUri = urdf_filepath + "/container_1.urdf"
        container1_1Pose = [0.4, -0.4, 0., 0., 0., 0., 0.]
        container1_2Pose = [-0.4, -0.4, 0., 0., 0., 0., 0.]
        container1_3Pose = [0.55, -0.3, 0., 0., 0., 0., 0.]
        container1_4Pose = [-0.55, -0.3, 0., 0., 0., 0., 0.]

        container2URDFUri = urdf_filepath + "/container_2.urdf"
        container2_1Pose = [0.4, -0.1, 0, 0., 0., 0., 0.]
        container2_2Pose = [-0.4, -0.1, 0., 0., 0., 0., 0.]
        
        container3URDFUri = urdf_filepath + "/container_3.urdf"
        container3_1Pose = [0.6, 0., 0., 0., 0., 0., 0.]
        container3_2Pose = [-0.6, 0., 0., 0., 0, 0, 0]

        # grasp TSR and offsets
        tailGraspPose = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1]]
        tailGraspOffset = [0., 0.175, 0.]
        container1GraspPose = [[0., 1., 0., 0.], [1., 0., 0., -0.05], [0., 0., -1, 0.8], [0., 0., 0., 1.]]
        container1GraspOffset = [0., 0., -0.07]
        container2GraspPose = [[0., 1., 0., 0.], [1., 0., 0., -0.1], [0., 0., -1, 0.1], [0., 0., 0., 1.]]
        container2GraspOffset = [0., -0.115, 0.]
        container3GraspPose = [[-1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., -1., 0.1], [0., 0., 0., 1.]]
        container3GraspOffset = [0., 0., 0.]

        # hard-coded grasps
        self.graspConfig, self.deliveryRotation = {}, {}
        self.graspConfig["long bolts"] = [-2.11464507,  4.27069802,  2.12562682, -2.9179622, -1.1927828, -0.16230427]
        self.deliveryRotation["long bolts"] = -1.34
        self.graspConfig["short bolts"] = [-0.72561783, 4.31588712, 2.28856202, -2.71514972, -1.42200445, 1.01089267]
        self.deliveryRotation["short bolts"] = 1.25
        self.graspConfig["propeller nut"] = [0.49700125, 1.86043184, 3.78425230, 2.63384048, 1.44808279, 1.67817618]
        self.deliveryRotation["propeller nut"] = -1.1
        self.graspConfig["tail screw"] = [-0.46015322, 4.47079882, 2.68192519, -2.584758426, -1.74260217, 1.457295330]
        self.deliveryRotation["tail screw"] = 1.0  
        self.graspConfig["propeller blades"] = [-2.4191907,  3.9942575,  1.29241768,  3.05926906, -0.50726387, -0.52933128]
        self.deliveryRotation["propeller blades"] = -1.1
        self.graspConfig["tool"] = [-0.32843145,  4.02576609,  1.48440087, -2.87877031, -0.79457283,  1.40310179]
        self.deliveryRotation["tool"] = 1.05
        self.graspConfig["propeller hub"] = [3.00773842,  4.21352853,  1.98663177, -0.17330897,  1.01156224, -0.46210507]
        self.deliveryRotation["propeller hub"] = -0.6
        self.graspConfig["tail wing"] = [3.129024,  1.87404028,  3.40826295,  0.53502216, -1.86749865, -0.99044654]
        self.deliveryRotation["tail wing"] = 0.7

        # initialize sim environment
        self.world = self.ada.get_world()
        viewer = self.ada.start_viewer("airplane_assembly_demo", "map")

        # add parts to sim environment
        storageInWorld = self.world.add_body_from_urdf(storageURDFUri, storagePose)
        container1_1 = self.world.add_body_from_urdf(container1URDFUri, container1_1Pose)
        container1_2 = self.world.add_body_from_urdf(container1URDFUri, container1_2Pose)
        container1_3 = self.world.add_body_from_urdf(container1URDFUri, container1_3Pose)
        container1_4 = self.world.add_body_from_urdf(container1URDFUri, container1_4Pose)
        container2_1 = self.world.add_body_from_urdf(container2URDFUri, container2_1Pose)
        container2_2 = self.world.add_body_from_urdf(container2URDFUri, container2_2Pose)
        container3_1 = self.world.add_body_from_urdf(container3URDFUri, container3_1Pose)
        # container3_2 = self.world.add_body_from_urdf(container3URDFUri, container3_2Pose)
        tailWing = self.world.add_body_from_urdf(tailURDFUri, tailPose)

        # dict of all objects
        self.objects = {"long bolts": [container1_1, container1_1Pose, container1GraspPose, container1GraspOffset],
                        "short bolts": [container1_2, container1_2Pose, container1GraspPose, container1GraspOffset],
                        "propeller nut": [container1_3, container1_3Pose, container1GraspPose, container1GraspOffset],
                        "tail screw": [container1_4, container1_4Pose, container1GraspPose, container1GraspOffset],
                        "propeller blades": [container2_1, container2_1Pose, container2GraspPose, container2GraspOffset],
                        "tool": [container2_2, container2_2Pose, container2GraspPose, container2GraspOffset],
                        "propeller hub": [container3_1, container3_1Pose, container3GraspPose, container3GraspOffset],
                        "tail wing": [tailWing, tailPose, tailGraspPose, tailGraspOffset],
                        "main wing": [],
                        "airplane body": []}

        # ------------------------------------------------ Get robot config ---------------------------------------------- #

        collision = self.ada.get_self_collision_constraint()

        self.arm_skeleton = self.ada.get_arm_skeleton()
        self.arm_state_space = self.ada.get_arm_state_space()
        self.hand = self.ada.get_hand()
        self.hand_node = self.hand.get_end_effector_body_node()

        viewer.add_frame(self.hand_node)

        # ------------------------------- Start executor for real robot (not needed for sim) ----------------------------- #

        if not IS_SIM:
            self.ada.start_trajectory_controllers() 

        self.armHome = [-1.57, 3.14, 1.23, -2.19, 1.8, 1.2]
        waypoints = [(0.0, self.arm_skeleton.get_positions()), (1.0, self.armHome)]
        trajectory = self.ada.compute_joint_space_path(waypoints)  # self.ada.plan_to_configuration(self.armHome)
        self.ada.execute_trajectory(trajectory)
        self.hand.execute_preshape([0.15, 0.15])
      
        # -------------------------------------- Assembly and Aniticipation Info ----------------------------------------- #

        user_id = input("Enter user id: ")

        # load the learned q_values for each state
        self.qf = pickle.load(open("data/q_values_" + user_id + ".p", "rb"))
        self.states = pickle.load(open("data/states_" + user_id + ".p", "rb"))

        # actions in airplane assembly and objects required for each action
        self.remaining_user_actions = [0, 1, 2, 3, 4, 5, 6, 7]
        self.action_names = ["insert main wing",
                             "insert tail wing",
                             "insert long bolts",
                             "insert tail screw",
                             "screw long bolt",
                             "screw tail screw",
                             "screw propeller blades",
                             "screw propeller base"]
        self.action_counts = [1, 1, 4, 1, 4, 1, 4, 1]
        self.required_objects = [["main wing", "airplane body"],
                                 ["tail wing", "airplane body"],
                                 ["long bolts", "tool"],
                                 ["tail", "tail screw"],
                                 ["long bolts", "tool"],
                                 ["tail screw", "tool"],
                                 ["propeller blades", "propeller hub", "short bolts", "tool"],
                                 ["propeller nut", "airplane body"]]
        
        # objects yet to be delivered
        self.remaining_objects = list(self.objects.keys())

        # subscribe to action recognition
        sub_act = rospy.Subscriber("/april_tag_detection", Float64MultiArray, self.callback, queue_size=1)

        # initialize user sequence
        self.time_step = 0
        self.user_sequence = []
        self.anticipated_action_names = []
        self.suggested_objects = []

        # proactive
        self.delivering_part = False
        self.current_suggestion = None

        # ------------------------------------------------ GUI details --------------------------------------------------- #

        # window title and size
        self.setWindowTitle("Robot Commander")
        self.setGeometry(0, 0, 1280, 720)

        # prompt
        query = QLabel(self)
        query.setText("Which part(s) do you want?")
        query.setFont(QFont('Arial', 28))
        query.adjustSize()
        query.move(95, 135)

        # task info
        assembly_image = QLabel(self)
        pixmap = QPixmap(directory_syspath + "/src/actual_task.jpg")
        pixmap = pixmap.scaledToWidth(1125)
        assembly_image.setPixmap(pixmap)
        assembly_image.adjustSize()
        assembly_image.move(660, 145)

        # inputs
        options = deepcopy(self.remaining_objects)
        suggestions = deepcopy(self.suggested_objects)
        suggestion_text = deepcopy(self.anticipated_action_names)

        # print the options
        option_x, option_y = 210, 200
        buttons = []
        for opt in options:
            opt_button = QPushButton(self)
            opt_button.setText(opt)
            opt_button.setFont(QFont('Arial', 20))
            opt_button.setGeometry(option_x, option_y, 225, 50)
            opt_button.setCheckable(True)
            if opt in suggestions:
                opt_button.setStyleSheet("QPushButton {background-color : lightgreen;} QPushButton::checked {background-color : lightpink;}")
            else:
                opt_button.setStyleSheet("QPushButton::checked {background-color : lightpink;}")
            buttons.append(opt_button)
            option_y += 50    
        self.option_buttons = buttons

        # button for performing suggested actions
        option_x = 85
        option_y += 50
        self.suggested_button = QPushButton(self)
        self.suggested_button.setText("YES. Give the parts you suggested.")
        self.suggested_button.setFont(QFont('Arial', 20))
        self.suggested_button.setGeometry(option_x, option_y, 500, 50)
        self.suggested_button.setStyleSheet("background-color : lightgreen")
        self.suggested_button.setCheckable(True)
        self.suggested_button.clicked.connect(self.deliver_part)

        # button for performing selected actions
        option_x = 80
        option_y += 75
        self.selected_button = QPushButton(self)
        self.selected_button.setText("NO. Give the parts I selected.")
        self.selected_button.setFont(QFont('Arial', 20))
        self.selected_button.setGeometry(option_x, option_y, 500, 50)
        self.selected_button.setStyleSheet("background-color : lightpink")
        self.selected_button.setCheckable(True)
        self.selected_button.clicked.connect(self.deliver_part)

        # print current time step
        self.step_label = QLabel(self)
        self.step_label.setText("Current time step: " + str(self.time_step))
        self.step_label.setFont(QFont('Arial', 36))
        self.step_label.adjustSize()
        self.step_label.move(715, 65)

        # pre-text for suggestion action
        pre_text = QLabel(self)
        pre_text.setText("Suggested next action:")
        pre_text.setFont(QFont('Arial', 36))
        pre_text.adjustSize()
        pre_text.move(715, 820)

        # print the anticipated action
        self.user_instruction = QLabel(self)
        self.user_instruction.setText(str(suggestion_text))
        self.user_instruction.setFont(QFont('Arial', 32))
        self.user_instruction.adjustSize()
        self.user_instruction.move(1235, 820)
        self.user_instruction.setStyleSheet("color: green")

        # update timer
        self.time_to_respond = 10
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_application)
        
        self.time_left = deepcopy(self.time_to_respond)
        self.countdown = QLabel(self)
        self.countdown.setText(str(self.time_left))
        self.countdown.setFont(QFont('Arial', 36))
        self.countdown.setStyleSheet("background-color: khaki")
        self.countdown.adjustSize()
        self.countdown.move(1720, 65)
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.timer_update)
        
        self.timer.start(self.time_to_respond*1000) 
        self.countdown_timer.start(1000)


    def timer_update(self): 
        self.time_left -=1
        self.countdown.setText(" " + str(self.time_left) + " ")
        if self.time_left == 0:
            self.time_left = deepcopy(self.time_to_respond)
            self.countdown.setText(str(self.time_left))


    def update_application(self):

        # update time stamp
        self.step_label.setText("Current time step: " + str(self.time_step))

        # update anticipated action
        self.user_instruction.setText(str(self.anticipated_action_names))
        self.user_instruction.adjustSize()

        # update suggested options
        for opt_button in self.option_buttons:
            # opt_button.setChecked(False)
            if opt_button.text() not in self.remaining_objects:
                opt_button.setChecked(False)
                opt_button.setCheckable(False)
                opt_button.setStyleSheet("QPushButton {color : lightgrey;}")
            elif opt_button.text() in self.suggested_objects:
                opt_button.setStyleSheet("QPushButton {background-color : lightgreen;} QPushButton::checked {background-color : lightpink;}")
            else:
                opt_button.setStyleSheet("QPushButton::checked {background-color : lightpink;}")

        # update action buttons
        self.suggested_button.setChecked(False)
        self.selected_button.setChecked(False)
        
        
    def callback(self, data):

        # current recognised action sequence
        detected_sequence = [int(a) for a in data.data]

        # current recognised parts
        detected_parts = data.layout.dim[0].label.split(",")
            
        # update action sequence
        self.user_sequence = detected_sequence
        self.time_step = len(self.user_sequence)

        # determine current state based on detected action sequence
        current_state = self.states[0]
        for user_action in self.user_sequence:
            for i in range(self.action_counts[user_action]):
                p, next_state = common.transition(current_state, user_action)
                current_state = next_state

        # update remaining parts
        self.remaining_objects = [rem_obj for rem_obj in self.remaining_objects if rem_obj not in detected_parts]

        # ---------------------------------------- Anticipate next user action --------------------------------------- #
        sensitivity = 0.0
        max_action_val = -np.inf
        available_actions, anticipated_actions = [], []
        
        for a in self.remaining_user_actions:
            s_idx = self.states.index(current_state)
            p, next_state = common.transition(current_state, a)
            
            # check if the action results in a new state
            if next_state:
                available_actions.append(a)

                if self.qf[s_idx][a] > (1 + sensitivity) * max_action_val:
                    anticipated_actions = [a]
                    max_action_val = self.qf[s_idx][a]

                elif (1 - sensitivity) * max_action_val <= self.qf[s_idx][a] <= (1 + sensitivity) * max_action_val:
                    anticipated_actions.append(a)
                    max_action_val = self.qf[s_idx][a]

        # determine the legible names of the anticipated actions
        self.anticipated_action_names = [self.action_names[a] for a in anticipated_actions]

        # determine objects required for anticipated actions
        suggested_objs = []
        for a in anticipated_actions:
            suggested_objs += [obj for obj in self.required_objects[a] if obj in self.remaining_objects]
        suggested_objs = list(set(suggested_objs))

        if not self.delivering_part and set(suggested_objs) != set(self.suggested_objects):
            if suggested_objs:
                self.current_suggestion = suggested_objs[0]
                reached = self.reach_part(self.current_suggestion)
                # self.ada.execute_trajectory(trajectory)

            self.suggested_objects = deepcopy(suggested_objs)


    def reach_part(self, chosen_obj, midpoint=False):

        if chosen_obj not in ["main wing", "airplane body", "none"]:
            obj = self.objects[chosen_obj][0]
            objPose = self.objects[chosen_obj][1]
            objGraspPose = self.objects[chosen_obj][2]

            # use pre-computed grasp configuration if available
            if chosen_obj in self.graspConfig.keys():
                print("Running hard-coded...")
                grasp_configuration = self.graspConfig[chosen_obj]
            else:
                print("Creating new TSR.")
                # grasp TSR for object
                objTSR = common.createTSR(objPose, objGraspPose)
                # marker = viewer.add_tsr_marker(objTSR)
                # input("Marker look good?")

                # perform IK to compute grasp configuration
                ik_sampleable = adapy.create_ik(self.arm_skeleton, self.arm_state_space, objTSR, self.hand_node)
                ik_generator = ik_sampleable.create_sample_generator()
                configurations = []
                samples, max_samples = 0, 10
                while samples < max_samples and ik_generator.can_sample():
                    samples += 1
                    goal_state = ik_generator.sample(self.arm_state_space)
                    if len(goal_state) == 0:
                        continue
                    configurations.append(goal_state)
                    print("Found new configuration.")

                grasp_configuration = configurations[0]

            # plan path to grasp configuration
            if midpoint:
                waypoints = [(0.0, self.ada.get_arm_positions()), (1.0, self.armHome), (2.0, grasp_configuration)]
            else:
                waypoints = [(0.0, self.ada.get_arm_positions()), (1.0, grasp_configuration)]
            trajectory = self.ada.compute_joint_space_path(waypoints)

            if not trajectory:
                print("Failed to find a solution!")
            else:
                # execute the planned trajectory
                self.ada.execute_trajectory(trajectory)
                return True

        return False


    def deliver_part(self):

        self.delivering_part = True
        set_midpoint = False
        
        # check which objects were selected by the user       
        if self.selected_button.isChecked():
            objects_to_deliver = []
            for option in self.option_buttons:
                if option.isChecked():
                    objects_to_deliver.append(option.text())
            set_midpoint = True
        elif self.suggested_button.isChecked():
            objects_to_deliver = self.suggested_objects
        else:
            objects_to_deliver = []
        
        # loop over all objects to be delivered
        for chosen_obj in objects_to_deliver:

            # instruct the user to retreive the parts that cannot be delivered by the robot
            if chosen_obj in ["main wing", "airplane body", "none"]:
                print("Cannot provide this part.")
                msg = QMessageBox()
                msg.setText("Get the parts you need while the robot waits.")
                msg.setFont(QFont('Arial', 20))
                msg.setWindowTitle("Robot Message")
                QTimer.singleShot(4000, msg.close)    
                msg.exec_()
            else:
                # deliver parts requested by the user whenever possible
                print("Providing the required part.")

                # ---------------------------------------- Collision detection --------------------------------------- #

                # collision_free_constraint = self.ada.set_up_collision_detection(ada.get_arm_state_space(), self.ada.get_arm_skeleton(),
                #                                                                        [obj])
                # full_collision_constraint = self.ada.get_full_collision_constraint(ada.get_arm_state_space(),
                #                                                                      self.ada.get_arm_skeleton(),
                #                                                                      collision_free_constraint)
                # collision = self.ada.get_self_collision_constraint()


                # -------------------------------------- Plan path for grasping -------------------------------------- #
                
                reached = self.reach_part(chosen_obj, midpoint=set_midpoint)

                # ------------------------------------------ Execute path to grasp object --------------------------------- #

                if not reached:
                    print("Cannot pick the part.")
                else:
                    # execute the planned trajectory
                    # self.ada.execute_trajectory(trajectory)
                    
                    # lower gripper
                    traj = self.ada.plan_to_offset("j2n6s200_hand_base", [0., 0., -0.045])
                    self.ada.execute_trajectory(traj)
                    
                    # grasp the object                    
                    self.hand.execute_preshape([1.3, 1.3])
                    time.sleep(1.5)
                    # self.hand.grab(obj)

                    # lift up grasped object
                    traj = self.ada.plan_to_offset("j2n6s200_hand_base", [0., 0., 0.15])
                    self.ada.execute_trajectory(traj)

                    # move grasped object to workbench
                    current_position = self.arm_skeleton.get_positions()
                    new_position = current_position.copy()
                    new_position[0] += self.deliveryRotation[chosen_obj]
                    waypoints = [(0.0, current_position), (1.0, new_position)]
                    traj = self.ada.compute_joint_space_path(waypoints)
                    self.ada.execute_trajectory(traj)

                    # ----------------------- Lower grasped object using Jacobian pseudo-inverse ------------------------ #

                    traj = self.ada.plan_to_offset("j2n6s200_hand_base", [0., 0., -0.10])
                    self.ada.execute_trajectory(traj)

                    # self.hand.ungrab()
                    self.hand.execute_preshape([0.15, 0.15])
                    # self.world.remove_skeleton(obj)
                    time.sleep(1)

                    # ------------------- Move robot back to home ------------------- #

                    waypoints = [(0.0, self.ada.get_arm_positions()), (1.0, self.armHome)]
                    traj = self.ada.compute_joint_space_path(waypoints)
                    self.ada.execute_trajectory(traj)

        self.delivering_part = False
        print("Finished executing actions.")
        # trajectory = self.reach_part(self.suggested_objects[0])
        # self.ada.execute_trajectory(trajectory)


# MAIN
# initialise ros node
rospy.init_node("proactive_assembly")
roscpp_init('proactive_assembly', [])
app = QApplication(sys.argv)
win = AssemblyController()
win.showMaximized()
app.exec_()
try:
    rospy.spin()
except KeyboardInterrupt:
    print ("Shutting down")

input("Press Enter to Quit...")
