#!/usr/bin/python3
from GPIO import GPIO
from _thread import start_new_thread as newThread
from TIME import time
from random import randrange as rng
from os import stat
from gc import mem_free as fram, collect as clearRAM
from json import dumps as json_encode, loads as json_decode
import ntptime
import uasyncio
import urequest

sleep = uasyncio.sleep_ms
time.tz.set(-5)

#'{"target": 72.5, "format": "F", "auxon": 1, "auxenabled": 1, "enabled": 1, "auxoff": 2, "trigger": 1, "sunset": 30, "night": 0, "day": 0, "sunrise": 90}'

class config:
	class temp:
		temp=0
		min=125
		max=-55
		format="C"
		target=24
		cron=0
		time=0
	class thermostat:
		enabled=1
		auxon=1
		auxoff=1.5
		auxenabled=1
		trigger=0 # cooling (+) / heating (-) / copy (0)
		cycled=0
		saved=0
	class solar:
		sunset=0
		sunrise=0
		day=0 # temp adjustment
		night=0

	remote_ip="10.0.0.69"
	remote_url="http://"+remote_ip+":8081/thermostat/"
	cron=[]
	dst_update=0
#END config

class solar:
	class rise:
		time=""
		hour=0
		minute=0
		stamp=0
	class set:
		time=""
		hour=0
		minute=0
		stamp=0
#END solar

class debug:
	class thermostat:
		onTemp=0
		offTemp=0
		auxOn=0
		auxOff=0
	class solar:
		now=0
		rise=0
		set=0
	class matrix:
		target_F=0
		target_C=0
		format=["C","C"]
	class poweron:
		time=time.time()
#END debug

class logging:
	pending_post=[]
	http_errors=[]
	class clock:
		time_delta=0 # This is used as a backup method of setting the clock
		method="unset"
#END logging

def LED_panel():
	print("LED_panel running")
	# 7 Segment LED layout
	#   A
	# F   B
	#   G
	# E   C
	#   D
	segments=[
		#A B C D E F G
		[0,0,0,0,0,0,1],# 0
		[1,0,0,1,1,1,1],# 1
		[0,0,1,0,0,1,0],# 2
		[0,0,0,0,1,1,0],# 3
		[1,0,0,1,1,0,0],# 4
		[0,1,0,0,1,0,0],# 5
		[1,1,0,0,0,0,0],# 6
		[0,0,0,1,1,1,1],# 7
		[0,0,0,0,0,0,0],# 8
		[0,0,0,1,1,0,0],# 9
		[1,1,1,1,1,1,0],# -
		[1,1,1,1,1,1,1],# blank
		[0,0,0,1,0,0,0],# A
		[0,1,1,0,0,0,1],# C
		[0,1,1,0,0,0,0],# E
		[0,1,1,1,0,0,0],# F
		[1,0,0,0,0,1,1],# J
		[1,1,1,0,0,0,1],# L
		[0,0,1,1,0,0,0],# P
		[1,0,0,0,0,0,1] # U
		#A B C D E F G
	]

	then=3
	now=0
	while True:
		then=now
		now=then+1
		if now>3:
			now=0
		GPIO.matrix.digits[then].value(1)
		ct=0
		for i in segments[GPIO.matrix.value[now]]:
			GPIO.matrix.segments[ct].value(i)
			ct=ct+1
		GPIO.matrix.digits[now].value(0)
		time.sleep_ms(7)
#END LED_panel()

def file_exists(filename):
	try:
		return (stat(filename)[0] & 0x4000) == 0
	except OSError:
		return False
#END file_exists()

def post(json,comment=""):
	async def send(json,comment):
		# This is deferred till next sleep period
		if not json:
			json=json_encode(logging.pending_post)
			logging.pending_post=[]
		r=urequest.post(config.remote_url,data=json,headers={"Content-type":"application/json"})
		if r.status_code != 200:
			print("------ERROR------")
			logging.http_errors.append({
				"error":r.status_code,
				"message":r.content,
				"data":json
			})
			if len(logging.http_errors) > 4:
				logging.http_errors.pop(0)
		print(comment,r.status_code,"-", r.content)
		r.close()
	if not isinstance(json, str):# comment == "appendLog:"
		logging.pending_post.append(json)
		if len(logging.pending_post) > 1:
			return
		json=False
	uasyncio.create_task(send(json,comment))
