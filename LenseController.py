import sys
import time
import RPi.GPIO as GPIO


class LenseController:
    """
    Controls the Stepper Motors
    """

    GPIO.setmode(GPIO.BCM)

    # ID
    irisID = 0
    focusID = 1
    zoomID = 2

    # Dir, Step, Enable
    irisPins = [26, 19, 13]
    focusPins = [21, 20, 16]
    zoomPins = [24, 23, 18]

    # maximum positions of each stepper motor (ID)
    maxPositions = [112, 6000, 4200]

    # motor delay
    motorDelay = [0.003, 0.001, 0.001]

    def __init__(self, dummy, dummyy):

        GPIO.setmode(GPIO.BCM)

    def open(self):
        # open lense controllers
        self.iris = DriverController(
                                    self.irisPins,
                                    self.maxPositions[self.irisID],
                                    self.motorDelay[self.irisID])
        self.focus = DriverController(
                                    self.focusPins,
                                    self.maxPositions[self.focusID],
                                    self.motorDelay[self.focusID])
        self.zoom = DriverController(
                                    self.zoomPins,
                                    self.maxPositions[self.zoomID],
                                    self.motorDelay[self.zoomID])

        print('All lenses are now on minimum setting!')

    def close(self):
        # close lense controller: disable all motors and close serial port
        self.iris.disable()
        self.focus.disable()
        self.zoom.disable()
        GPIO.cleanup()

    def disable_drivers(self):
        # disable all motors
        return self.iris.disable(), self.zoom.disable(), self.focus.disable()

    def enable_drivers(self):
        # enable all motors
        return self.iris.enable(), self.zoom.enable(), self.focus.enable()

    def get_lense_info(self):
        # get information about all three motors
        return self.iris.get_min_position(), self.zoom.get_min_position(),\
                self.focus.get_min_position(), self.iris.get_position(),\
                self.zoom.get_position(), self.focus.get_position(),\
                self.iris.get_max_position(), self.zoom.get_max_position(),\
                self.focus.get_max_position()


class DriverController:
    """
    Controls the Stepper Motors
    """
    # setting motor current position
    # motors will be set to this position in __init__

    def __init__(self, pins, maxPosition, delay):

        self.pins = pins
        self.maxPosition = maxPosition
        self.delay = delay
        self.status = 0

        # Set all pins as output
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT)

        self.enable()

        # motor to min position
        self.currPosition = 0
        self.go_n_steps(-maxPosition)

    def init_motor(self):
        return self.go_n_steps(-maxPosition)

    def go_n_steps(self, stepCount):
        if self.isEnabled() is False:
            print('Lense is disbaled!')
            return False
        else:
            self.currPosition = self.currPosition + stepCount
            if (self.currPosition < 0):
                self.currPosition = 0
            if (self.currPosition > self.maxPosition):
                self.currPosition = self.maxPosition

            if (stepCount > 0):
                GPIO.output(self.pins[0], True)
            elif (stepCount < 0):
                GPIO.output(self.pins[0], False),
            else:
                raise Exception('Direction Error!')

            for i in range(0, abs(stepCount)):
                GPIO.output(self.pins[1], True)
                time.sleep(self.delay)
                GPIO.output(self.pins[1], False)
                time.sleep(self.delay)
            return self.currPosition

    def get_position(self):
        return self.currPosition

    def get_max_position(self):
        return self.maxPosition

    def get_min_position(self):
        return 0

    def go_to_position(self, newPosition):
        # move motor to position position
        # steps=distance between new position and current position
        steps = newPosition-self.currPosition
        # move lense steps steps
        return self.go_n_steps(steps)

    def go_to_min(self):
        return self.go_to_position(0)

    def go_to_max(self):
        return self.go_to_position(self.maxPosition)

    def enable(self):
        GPIO.output(self.pins[2], False)
        self.status = True
        return True

    def disable(self):
        GPIO.output(self.pins[2], True)
        self.status = False
        return True

    def isEnabled(self):
        return self.status
