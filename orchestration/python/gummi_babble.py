#!/usr/bin/env python

import rospy
import wx
import sys
import random
import time
import pygame
from pygame.locals import *

from gummi import Gummi
import helpers

def isAtJointLimit(angles, mins, maxs):
    atLimits = list()
    for an, mi, ma in zip(angles, mins, maxs):
        if an <= mi:
            atLimits.append(True)
        else:
            if an >= ma:
                atLimits.append(True),
            else:
                atLimits.append(False)
    return atLimits

def limitVelocity(v,limit):
    if v >= limit:
        return limit
    else:
        if v <= -limit:
            return -limit
    return v

def reverseVelocities(vels):
    for i,v in enumerate(vels):
        v = -v/4
        vels[i] = v
    return vels

def main(args):

    pygame.init()
    
    disp = pygame.display.set_mode((600,600),0,32)
    disp.fill((255,255,255))
    pygame.display.update()

    rospy.init_node('GummiBabble', anonymous=True)
    r = rospy.Rate(60)  

    gummi = Gummi()

    gummi.setStiffness(0.45, 0.6, 0.45, 0.3)

    minLimits = [-30,5,-30,-20,-75,-35]
    maxLimits = [65,75,30,20,75,35]

    timeReverse = rospy.Time.now()

    print('WARNING: Moving joints sequentially to equilibrium positions.')
    gummi.doGradualStartup()

    print('WARNING: Moving to resting pose, hold arm!')
    rospy.sleep(3)
    for i in range(0, 400):
        gummi.goRestingPose()
        r.sleep()

    print("GummiArm is live!")
    gummi.setMaxLoads(0.6, 0.8, 0.75, 1.25)

    velocities = [0, 0, 0, 0, 0, 0]
    while not rospy.is_shutdown():

        angles = gummi.getJointAngles()
        angles = helpers.radToDeg(angles)
        #print(angles)

        for i,v in enumerate(velocities):
            ran = random.uniform(-0.0003, 0.0003)  
            v = v + ran
            velocities[i] = v

        reverse = False
        loads = gummi.getLoads()
        #print(loads)
        for i,l in enumerate(loads):
            if i is not 2:
                if i is not 4:
                    if abs(l) > 1:
                        print("Joint " + str(i+1) + " has load above 1: " + str(l) + ".") 
                        reverse = True
        
        if not reverse:
            atLimits = list()
            atLimits = isAtJointLimit(angles, minLimits, maxLimits)
            for i,l in enumerate(atLimits):
                if l:
                    if angles[i] <= minLimits[i]:
                        corrected = 0.0002
                    else:
                        corrected = -0.0002
                    velocities[i] = corrected
                    print("Moving joint " + str(i+1) + " away from joint limit!")

        duration = rospy.Time.now() - timeReverse
        secondsSinceReverse = duration.to_sec()

        if secondsSinceReverse > 2.0:
            if reverse:
                velocities = reverseVelocities(velocities)
                print("Reversing all velocities!")
                timeReverse = rospy.Time.now()
            colour = (0, 255, 0)
        else:
            colour = (255, 0, 0)

        for i,v in enumerate(velocities):
            if i==2: 
                #Upper arm roll
                v = limitVelocity(v,0.001)
            else:
                v = limitVelocity(v,0.002)
            velocities[i] = v

        #print(velocities)
        gummi.setVelocity(velocities)
        gummi.doUpdate()

        disp.fill(colour)
        pygame.display.update()

        r.sleep()
  
if __name__ == '__main__':
    main(sys.argv)