#END post()


async def read_temp(delay):
	temp=await GPIO.d18b20.temp()
	while GPIO.d18b20.error.state == True:
		setPanel("EE",True)
		updateTarget("CP")
		copyTubes(False)
		await sleep(delay-GPIO.d18b20.readTime)
		temp=await GPIO.d18b20.temp()
	temp=float(temp)
	#print(temp)
	if debug.matrix.format[0] != config.temp.format:
		config.temp.temp=-273.16 # force update as format changed (Absolute 0 is -237.15 C)
		debug.matrix.format[0] = config.temp.format
	config.temp.time=time.time()
	if config.temp.temp!=temp:
		config.temp.temp=temp
		if config.temp.min > config.temp.temp:
			config.temp.min=config.temp.temp
		if config.temp.max < config.temp.temp:
			config.temp.max=config.temp.temp
		if config.temp.format=="F":
			temp=temp*1.8+32
		setPanel(temp,True)
#END read_temp()

def appendLog(mode):
	log={
		"time":time.time(),
		"mode":mode,
		"temp":config.temp.temp,
		"relays":[
			GPIO.thermostat.relay[0].value(),
			GPIO.thermostat.relay[1].value()
		],
		#"tubes":[
		#	GPIO.thermostat.tube[0].value(),
		#	GPIO.thermostat.tube[1].value()
		#],
		"saved":config.thermostat.saved
	}
	print(log)
	post(log,"appendLog:")
#END appendLog()

def copyTubes(good=True):
	if GPIO.thermostat.relay[0].value() != GPIO.thermostat.tube[0].value() or GPIO.thermostat.relay[1].value() != GPIO.thermostat.tube[1].value():
		GPIO.thermostat.relay[0].value(GPIO.thermostat.tube[0].value())
		GPIO.thermostat.relay[1].value(GPIO.thermostat.tube[1].value())
		appendLog(2)
	if not good:# problem found, distress signal
		GPIO.thermostat.LED[0].toggle()
#END copyTubes()

async def getSolar():
	import sunTime
	from gps_cords import LONGITUDE, LATITUDE

	class TZ:# used to convert time stamp from local to UTC
		delta=-time.tz.sec
		delta_dst=-time.tz.sec-time.dst.offset

	while True:
		if time.dst.start <= time.time()+3600 <= time.dst.end:# check for DST after 2AM
			TIMEZONE_DIFFERENCE=TZ.delta_dst
		else:
			TIMEZONE_DIFFERENCE=TZ.delta
		sunTime.time.dst.start=time.dst.start
		sunTime.time.dst.end=time.dst.end
		sun = sunTime.sun(lat=LATITUDE,long=LONGITUDE,TzOffset=time.tz.hr)
		sunrise = sun.sunrise()
		sunset = sun.sunset()
		solar.rise.time=str(sunrise[3])+":"+f'{sunrise[4]:02}'+" AM"
		solar.rise.hour=sunrise[3]
		solar.rise.minute=sunrise[4]
		solar.rise.stamp=time.mktime(sunrise)+TIMEZONE_DIFFERENCE
		solar.set.time=str(sunset[3]-12)+":"+f'{sunset[4]:02}'+" PM"
		solar.set.hour=sunset[3]
		solar.set.minute=sunset[4]
		solar.set.stamp=time.mktime(sunset)+TIMEZONE_DIFFERENCE

		print("Solar events set: { rise : '",solar.rise.time,"', set: '",solar.set.time,"' }")

		now=time.localtime()
		then=(now[0],now[1],now[2],23,59,59,now[6],now[7])
		then=time.mktime(then)+3601
		now=time.mktime(now)

		await uasyncio.sleep(then-now) # Tomorrow after 1AM
#END getSolar()

