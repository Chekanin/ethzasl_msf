#!/usr/bin/env python



#This code closely follows the pytalker/pylistener node example (http://wiki.ros.org/ROSNodeTutorialPython)
#(c) Yannick Huber (huberya)


import roslib
roslib.load_manifest('msf_updates')
import rospy
import numpy as np
import csv
import os
from math import sqrt
#import sys
#sys.path.insert(0, '~/catkin_ws/src/ethzasl_msf/msf_core
#need pose_with_covariance (as input for msf) and position if want to apply noise there as well
from geometry_msgs.msg import PoseWithCovarianceStamped as messagetype


class MsfNoiseHandler:
  def __init__(self):
    #params for noise. To be set in yaml file
    #if mean is 0 then adding pure noise
    #if mean != 0 then is creating some drift aswell
    self.mu_=rospy.get_param("~noise_mean",0.0)
    self.nstddeviations_=rospy.get_param("~noise_number_stddeviations", 0.0)
    self.use_noise_=rospy.get_param("~use_noise", False)
        
    #params for outlier creation. To be set in yaml file
    self.p_outlier_=rospy.get_param("~probability_outlier", 0.0)
    self.create_outlier_=rospy.get_param("~create_outlier", False)
    
    #params to estimate stddeviation of data
    self.ninit_=100
    self.nrecv_=0
    self.stddeviation_=0
    self.datamean_=0
    
    #init publisher
    self.pub_=rospy.Publisher("noise_drift_handler/output", messagetype)
    
  def add_noise(self, arrin):
    noise=np.random.normal(self.mu_, self.nstddeviations_*self.stddeviation_ , len(arrin))
    arrout=arrin+noise
    return arrout


  def create_outlier(self, arrin):
    #add some big disturbance to arrin (for now 100 times stddeviation)
    sign=np.random.bool #need 0/1 random
    noise=np.array([100*self.stddeviation for i in range(len(arrin))])
    if sign:
      arrout=arrin+noise
    else:
      arrout=arrin-noise
    return arrout

  def callback(self, data):
    #handle data here and add noise if necessary
    dataarr=np.array([data.pose.pose.position.x, data.pose.pose.position.y, data.pose.pose.position.z,
    data.pose.pose.orientation.x, data.pose.pose.orientation.y, data.pose.pose.orientation.z,
    data.pose.pose.orientation.w]) # (something like this) may need to convert to array
    if self.nrecv_<self.ninit_:
    #use data to estimate stddeviation (maybe need to do multidim) right now computes 1d stddeviation
      self.nrecv_+=1
      delta=dataarr[0]-self.datamean_
      self.datamean_+=delta/self.nrecv_
      delta2=dataarr[0]-self.datamean_
      self.stddeviation_+=delta*delta2
    if self.nrecv_==self.ninit_:
      self.stddeviation_=sqrt(self.stddeviation_/(self.nrecv_-1))
    
    else:
      if self.use_noise_:
        dataarr=add_noise(self, dataarr)
      if self.create_outlier_:
        t=np.random.uniform()
        if t<self.p_outlier_:
          dataarr=create_outlier(self, dataarr)
      data.pose.pose.position.x = dataarr[0]
      data.pose.pose.position.y = dataarr[1]
      data.pose.pose.position.z = dataarr[2]
      data.pose.pose.orientation.x = dataarr[3]
      data.pose.pose.orientation.y = dataarr[4]
      data.pose.pose.orientation.z = dataarr[5]
      data.pose.pose.orientation.w = dataarr[6]
      self.pub_.publish(data)
    
  def listener(self):
    topic="noise_drift_handler/input"
    rospy.Subscriber(topic, messagetype, self.callback)
    rospy.spin()
      
  def reconfigure(self, config, level):
    return config
      
if __name__ == '__main__':
  try:
    rospy.init_node('noise_drift_handler', anonymous=True)
    gs=MsfNoiseHandler()
    gs.listener()
  except rospy.ROSInterruptException:
    pass
