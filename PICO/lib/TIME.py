#!/usr/bin/python3
import time as TIME
class time:
	tz=0
	tz_sec=0
	tz_ms=0
	tz_ns=0
	gmtime=TIME.gmtime
	def localtime(t=0):
		if not t:
			t=time.time()
		t+=time.tz_sec
		return TIME.localtime(t)
	mktime=TIME.mktime
	sleep=TIME.sleep
	sleep_ms=TIME.sleep_ms
	ticks_us=TIME.ticks_us
	ticks_cpu=TIME.ticks_cpu
	ticks_add=TIME.ticks_add
	ticks_diff=TIME.ticks_diff
	time=TIME.time
	def time_ms():
		return round(time.time_ns()/1000000)
	time_ns=TIME.time_ns
	def tzset(tz):
		time.tz=int(tz)
		time.tz_sec=time.tz*3600
		time.tz_ms=time.tz_sec*1000
		time.tz_ns=time.tz_ms*1000000
	def format_time(t=0):# local time in US format
		if not t:
			t=time.time()
		t=time.localtime(t)
		#return str(t[2])+"/"+str(t[1])+"/"+str(t[0])+" "+str(t[3])+":"+str(t[4])+":"+str(t[5]) # D/M/Y H:M:S
		date=str(t[1])+'/'+str(t[2])+'/'+str(t[0])
		date+=' '
		if t[3]>=12:
			date+=str(t[3]-(0 if t[3] == 12 else 12))
			m=" PM"
		else:
			date+=str(t[3] if t[3] > 0 else 12)
			m=" AM"
		date+=':'
		if t[4]<10:
			date+='0'
		date+=str(t[4])
		date+=':'
		if t[5]<10:
			date+='0'
		date+=str(t[5])
		date+=m
		return date