async def getDST():
	def long_sleep(seconds):
		# uasyncio.sleep(sec); sec*1000 must be under the 32bit limit of 2,147,483,647
		while seconds > 2000000:
			await uasyncio.sleep(2000000)
			seconds -= 2000000
		await uasyncio.sleep(seconds)

	await long_sleep(config.dst_update-time.time())
	while True:
		r=urequest.get(config.remote_url+"?dst")
		if r.status_code != 200:
			await sleep(10000)
			continue
		data=json_decode(r.content)
		time.dst.start=data['start']
		time.dst.end=data['end']
		config.dst_update=data['update']

		await long_sleep(data['update']-time.time()) #Jan 1 at 2AM
#END getDST()

def updateTarget(on):
	# not using async intentionally
	if debug.matrix.target_C != on or debug.matrix.format[1] != config.temp.format:
		# update needed
		debug.matrix.target_C=on
		debug.matrix.format[1]=config.temp.format
		if debug.matrix.format[1]=="F" and not isinstance(on, str):
			on=on*1.8+32
			debug.matrix.target_F=on
		setPanel(on)
	if GPIO.matrix.input[0].value() or GPIO.matrix.input[1].value():
		# user input, locking out web ui access for this by not using async
		if isinstance(on, str):
			while GPIO.matrix.input[0].value() or GPIO.matrix.input[1].value():
				if GPIO.matrix.value[2]==14:# if 1st char == E
					setPanel(" E")
				else:
					setPanel("E ")
				time.sleep_ms(500)
			setPanel(on)
			return
		adj=[0,1]# [adjustment, increment]
		if config.temp.format=="F":
			adj[1]=0.55556
			on=debug.matrix.target_F
		on=round(on)
		while GPIO.matrix.input[0].value() or GPIO.matrix.input[1].value():
			if GPIO.matrix.input[1].value():
				on+=1
				adj[0]+=adj[1]
			else:
				on-=1
				adj[0]-=adj[1]
			setPanel(on)
			time.sleep(1)
		if adj[0] != 0:
			config.temp.target+=adj[0]
			config.thermostat.saved=time.time()
			config.thermostat.enabled=1
			post(json_encode({"target":config.temp.target}),"Update backup config data:")
#END updateTarget()

def setPanel(val,isTemp=False):
	def strInt(i):
		if i == "-":
			return 10
		elif i == " " or i == "":
			return 11
		elif i == "A":
			return 12
		elif i == "C":
			return 13
		elif i == "E":
			return 14
		elif i == "F":
			return 15
		elif i == "J":
			return 16
		elif i == "L":
			return 17
		elif i == "P":
			return 18
		elif i == "U":
			return 19
		return int(i)
	if not isinstance(val, str):
		val=str(round(val))
	if isTemp:
		GPIO.matrix.value[0]=strInt(val[0])
		GPIO.matrix.value[1]=strInt(val[1])
	else:
		GPIO.matrix.value[2]=strInt(val[0])
		GPIO.matrix.value[3]=strInt(val[1])
#END setPanel()

