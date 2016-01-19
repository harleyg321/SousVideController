#!/bin/python

import serial
import time
import statistics
import math
import datetime

class PID:
	def __init__(self):
		self.output = 0
		self.iterm = 0
		self.setpoint = 0
		self.autoMode = False

		self.setOutputLimits(0, 255)
		self.setTunings(0, 0, 0)

	def setTunings(self, kp, ki, kd):
		self.kp = kp
		self.ki = ki
		self.kd = kd

	def setOutputLimits(self, min, max):
		self.min = min
		self.max = max
		self.restrictOutput()
		self.restrictIterm()

	def compute(self, input):
		if not self.autoMode:
			return False

		now = datetime.datetime.now()
		dt = now-self.lasttime
		dt = dt.seconds*1000 + dt.microseconds/1000
		error =  self.setpoint - input
		dError = (error - self.lasterror)/dt
		self.iterm += self.ki * error
		self.restrictIterm()

		self.output = self.kp * error + self.iterm + self.kd * dError
		self.restrictOutput()

		self.lasterror = error
		self.lasttime = now
		return self.output

	def restrictOutput(self):
		if self.autoMode:
			if (self.output > self.max):
				self.output = self.max
			elif (self.output < self.min):
				self.output = self.min

	def restrictIterm(self):
		if self.autoMode:
			if (self.iterm > self.max):
				self.iterm = self.max
			elif (self.iterm < self.min):
				self.iterm = self.min

	def setAuto(self, mode):
		if (mode and not self.autoMode):
			self.initialise()
		self.autoMode = mode

	def initialise(self):
		self.lasttime = datetime.datetime.now()
		self.iterm = self.output
		self.lastinput = self.output
		self.lasterror = 0
		self.restrictIterm()

	def setTarget(self, setpoint):
		self.setpoint = setpoint

R1 = 10000
R2 = 10000
B = 3380

pid = PID()

pid.setTunings(100,0,0)
pid.setOutputLimits(0, 5000)
pid.setTarget(10)
pid.setAuto(True)

with serial.Serial("/dev/ttyACM0", 115200, timeout=10) as arduino:
	while True:
		median1 = []
		median2 = []
		for i in range(1, 244): # takes approximately 1 second
			arduino.write(b'R\n')
			temps = arduino.readline().decode("UTF-8").splitlines()[0]

			if (temps[0:2] == "T "):
				temps = temps[2:].split(",")
				median1.append(int(temps[0]))
				median2.append(int(temps[1]))

		voltage1 = statistics.median(median1)
		voltage2 = statistics.median(median2)
		resistance1 = R2 * (4095 / voltage1 - 1);
		resistance2 = R2 * (4095 / voltage2 - 1);
		temperature1 = math.log(resistance1 / R1);
		temperature2 = math.log(resistance2 / R1);
		temperature1 /= B;
		temperature2 /= B;
		temperature1 += 1 / (273.15 + 25);
		temperature2 += 1 / (273.15 + 25);
		temperature1 = 1 / temperature1;
		temperature2 = 1 / temperature2;
		temperature1 -= 273.15;
		temperature2 -= 273.15;

		print(pid.compute((temperature1+temperature2)/2))