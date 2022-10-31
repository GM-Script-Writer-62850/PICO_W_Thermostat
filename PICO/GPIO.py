#!/usr/bin/python3
from machine import Pin
from onewire import OneWire
from ds18x20 import DS18X20
from uasyncio import sleep_ms as sleep, run as newProcess
from time import time as time_stamp

class GPIO:
	class matrix:
		#           A  B  C  D  E  F  G
		segments = [ 9,10,11,12,13,14,15]
		digits = [28,27,26,22]
		value = [11,11,11,11]
		input = [7,8]
	class thermostat:
		LED=[0]
		relay=[2,3]
		tube=[4,5]
	class d18b20:
		class error:
			state=False
			error=[]
			time=0
		sensor=DS18X20(OneWire(Pin(1)))
		rom=False
		readTime=750# below 750 is a bad idea
		def setdevice():
			dev=GPIO.d18b20.sensor.scan()
			if len(dev)>0:
				GPIO.d18b20.rom=dev[0]
			return dev
		async def temp(limit=False):
			try:
				GPIO.d18b20.sensor.convert_temp()
				await sleep(GPIO.d18b20.readTime)
				t=GPIO.d18b20.sensor.read_temp(GPIO.d18b20.rom)
				if t == 85:
					# We could compare this to the onboard sensor, but if it is really 85C you have bigger problems than software support for it on a home thermostat
					raise RuntimeError('85 C, I call BS')
				GPIO.d18b20.error.state=False
				return t
			except Exception as e:
				GPIO.d18b20.error.time=time_stamp()
				GPIO.d18b20.error.error=e
				GPIO.d18b20.error.state=True
				if len(GPIO.d18b20.setdevice()) == 0:
					# No data connection
					GPIO.d18b20.error.error=["No D18B20 sensor found"]
					return False# Something wrong, not fixing in software
				elif limit:
					# data, but no power
					return False# Odd we have valid rom and can't get a reading...
				else:
					# rom found, not at recursion limit; try again
					return await GPIO.d18b20.temp(True)
#Could do this, but I like keeping my pins in a row, could skip to 5/6 and leave 4 open...
#	class onboard:
#		sensor=machine.ADC(4)
#		led=machine.ADC('LED',Pin.OUT)
#		def reboot():
#			machine.reset()
#		def temp():
#			temp=GPIO.onboard.sensor.read_u16() * (3.3/65535)
#			temp=27-(temp-0.706)/0.001721

GPIO.d18b20.setdevice()

outs_high=[GPIO.matrix.digits, GPIO.matrix.segments, GPIO.thermostat.LED]
for x in range(len(outs_high)):
	for i in range(len(outs_high[x])):
		outs_high[x][i]=Pin(outs_high[x][i], mode=Pin.OUT)
		outs_high[x][i].value(1)

outs_low=[GPIO.thermostat.relay]
for x in range(len(outs_low)):
	for i in range(len(outs_low[x])):
		outs_low[x][i]=Pin(outs_low[x][i], mode=Pin.OUT)
		outs_low[x][i].value(0)

ins=[GPIO.matrix.input, GPIO.thermostat.tube]
for x in range(len(ins)):
	for i in range(len(ins[x])):
		ins[x][i]=Pin(ins[x][i], mode=Pin.IN, pull=Pin.PULL_DOWN)

del outs_high, outs_low, ins, i, x
