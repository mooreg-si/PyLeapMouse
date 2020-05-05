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
        self.screen_resolution = (2560, 1440)#adjust for display scale. i.e 3840x2016 with 150% scale = 2560x1440
        # The cursor object that lets us control mice cross-platform
        self.cursor = mouse.absolute_cursor()
        self.mouse_position_smoother = mouse_position_smoother(
            smooth_aggressiveness, smooth_falloff)  # Keeps the cursor from fidgeting
        # A signal debouncer that ensures a reliable, non-jumpy click
        self.mouse_button_debouncer = debouncer(5)
        # This holds the ID of the most recently used pointing finger, to prevent annoying switching
        self.most_recent_pointer_finger_id = None
        self.gesture_debouncer = n_state_debouncer(1, 2)

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
                self.do_gesture_recognition(leftmost_hand)
                self.do_mouse_stuff(rightmost_hand,frame)

    def do_mouse_stuff(self, hand, frame):  # Take a hand and use it as a mouse
        stabilizedPosition = hand.stabilized_palm_position
        interactionBox = frame.interaction_box
        normalizedPosition = interactionBox.normalize_point(stabilizedPosition)
        self.cursor.move(normalizedPosition.x * self.screen_resolution[0], self.screen_resolution[1] - normalizedPosition.y * self.screen_resolution[1])
        

    def do_gesture_recognition(self, gesture_hand):
        # store only the extended fingers
        extended_finger_list = gesture_hand.fingers.extended()
        if len(extended_finger_list) == 0:  # One open finger on gesture hand (click down)
            self.gesture_debouncer.signal(1)
        else:  # No open fingers or 3+ open fingers (click up/no action)
            self.gesture_debouncer.signal(0)
        # Now that we've told the debouncer what we *think* the current gesture is, we must act
        # On what the debouncer thinks the gesture is
        if self.gesture_debouncer.state == 1:  # Click/drag mode
            if not self.cursor.left_button_pressed:
                self.cursor.click_down()  # Click down (if needed)
        elif self.gesture_debouncer.state == 0:  # Move cursor mode
            if self.cursor.left_button_pressed:
                self.cursor.click_up()  # Click up (if needed)