async def thermostat(delay):
	def getOffset(onlySolar=False):
		cronOffset=0
		if not onlySolar:
			#getCronOffset
			now=time.localtime()
			today=now[6]# day of week; 0 = Monday
			sec=now[3]*60+int(now[4])# Current Hour*60+Minute

			for evt in config.cron:
				if(evt["enable"]):
					if today in evt["days"]:
						start=evt["time"]["start"]["h"]*60+evt["time"]["start"]["m"]
						end=evt["time"]["end"]["h"]*60+evt["time"]["end"]["m"]
						if sec >= start and sec <= end:
							cronOffset+=evt["offset"]
			config.temp.cron=cronOffset
		#getSolarOffset
		debug.solar.now=time.time()
		debug.solar.rise=solar.rise.stamp+config.solar.sunrise
		debug.solar.set=solar.set.stamp+config.solar.sunset
		if debug.solar.now > debug.solar.rise and debug.solar.now < debug.solar.set:
			GPIO.thermostat.LED[0].value(1)
			return config.solar.day+cronOffset
		GPIO.thermostat.LED[0].value(0)

		return config.solar.night+cronOffset
	#END getOffset()

	def setOnOff():
		debug.thermostat.offTemp=config.temp.target+getOffset()
		debug.thermostat.onTemp=debug.thermostat.offTemp+config.thermostat.trigger
		return (debug.thermostat.onTemp, debug.thermostat.offTemp)

	while True:
		await read_temp(delay)
		onTemp, offTemp = setOnOff()
		#print("On @",onTemp,"and Off @",offTemp,"; if = CP mode is used")
		if config.thermostat.trigger > 0: # Cooling
			#print('Cool mode | temp:',config.temp.temp,"| on:",onTemp,"| off:",offTemp)
			GPIO.thermostat.relay[1].value(0) # Only used for heating
			if onTemp <= config.temp.temp and config.thermostat.enabled == 1:
				#print('Cool | temp:',config.temp.temp,"| on:",onTemp,"| off:",offTemp)
				updateTarget(offTemp)
				GPIO.thermostat.relay[0].value(1) # Start cooling
				appendLog(0)
				while config.temp.temp >= offTemp and config.thermostat.enabled == 1: # Keep cooling
					#print('More Cool | temp:',config.temp.temp,"| on:",onTemp,"| off:",offTemp)
					updateTarget(offTemp)
					await sleep(delay)
					await read_temp(delay)
					onTemp, offTemp = setOnOff()
					#print("Off @",offTemp)
					if config.thermostat.trigger <= 0:
						break
				GPIO.thermostat.relay[0].value(0) # Stop cooling
				appendLog(0)
			else:
				#print('No Cool',onTemp,offTemp)
				GPIO.thermostat.relay[0].value(0) # Do not cool
				updateTarget(onTemp)
		elif config.thermostat.trigger < 0 : # Heating
			#print('Heat mode | temp:',config.temp.temp,"| on:",onTemp,"| off:",offTemp)
			if onTemp >= config.temp.temp and config.thermostat.enabled == 1:
				#print('Heat | temp:',config.temp.temp,"| on:",onTemp,"| off:",offTemp)
				updateTarget(offTemp)
				GPIO.thermostat.relay[0].value(0) # Heat
				appendLog(1)
				cycled=0
				Otemp=0 # temp aux heat turned off
				while config.temp.temp <= offTemp and config.thermostat.enabled == 1: # Keep heating
					updateTarget(offTemp)
					auxOn=onTemp-config.thermostat.auxon
					auxOff=auxOn+config.thermostat.auxoff
					debug.thermostat.auxOn=auxOn
					debug.thermostat.auxOff=auxOff
					#print('More heat | temp=',config.temp.temp,"; on=",onTemp,"; off=",offTemp,"; On2=",auxOn,"; Off2=",auxOff)
					#print("auxOn @",auxOn," and auxOff @",auxOff, 'and cycled =',cycled)
					if cycled == 1 and config.temp.temp <= Otemp-0.26: # Aux shut off and temp fell 0.26C (~0.5F) while the heat was running, better turn it on and keep it on
						cycled=2
					if (config.temp.temp <= auxOn or cycled == 2 ) and config.thermostat.auxenabled == 1:
						if GPIO.thermostat.relay[1].value() == 0:
							GPIO.thermostat.relay[1].value(1) # Need more heat
							appendLog(1)
					elif config.temp.temp >= auxOff or config.thermostat.auxenabled == 0:
						if GPIO.thermostat.relay[1].value() == 1:
							Otemp=config.temp.temp
							cycled+=1
							GPIO.thermostat.relay[1].value(0) # Heat slower
							appendLog(1)
					if cycled == 1 and temp > Otemp: # Lets not waist the heat we just got via Aux
						Otemp=config.temp.temp
					await sleep(delay)
					await read_temp(delay)
					onTemp, offTemp = setOnOff()
					#print("Off @",offTemp)
					if config.thermostat.trigger >= 0:
						break
				GPIO.thermostat.relay[1].value(0) # Stop Heating
				GPIO.thermostat.relay[0].value(1) # Stop Heating
				appendLog(1)
			else: # Do not heat
				GPIO.thermostat.relay[1].value(0)
				GPIO.thermostat.relay[0].value(1)
				updateTarget(onTemp)
		else:
			#print("Copy Cat Mode")
			while config.thermostat.trigger == 0:
				updateTarget("CP")
				copyTubes()
				getOffset(True)# need to keep night light LED working
				await sleep(delay)
				await read_temp(delay)
		await sleep(delay)
