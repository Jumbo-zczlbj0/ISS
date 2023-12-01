#!/usr/bin/env python

from wpt_tracker.pid_wpt_tracker import VehiclePIDController
from wpt_tracker.linear_mpc_tracker import VehicleLinearMPCController
from iss_msgs.msg import ControlCommand, StateArray, State
from planning_utils.trajectory import Trajectory
import rospy
import numpy as np

class WPTTrackerNode:
    def __init__(self) -> None:
        ctrl_freq = rospy.get_param("~control_frequency", 10)
        self._timer = rospy.Timer(rospy.Duration(1 / ctrl_freq), self._timer_callback)
        self._ctrl_pub = rospy.Publisher("control/wpt_tracker/control_command", ControlCommand, queue_size=1)
        self._ego_state_sub = rospy.Subscriber("carla_bridge/gt_state", State, self._state_callback)
        self._trajectory_sub = rospy.Subscriber("planning/local_planner/trajectory", StateArray, self._trajectory_callback)
        self._ego_state = None
        
        # self._pid_tracker = VehiclePIDController()
        linear_mpc_settings = {
            "acc_table": {0: 0, 0.2: 0.5, 0.4: 0.8, 0.6: 0.9, 0.8: 0.95, 1: 1},
            "nx": 4,
            "nu": 2,
            "N": 20,
            "dt": 0.05,
            "acc_max": 6,
            "steer_max": np.deg2rad(45.0),
            "steer_rate_max": np.deg2rad(15.0),
            "speed_max": 50 / 3.6,
            "ego_veh_info": {
                "wheelbase": 2.8,
                "steer_max": 0.5,
                "acc_max": 6
            },
            "Q": np.diag([1.0, 1.0, 3.0, 3.0]),
            "Qf": np.diag([2.0, 2.0, 3.0, 3.0]),
            "R": np.diag([0.1, 1]),
            "Rd": np.diag([0.1, 1.0])
        }
        self._pid_tracker = VehiclePIDController()
        self._mpc_tracker = VehicleLinearMPCController(linear_mpc_settings)
        self._trajectory = Trajectory()
        
    def _timer_callback(self, event):
        if self._ego_state is None:
            return
        throttle, steering = self._pid_tracker.run_step(self._ego_state)
        # throttle, steering = self._mpc_tracker.run_step(self._ego_state)
        self._ctrl_pub.publish(ControlCommand(steering=steering, throttle=throttle))
    
    def _state_callback(self, msg):
        self._ego_state = msg
    
    def _trajectory_callback(self, msg):
        self._trajectory.from_ros_msg(msg)
        # self._mpc_tracker.set_traj(self._trajectory)
        self._pid_tracker.set_traj(self._trajectory.get_states())
        

if __name__ == "__main__":
    rospy.init_node("wpt_tracker_node")
    wpt_tracker_node = WPTTrackerNode()
    rospy.spin()