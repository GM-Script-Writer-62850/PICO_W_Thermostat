from math import cos,sin,acos,asin,tan
from math import degrees as deg, radians as rad
from TIME import time
import datetime

# this module is not provided here. See text.


class sun:
 """
 Calculate sunrise and sunset based on equations from NOAA
 http://www.srrb.noaa.gov/highlights/sunrise/calcdetails.html

 typical use, calculating the sunrise at the present day:

 import datetime
 import sunrise
 s = sun(lat=49,long=3)
 print('sunrise at ',s.sunrise(when=datetime.datetime.now())
 """
 def __init__(self,lat=52.37,long=4.9, TzOffset=0): # default Montreal
  self.lat=lat
  self.long=long
  self.TzOffset = TzOffset
  time.tz.set(TzOffset)

 def sunrise(self,when=None):
  """
  return the time of sunrise as a datetime.time object
  when is a datetime.datetime object. If none is given
  a local time zone is assumed (including daylight saving
  if present)
  """
  if when is None : when = datetime.datetime(*time.localtime())
  self.__preptime(when)
  self.__calc()
  return time.gmtime(sun.__timefromdecimalday(self.sunrise_t,when))

 def sunset(self,when=None):
  if when is None : when = datetime.datetime(*time.localtime())
  self.__preptime(when)
  self.__calc()
  return time.gmtime(sun.__timefromdecimalday(self.sunset_t,when))


 def solarnoon(self,when=None):
  if when is None : when = datetime.datetime(*time.localtime())
  self.__preptime(when)
  self.__calc()
  return time.gmtime(sun.__timefromdecimalday(self.solarnoon_t,when))

 @staticmethod
 def __timefromdecimalday(day,when):
  """
  returns a datetime.time object.

  day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5
  """
  hours  = 24.0*day
  h      = int(hours)
  minutes= (hours-h)*60
  m      = int(minutes)
  seconds= (minutes-m)*60
  s      = int(seconds)
  #return time(hour=h,minute=m,second=s)
  CDay = time.localtime(time.mktime((when.year,when.month,when.day,12,0,0,0,0)))# Use noon so time zone changes do not alter the date
  # change hours,min,sec
  #              y       m      d        h       m       s       w      yearday
  #Sun_Day = ( CDay[0], CDay[1],CDay[2],CDay[3],CDay[4],CDay[5],CDay[6],CDay[7])
  Sun_Day = ( CDay[0], CDay[1],CDay[2],h     ,  m,   s,CDay[6],CDay[7])
  return time.mktime(Sun_Day)

 def __preptime(self,when):
  """
  Extract information in a suitable format from when,
  a datetime.datetime object.
  """
  # datetime days are numbered in the Gregorian calendar
  # while the calculations from NOAA are distibuted as
  # OpenOffice spreadsheets with days numbered from
  # 1/1/1900. The difference are those numbers taken for
  # 18/12/2010
  self.day = when.toordinal()-(734124-40529)
  t=when.time()
  self.time= (t.hour + t.minute/60.0 + t.second/3600.0)/24.0

  self.timezone=self.TzOffset

 def __calc(self):
  """
  Perform the actual calculations for sunrise, sunset and
  a number of related quantities.

  The results are stored in the instance variables
  sunrise_t, sunset_t and solarnoon_t
  """
  timezone = self.timezone # in hours, east is positive
  longitude= self.long     # in decimal degrees, east is positive
  latitude = self.lat      # in decimal degrees, north is positive

  time  = self.time # percentage past midnight, i.e. noon  is 0.5
  day      = self.day     # daynumber 1=1/1/1900

  Jday     =day+2415018.5+time-timezone/24 # Julian day
  Jcent    =(Jday-2451545)/36525    # Julian century

  Manom    = 357.52911+Jcent*(35999.05029-0.0001537*Jcent)
  Mlong    = 280.46646+Jcent*(36000.76983+Jcent*0.0003032)%360
  Eccent   = 0.016708634-Jcent*(0.000042037+0.0001537*Jcent)
  Mobliq   = 23+(26+((21.448-Jcent*(46.815+Jcent*(0.00059-Jcent*0.001813))))/60)/60
  obliq    = Mobliq+0.00256*cos(rad(125.04-1934.136*Jcent))
  vary     = tan(rad(obliq/2))*tan(rad(obliq/2))
  Seqcent  = sin(rad(Manom))*(1.914602-Jcent*(0.004817+0.000014*Jcent))+sin(rad(2*Manom))*(0.019993-0.000101*Jcent)+sin(rad(3*Manom))*0.000289
  Struelong= Mlong+Seqcent
  Sapplong = Struelong-0.00569-0.00478*sin(rad(125.04-1934.136*Jcent))
  declination = deg(asin(sin(rad(obliq))*sin(rad(Sapplong))))

  eqtime   = 4*deg(vary*sin(2*rad(Mlong))-2*Eccent*sin(rad(Manom))+4*Eccent*vary*sin(rad(Manom))*cos(2*rad(Mlong))-0.5*vary*vary*sin(4*rad(Mlong))-1.25*Eccent*Eccent*sin(2*rad(Manom)))

  hourangle= deg(acos(cos(rad(90.833))/(cos(rad(latitude))*cos(rad(declination)))-tan(rad(latitude))*tan(rad(declination))))

  self.solarnoon_t=(720-4*longitude-eqtime+timezone*60)/1440
  self.sunrise_t  =self.solarnoon_t-hourangle*4/1440
  self.sunset_t   =self.solarnoon_t+hourangle*4/1440



def ShowTime(info, thetime,us_format):
    Dyear, Dmonth, Dday, Dhour, Dmin, Dsec, Dweekday, Dyearday = thetime
    timeFormat = "{}/{}/{} {}:{:02d}"
    if us_format:
        if Dhour >= 12:
            if Dhour > 12:
                Dhour-=12
            apm="PM"
        else:
            apm="AM"
        print(info," : ",timeFormat.format(Dmonth, Dday, Dyear, Dhour, Dmin,),apm)
    else:
        print(info," : ",timeFormat.format(Dday, Dmonth, Dyear, Dhour, Dmin,))

if __name__ == "__main__":
 import machine
 rtc=machine.RTC()

 s=sun(lat=45.5017,long=-73.5673,TzOffset=-4)
 usa=False # D/M/Y H:M
 usa=True # M/D/Y H:M (AM|PM)
 
 # Set date, if needed
 ognow=time.gmtime()# (year, month, mday, hour, minute, second, weekday, yearday)
 if(ognow[0]<2022):
  # If the year is wrong there is no date set
  #(year, month, day, weekday, hours, minutes, seconds, subseconds),
  rtc.datetime((2022, 10, 16, 6, 13, 11, 30, 0))# current time as of writing
  time.sleep_ms(50)
  now=time.gmtime()
 else:
  now=ognow
 
 print("Test Current Time")
 ShowTime("time now",time.localtime(),usa)
 ShowTime("sunrise",s.sunrise(),usa)
 ShowTime("sunset",s.sunset(),usa)
 
 i=0
 while i < 24:
  rtc.datetime((now[0], now[1], now[2], now[6], i, now[4], now[5], 0))
  time.sleep_ms(50)
  print("\nSimulate:",i*100+100,"UTC 0")
  ShowTime("time now",time.localtime(),usa)
  ShowTime("sunrise",s.sunrise(),usa)
  ShowTime("sunset",s.sunset(),usa)
  i+=1
 rtc.datetime((ognow[0], ognow[1], ognow[2], ognow[6], ognow[3], ognow[4], ognow[5], 0))
 