#END thermostat()

async def wait4clock():
	delay=2000
	updateTarget("CP")
	print("Waiting for clock")
	while time.time() < 1640995200: # Wait for clock to set or a 1 year...)
		updateTarget("CP")
		copyTubes(False)
		await read_temp(delay)
		await sleep(delay-GPIO.d18b20.readTime)
	print('Clock set:',time.time(),"aka",time.format_time())
	solar=uasyncio.create_task(getSolar())
	print("Solar loop started")
	thermo=uasyncio.create_task(thermostat(delay))
	print("Thermostat loop started")
#END wait4clock()

async def wifi():
	from wifi_auth import ssid, password
	import network

	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	wlan.config(pm = 0xa11140)# Power management is very very bad, ping time is around 1000x worse and packet loss insane
	wlan.connect(ssid, password)

	while True:
		wstat=wlan.status()
		if wstat < 0 or wstat >= 3:
			break
		print('Waiting for WiFi connection...')
		await sleep(1000)

	if wlan.status() != 3:
		raise RuntimeError('Network connection failed!')
	else:
		print('Connected')
		status = wlan.ifconfig()
		print('ip =',status[0])
	return print('WiFi setup')
#END wifi()

async def setTime(loop=0):
	#ntptime.settime() failure: [Errno 110] ETIMEDOUT
	#ntptime.settime() failure: overflow converting long int to machine word
	try:
		if loop<5:
			d=time.time()-debug.poweron.time
			ntptime.settime()
			debug.poweron.time=time.time()-d
			logging.clock.method="accurate"
		else:
			# if it did not work the second time it is not going to in my testing
			print("Failed to set time; Waiting 15 seconds")
			await sleep(15000)
			if logging.clock.time_delta:
				# If I do not have this by now something is very wrong
				# WiFi is working, therefore my server is up and has configured settings
				print("Setting clock using low precision method")
				from machine import RTC
				d=time.time()-debug.poweron.time
				t=time.gmtime(time.time()+logging.clock.time_delta)
				RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
				debug.poweron.time=time.time()-d
				print("Result:",debugData(time.time()))
				logging.clock.method="low precision"
			else:
				# So lets get this strait:
				# The server's Guest OS (pfsense) has asigned a IP to us over WiFi
				# The server host is unrechable
				# How is that even possible
				print("Rebooting in 15 seconds, failed to set clock")
				await sleep(15000)
				from machine import reset
				reset()
	except OverflowError:
		# it is not going to work
		print("overflow error; settime is borked")
		await setTime(9001)
	except OSError:
		print("ntptime.settime() failure")
		if loop>0:
			# Not expecting more than 1 failure, maybe waiting will help?
			await sleep(10000)
		await setTime(loop+1)
#END setTime()

def debugData(data,sub=False):
	if not sub:
		sub={}
	if data > 5500:# date (lets assume the temp reading not over the surface temp of the sun)
		sub["stamp"]=data
		sub["date"]=time.format_time(data)
	else:# temp
		sub["C"]=data
		sub["F"]=data*1.8+32
	return sub
#END debugData()

