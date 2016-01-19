#!/bin/python

import serial
import time
import statistics

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

		print(statistics.median(median1))