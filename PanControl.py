# William Yager
# Leap Python mouse controller POC
# This file is for palm-tilt and gesture-based control (--palm)


import math
from leap import Leap, Mouse
import Geometry
from MiscFunctions import *


# The Listener that we attach to the controller. This listener is for palm tilt movement
class Pan_Control_Listener(Leap.Listener):
    def __init__(self, mouse, smooth_aggressiveness=8, smooth_falloff=1.3):
        # Initialize like a normal listener
        super(Pan_Control_Listener, self).__init__()
        # Initialize a bunch of stuff specific to this implementation
        self.screen = None
        self.screen_resolution = (1920, 1080)
        # The cursor object that lets us control mice cross-platform
        self.cursor = mouse.absolute_cursor()
        self.mouse_position_smoother = mouse_position_smoother(
            smooth_aggressiveness, smooth_falloff)  # Keeps the cursor from fidgeting
        # A signal debouncer that ensures a reliable, non-jumpy click
        self.mouse_button_debouncer = debouncer(5)
        # This holds the ID of the most recently used pointing finger, to prevent annoying switching
        self.most_recent_pointer_finger_id = None

    def on_init(self, controller):
        print("Initialized")

    def on_connect(self, controller):
        print("Connected")

    def on_disconnect(self, controller):
        print("Disconnected")

    def on_exit(self, controller):
        print("Exited")

    def on_frame(self, controller):
        frame = controller.frame()  # Grab the latest 3D data
        if not frame.hands.is_empty:  # Make sure we have some hands to work with
            rightmost_hand = None  # We always have at least one "right hand"
            if len(frame.hands) < 2:  # Just one hand
                # If there's only one hand, we assume it's to be used for mouse control
                self.do_mouse_stuff(frame.hands[0], frame)
            else:  # Multiple hands. We have a right AND a left
                rightmost_hand = frame.hands.rightmost  # Get rightmost hand
                leftmost_hand = frame.hands.leftmost  # Get leftmost hand
                # This will run with >1 hands in frame
                self.do_gesture_recognition(leftmost_hand, rightmost_hand)

    def do_scroll_stuff(self, hand):  # Take a hand and use it as a scroller
        fingers = hand.fingers  # The list of fingers on said hand
        if not fingers.is_empty:  # Make sure we have some fingers to work with
            sorted_fingers = sort_fingers_by_distance_from_screen(
                fingers)  # Prioritize fingers by distance from screen
            # Get the velocity of the forwardmost finger
            finger_velocity = sorted_fingers[0].tip_velocity
            x_scroll = self.velocity_to_scroll_amount(finger_velocity.x)
            y_scroll = self.velocity_to_scroll_amount(finger_velocity.y)
            self.cursor.scroll(x_scroll, y_scroll)

    # Converts a finger velocity to a scroll velocity
    def velocity_to_scroll_amount(self, velocity):
        # The following algorithm was designed to reflect what I think is a comfortable
        # Scrolling behavior.
        vel = velocity  # Save to a shorter variable
        vel = vel + math.copysign(300, vel)  # Add/subtract 300 to velocity
        vel = vel / 150
        vel = vel ** 3  # Cube vel
        vel = vel / 8
        vel = vel * -1  # Negate direction, depending on how you like to scroll
        return vel

    def do_mouse_stuff(self, hand, frame):  # Take a hand and use it as a mouse
        stabilizedPosition = hand.stabilized_palm_position
        interactionBox = frame.interaction_box
        normalizedPosition = interactionBox.normalize_point(stabilizedPosition)
        self.cursor.move(normalizedPosition.x * self.screen_resolution[0], self.screen_resolution[1] - normalizedPosition.y * self.screen_resolution[1])

    # Choose the best pointer finger
    def select_pointer_finger(self, possible_fingers):
        sorted_fingers = sort_fingers_by_distance_from_screen(
            possible_fingers)  # Prioritize fingers by distance from screen
        if self.most_recent_pointer_finger_id != None:  # If we have a previous pointer finger in memory
            for finger in sorted_fingers:  # Look at all the fingers
                # The previously used pointer finger is still in frame
                if finger.id == self.most_recent_pointer_finger_id:
                    return finger  # Keep using it
        # If we got this far, it means we don't have any previous pointer fingers OR we didn't find the most recently used pointer finger in the frame
        # This is the new pointer finger
        self.most_recent_pointer_finger_id = sorted_fingers[0].id
        return sorted_fingers[0]