async def webUI(reader, writer):
	request_line = await reader.readline()
	print("\nClient connected:",request_line)
	if(request_line == b""):
		writer.write('HTTP/1.0 204 No Content')# is this right?
		await writer.drain()
		await writer.wait_closed()
		return print("Disconnect")

	# We are not interested in HTTP request headers, skip them
	export=False
	accept=''
	length=0
	header=await reader.readline()
	while header != b"\r\n":
		if(header != b""):
			line=header.decode("utf-8")
			if line[0:16] == "Accept-Encoding:":
				accept=line[16:]
				print("Client accepting:",accept)
			elif line[0:15] == "Content-Length:":
				length=int(line[15:])
				print("Content length:",length)
			else:
				pass#print('Ignore header:',line)
		header=await reader.readline()

	request=request_line.decode("utf-8").split(' ')
	if request[0]=="GET":
		# The commented out code is to parse GET parameters and store them in a dict for easy access
		# I do not care about these and only use them client side to break cache by force
		# as such I do not need that code burning CPU cycles so it is commented out
		# be aware this does not decode uri encoded strings (eg space will be %20)
		# I am only stripping the url so i can use endswith instead of find as i would expect it be faster
		q=request[1].find('?')
		#params={}
		if q > 0:
			# This is to strip get parameters from url
			file=request[1][0:q]
			#q+=1
			#parameters=request[1][q:].split('&')
			#for i in parameters:
			#	if not i:
			#		continue
			#	param=params[i].split('=')
			#	params[param[0]]=None if len(param) == 1 else param[1]
			#print("Client set parameters:",params)
		else:
			file=request[1]

		if not file or file == "/":
			file = "/index.html"
		elif file == "/favicon.ico":
			file = "/style/images/favicon.png"

		file='www'+file
		print("Client asked for:",file)
		if file_exists(file):
			# Security note: Only thing stopping users from reading files outside of /www is the lack of a mime type below

			header='HTTP/1.0 200 OK\r\nContent-type: '
			if file.endswith('.html'):
				header+='text/html'
			elif file.endswith('.css'):
				header+='text/css'
			elif file.endswith('.js'):
				header+='application/javascript'
			elif file.endswith('.webp'):
				header+='image/webp'
			elif file.endswith('.gif'):
				header+='image/gif'
			elif file.endswith('.png'):
				header+='image/png'
			elif file.endswith('.jpg'):
				header+='image/jpeg'
			else:
				print('Not Implemented:', file,'\n')
				writer.write(header+'text/plain\r\n\r\nFile type not implemented')
				await writer.drain()
				await writer.wait_closed()
				print('Closed connection')
				return

			if file_exists(file+'.gz') and accept.find('gzip')>-1:
				compress=file
				file+='.gz'
				header+='\r\nContent-Encoding: gzip'
			else:
				compress=False
			clearRAM()
			s=1024# chunk size
			size=stat(file)[6]
			print('Open',file,'(',size,') with', fram())
			if(s*10 < fram()): # As long as we have over 10x the chunk size in ram (should never be that low)
				writer.write(header+
					'\r\nContent-Language: pt-BR\r\nCache-Control: max-age='+str(rng(604800,1209600))+'\r\n'+
					'Content-Length:'+str(size)+
					'\r\n\r\n'
				)
				with open(file, 'rb') as f:
					buf = memoryview(bytearray(s))
					while(c := f.readinto(buf)):
						await writer.drain()
						writer.write(buf if c == s else buf[:c])
				del(buf,c,f,s,size)
				print("File closed; free RAM:",fram())
			else:
				# This is gonna be a issue if it happens to index.html
				print("Low Ram: Offload",file,"to alt server")
				if compress != False:
					file=compress
				writer.write('HTTP/1.0 307 Temporary Redirect\r\nLocation: '+config.remote_url+file[4:])
		elif file.endswith('.json'):
			print('Emulate:',file)
			if file == "www/temp.json":
				json=json_encode({
					"temp":config.temp.temp,
					"age":config.temp.time,
					"cron":config.temp.cron,
					"tube1":GPIO.thermostat.tube[0].value(),
					"tube2":GPIO.thermostat.tube[1].value(),
					"relay1":GPIO.thermostat.relay[0].value(),
					"relay2":GPIO.thermostat.relay[1].value(),
					"cycled":config.thermostat.cycled
				})
			elif file == "www/config.json":
				json=json_encode({
					"target": config.temp.target,
					"format": config.temp.format,
					"auxon": config.thermostat.auxon,
					"auxenabled": config.thermostat.auxenabled,
					"enabled": config.thermostat.enabled,
					"auxoff": config.thermostat.auxoff,
					"trigger": config.thermostat.trigger,
					"sunset": config.solar.sunset/60,
					"night": config.solar.night,
					"day": config.solar.day,
					"sunrise": config.solar.sunrise/60
				})
			elif file == "www/sun.json":
				json=json_encode({
					"rise":{
						"time":solar.rise.time,
						"hour":solar.rise.hour,
						"minute":solar.rise.minute,
						"stamp":solar.rise.stamp
					},
					"set":{
						"time":solar.set.time,
						"hour":solar.set.hour,
						"minute":solar.set.minute,
						"stamp":solar.set.stamp
					}
				})
			elif file == "www/cron.json":
				json=json_encode(config.cron)
			elif file == "www/error.json":
				json=json=json_encode({
					"error":GPIO.d18b20.error.error,
					"time":False if not GPIO.d18b20.error.time else debugData(GPIO.d18b20.error.time),
					"is_error":GPIO.d18b20.error.state,
					"now":debugData(time.time())
				})
			elif file == "www/debug.json":
				# There is no link for this in the UI it is for admins only
				json=json_encode({
					"temperatures":{
						"sensor":{
							"reading":debugData(config.temp.temp),
							"min":debugData(config.temp.min),
							"max":debugData(config.temp.max),
							"time":debugData(config.temp.time),
							"error":{
								"time":False if not GPIO.d18b20.error.time else debugData(GPIO.d18b20.error.time),
								"error":GPIO.d18b20.error.error,
								"is_error":GPIO.d18b20.error.state
							}
						},
						"target":debugData(config.temp.target),
						"switches":{
							"on":debugData(debug.thermostat.onTemp,{"aux":debugData(debug.thermostat.auxOn)}),
							"off":debugData(debug.thermostat.offTemp,{"aux":debugData(debug.thermostat.auxOff)}),
						},
						"offsets":{
							"trigger": config.thermostat.trigger,
							"cron":config.temp.cron,
							"day":config.solar.day,
							"night":config.solar.night,
							"auxon":config.thermostat.auxon,
							"auxoff":config.thermostat.auxoff
						},
						"matrix_target":{
							"F":debug.matrix.target_F,
							"C":debug.matrix.target_C
						}
					},
					"gpio":{
						"top_tube":bool(GPIO.thermostat.tube[0].value()),
						"top_relay":bool(GPIO.thermostat.relay[0].value()),
						"bottom_tube":bool(GPIO.thermostat.tube[1].value()),
						"bottom_relay":bool(GPIO.thermostat.relay[1].value()),
						"led":not GPIO.thermostat.LED[0].value()# 0=on;1=off
					},
					"DST":{
						"start":debugData(time.dst.start),
						"end":debugData(time.dst.end),
						"update":debugData(config.dst_update)
					},
					"solar":{
						"config":{
							"rise":{
								"time":solar.rise.time,
								"date":debugData(solar.rise.stamp),
								"offset":config.solar.sunrise
							},
							"set":{
								"time":solar.set.time,
								"date":debugData(solar.set.stamp),
								"offset":config.solar.sunset
							},
						},
						"adjusted":{
							"rise":debugData(debug.solar.rise),
							"set":debugData(debug.solar.set),
							"now":debugData(debug.solar.now)
						}
					},
					"debug":{
						"time":debugData(time.time()),
						"poweron":debugData(debug.poweron.time),
						"uptime":time.time()-debug.poweron.time,
						"post_errors":logging.http_errors,
						"clock_set":logging.clock.method
					},
					"config":{
						"enabled": config.thermostat.enabled,
						"client_temp_format":config.temp.format,
						"aux":{
							"enabled": config.thermostat.auxenabled,
							"cycled":config.thermostat.cycled
						},
						"saved":config.thermostat.saved
					},
					"matrix":{
						"digits":GPIO.matrix.value,
						"format":debug.matrix.format
					}
				})
			else:
				json='{"Error":"File not implemented, typo?"}'
			writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\nContent-Length: '+str(len(json))+'\r\nCache-Control: no-cache\r\n\r\n'+json)
		elif file == 'www/logView.php':
			writer.write('HTTP/1.0 308 Permanent Redirect\r\nLocation: '+config.remote_url)
		elif file == "www/rebootNOW.py":
			# There is no link for this in the UI it is for admins only
			from machine import reset
			message="Good bye cruel world\nI was "+str(time.time()-debug.poweron.time)+" second(s) old..."
			writer.write('HTTP/1.0 200 OK\r\nContent-type: text/plain\r\nContent-Length: '+str(len(message))+'\r\nCache-Control: no-cache\r\n\r\n'+message)
			await writer.drain()
			await writer.wait_closed()
			await sleep(500)
			reset()# RIP
		else:
			print('404 Error',file)
			writer.write('HTTP/1.0 404 NOT FOUND\r\nContent-type: text/html\r\n\r\n<html><head><title>404 Error</title></head><body>404 File not found</body></html>')
	elif request[0]=="POST":
		data=await reader.readexactly(length)
		data=data.decode("utf-8")
		data=json_decode(data)
		if 'format' in data:
			config.temp.format=data['format']
		if 'target' in data:
			config.temp.target=float(data['target'])
			config.thermostat.saved=time.time()
		if 'trigger' in data:
			config.thermostat.trigger=float(data['trigger'])
		if 'enabled' in data:
			config.thermostat.enabled=int(data['enabled'])
		if 'auxenabled' in data:
			config.thermostat.auxenabled=int(data['auxenabled'])
		if 'auxon' in data:
			config.thermostat.auxon=float(data['auxon'])
		if 'auxoff' in data:
			config.thermostat.auxoff=float(data['auxoff'])
		if 'sunrise' in data:
			config.solar.sunrise=int(data['sunrise'])*60
		if 'sunset' in data:
			config.solar.sunset=int(data['sunset'])*60
		if 'day' in data:
			config.solar.day=float(data['day'])
		if 'night' in data:
			config.solar.day=float(data['night'])
		if 'cron' in data:
			config.cron=data['cron']
		if 'dst' in data:
			time.dst.start=data['dst']['start']
			time.dst.end=data['dst']['end']
			config.dst_update=data['dst']['update']
		if 'noexport' in data:# noexport is only sent by 10.0.0.69 when restoring settings
			logging.clock.time_delta=data['noexport']-time.time()
			writer.write('HTTP/1.0 200 OK\r\nContent-type: text/plain\r\nContent-Length: 2\r\nCache-Control: no-cache\r\n\r\nOK')
		else:
			export=True
			data=json_encode(data)
			writer.write('HTTP/1.0 200 OK\r\nContent-type: application/json\r\nContent-Length: '+str(len(data))+'\r\nCache-Control: no-cache\r\n\r\n'+data)
	try:
		await writer.drain()
		await writer.wait_closed()
		print("Client disconnected")
	except Exception as e:
		print("Error:",e)
	if export:
		post(data,"Update backup config data:")
#END webUI()

async def main():
	def requestConfig():
		while True:
			if config.thermostat.saved:
				break
			r=urequest.get(config.remote_url+"?firstboot")
			print("Notified server we are up and running:",r.status_code,"-",r.content)
			if r.content==b"OK" and r.status_code == 200:
				break
			await sleep(5000)
	print("main started")
	uasyncio.create_task(wait4clock())
	await wifi()
	uasyncio.create_task(uasyncio.start_server(webUI, "0.0.0.0", 80))
	print('Started Web UI')

	uasyncio.create_task(requestConfig())

	await sleep(250)
	ntptime.host = config.remote_ip
	await setTime()

	while time.dst.start == time.dst.end:
		await sleep(1000)
	uasyncio.create_task(getDST())

	while 1:
		await sleep(86400000)# 1 day
#END main()

newThread(LED_panel,())
try:
	uasyncio.run(main())
except KeyboardInterrupt:
	#Reset clock
	from machine import RTC
	RTC().datetime((2021, 1, 1, 4, 0, 0, 19, 0))
except Exception as e:
	print("----ERROR----\n",e)
