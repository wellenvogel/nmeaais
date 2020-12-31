#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=2 sw=2 et ai
###############################################################################
# Copyright (c) 2020 Andreas Vogel andreas@wellenvogel.net
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#
###############################################################################
import getopt
import socket
import sys
#install python-bitstring (pip install bitstring)
import threading
import time
import traceback

import pythonais.aislib as aislib
#install python-nmea2 (or pip install pynmea2)
import pynmea2
#install python-serial (pip install pyserial)
import serial

import geo

doDebug=0

def debug(txt):
  if doDebug > 0:
    print("##%s"%txt)

def getShiptype(typev):
  if typev is None:
    return 0
  try:
    tn=int(typev)
    return tn
  except:
    pass
  typev=typev.lower()
  if typev == 'wig':
    return 20
  if typev == 'fishing':
    return 30
  if typev == 'towing':
    return 31
  if typev == 'dredging':
    return 33
  if typev == 'diving':
    return 34
  if typev == 'military':
    return 35
  if typev == 'sail':
    return 36
  if typev == 'pleasure':
    return 37
  if typev == 'hsc':
    return 40
  if typev == 'pilot':
    return 50
  if typev == 'sar':
    return 51
  if typev == 'tug':
    return 52
  if typev == 'tender':
    return 53
  if type == 'law':
    return 55
  if typev == 'passenger':
    return 60
  if typev == 'cargo':
    return 70
  if typev == 'tanker':
    return 80
  if typev == 'other':
    return 90
  return 0
def filterString(str):
  if str is None:
    return ""
  str=str.upper()
  return ''.join(c for c in str if c in aislib.AISchars)

class Reader:
  def open(self):
    raise Exception("not implemented")
  def readline(self):
    raise Exception("not implemented")
class SerialReader(Reader):
  def __init__(self,port,baud):
    try:	
      self.port=int(port)
    except:
        self.port=port
    self.baud=baud
    self.ser=None

  def open(self):
    self.ser=serial.Serial(self.port, self.baud, timeout=5.0,xonxoff=True)

  def readline(self):
    if self.ser is None:
      raise Exception("serial not open")
    return self.ser.readline()

class SocketReader(Reader):
  def __init__(self,host,port):
    self.host=host
    self.port=port
    self.socket=None
    self.lines=[]
    self.buffer=''

  def open(self):
    self.socket=socket.create_connection((self.host, int(self.port)),timeout=20)

  def readline(self):
    if self.socket is None:
      raise Exception("socket not open")
    if len(self.lines) > 0:
      return self.lines.pop(0)
    while True:
      data = self.socket.recv(1024)
      if len(data) == 0:
        raise Exception("connection lost")
      self.buffer = self.buffer + data.decode('ascii', 'ignore')
      self.lines = self.buffer.splitlines(True)
      if self.lines[-1][-1] == '\n':
        self.buffer = ''
        return self.lines.pop(0)
      else:
        self.buffer=self.lines[-1]
        self.lines.pop()
        if len(self.lines) > 0:
          return self.lines.pop(0)


def createReader(input):
  ipopt = input.split(":")
  if len(ipopt) != 3:
    raise Exception("invalid input %s" % input)
  if ipopt[0] == 'ser':
    return SerialReader(ipopt[1],ipopt[2])
  if ipopt[0] == 'tcp':
    return SocketReader(ipopt[1],ipopt[2])
  raise Exception("unknown input type")

class Writer:
  def send(self,data):
    raise Exception("not implemented")
  def open(self):
    raise Exception("not implemented")
class UdpWriter(Writer):
  def __init__(self,host,port):
    self.host=host
    self.port=int(port)
    self.socket=None

  def open(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  def send(self,data):
    if self.socket is None:
      raise Exception("socket not open")
    self.socket.sendto(data, (self.host, self.port))

def createOutput(output):
  opopt = output.split(":")
  if len(opopt) != 3:
    raise Exception("invalid output %s" % output)
  if opopt[0] != 'udp':
    raise Exception("unknown output type %s"%output)
  return UdpWriter(opopt[1],opopt[2])

class Average:
  def __init__(self,len,iv=0):
    self.len=len
    self.array=[]
    self.sum=iv
    self.iv=iv

  def add(self,val):
    self.sum=self.sum+val
    self.array.append(val)
    if len(self.array) > self.len:
      ov=self.array.pop(0)
      self.sum=self.sum-ov

  def cur(self):
    if len(self.array) < 1:
      return self.sum
    return self.sum/len(self.array)

  def filled(self):
    return len(self.array) >= self.len

  def reset(self):
    self.array=[]
    self.sum=self.iv

class NmeaToAis:
  MMSI_DEFAULT=333333333
  SHIPTYPE='other'
  FIRST_NAME='SONDE'
  SECOND_NAME="LANDUNG"
  def __init__(self,input,output):
    self.input=input
    self.output=output
    self.bearingFromCourse=False
    self.positionInput=None
    self.positionThread=None
    self.aisoptions={}
    self.tryForever=False
    self.altitude=0
    self.lastAltitude=None
    self.ownPosition=None
    self.ownPostionTimeout=60
    self.averageLen=1
    self.minAltDiff=10
    self.minPosDiff=50
    self.maxNonCompute=20

  def readOwnPosition(self):
    print("own position reader started for %s"%self.positionInput)
    positionReader = None
    minPrintDiff=5
    lastPrinted=None
    while True:
      hasData=False
      try:
        positionReader = createReader(self.positionInput)
        positionReader.open()
        print("own position reader opened %s"%self.positionInput)
        while True:
          line = positionReader.readline()
          if self.lastAltitude is not None and time.time() > (self.lastAltitude+self.ownPostionTimeout):
            if hasData:
              print("lost own altitude")
              hasData=False
          if not line.startswith("$"):
            continue
          msg = pynmea2.parse(line)
          debug("own position msg: %s" % (type(msg)))
          if isinstance(msg, pynmea2.GGA):
            altitude = msg.altitude
            if altitude is not None:
              diff=minPrintDiff+1
              if lastPrinted is not None:
                diff=abs(lastPrinted-altitude)
              self.altitude=altitude
              self.lastAltitude=time.time()
              if not hasData or diff > minPrintDiff:
                print("OwnPosition altitude=%f" % (msg.altitude))
                lastPrinted=altitude
                hasData = True
              else:
                debug("OwnPosition altitude=%f" % (msg.altitude))
          if isinstance(msg, pynmea2.LatLonFix):
            self.ownPosition=[msg.longitude,msg.latitude]
      except Exception as e:
        print("Exception in reading own position: %s"%unicode(e))
      time.sleep(2)

  def getAisOption(self,name,second,default=None):
    suffix="" if not second else "2"
    rt=self.aisoptions.get(name+suffix)
    if rt is None:
      return default
    return rt

  def sendAisMessages(self,writer,second,longitude,latitude,speed,course,altitude):
    mmsi = int(self.getAisOption('mmsi', second, self.MMSI_DEFAULT if not second else self.MMSI_DEFAULT+1))
    aismsg = aislib.AISPositionReportMessage(
      mmsi=mmsi,
      status=0,
      sog=int((speed or 0) * 10),
      pa=1,
      lon=int(longitude * 600000.0),
      lat=int(latitude * 600000.0),
      cog=int((course or 0) * 10),
      ts=0,
      raim=1,
      comm_state=82419
    )
    ais = aislib.AIS(aismsg)
    payload = ais.build_payload(False)
    debug("!!%s" % payload)
    writer.send(payload + "\n")
    aismsg = aislib.AISStaticAndVoyageReportMessage(
      mmsi=mmsi,
      callsign=filterString(self.getAisOption('callsign', second)),
      destination=filterString(self.getAisOption('destination', second) or "alt=%d" % int(altitude)),
      shiptype=getShiptype(self.getAisOption('shiptype', second, self.SHIPTYPE)),
      shipname=filterString(self.getAisOption('shipname', second, self.FIRST_NAME if not second else self.SECOND_NAME))
    )
    ais = aislib.AIS(aismsg)
    payload = ais.build_payload(False)
    debug("!!%s" % payload)
    writer.send(payload + "\n")

  def computeLandingPoint(self,currentPosition,lastPosition,currentAltitude,lastAltitude,currentCourse):
    if currentAltitude > lastAltitude:
      debug("altitude increasing - cannot compute")
      return (None,None)
    lastAltitude=lastAltitude - self.altitude
    currentAltitude=currentAltitude - self.altitude
    if lastAltitude < 0 or currentAltitude < 0:
      print("altitudes < 0, last=%f, current=%f",lastAltitude,currentAltitude)
      return (None,None)
    adiff=lastAltitude-currentAltitude
    if adiff < self.minAltDiff:
      debug("altitude diff too small")
      return (None,None)
    distance=geo.distanceM(lastPosition,currentPosition)
    if distance < self.minPosDiff:
      debug("position difference to small, cannot compute landing point")
      return (None,None)
    bearing=geo.calcBearing(lastPosition,currentPosition) if not self.bearingFromCourse else currentCourse
    distanceToLanding=distance*(currentAltitude/(lastAltitude-currentAltitude))
    (landinglat,landinglon)=geo.targetPoint(currentPosition,bearing,distanceToLanding)
    return (landinglat,landinglon)

  def run(self):
    longitudeAverage=Average(self.averageLen)
    latitudeAverage=Average(self.averageLen)
    altitudeAverage=Average(self.averageLen)
    courseAverage=Average(self.averageLen)
    if self.positionInput:
      self.positionThread=threading.Thread(target=self.readOwnPosition)
      self.positionThread.setDaemon(True)
      self.positionThread.start()
    while True:
      try:
        longitudeAverage.reset()
        latitudeAverage.reset()
        altitudeAverage.reset()
        courseAverage.reset()
        reader = createReader(self.input)
        writer = createOutput(self.output)
        reader.open()
        print("opened %s" % self.input)
        writer.open()
        print("opened %s" % self.output)
        speed = 0
        course = 0
        altitude = 0
        hasData = False
        previousPosition=None
        previousAltitude=None
        numNonCompute=0
        isComputing=False
        while True:
          try:
            line = reader.readline()
            if not line.startswith("$"):
              continue
            msg = pynmea2.parse(line)
            debug("msg: %s" % (type(msg)))
            debug(repr(msg))
            if isinstance(msg, pynmea2.RMC):
              speed = msg.spd_over_grnd
              course = msg.true_course
              courseAverage.add(course or 0)
            if isinstance(msg, pynmea2.GGA):
              altitude = msg.altitude
              altitudeAverage.add(altitude)
            if isinstance(msg, pynmea2.LatLonFix):
              if not hasData:
                print("Position lat=%f,lon=%f" % (msg.latitude, msg.longitude))
                hasData = True
              else:
                debug("Position lat=%f,lon=%f" % (msg.latitude, msg.longitude))
              self.sendAisMessages(writer,False,msg.longitude,msg.latitude,speed,course,altitude)
              longitudeAverage.add(msg.longitude)
              latitudeAverage.add(msg.latitude)
              ownAltitudeValid=self.positionInput is None or (self.lastAltitude is not None and time.time() < (self.lastAltitude +self.ownPostionTimeout))
              if ownAltitudeValid and previousPosition is not None and previousAltitude is not None:
                (latitude,longitude)=self.computeLandingPoint([msg.latitude,msg.longitude],previousPosition,altitude,previousAltitude,courseAverage.cur())
                if longitude is not None and latitude is not None:
                  if not isComputing:
                    print("Landing Point computation started")
                    isComputing=True
                  numNonCompute=0
                  debug("computed landing point lat=%f,lon=%f"%(latitude,longitude))
                  self.sendAisMessages(writer,True,longitude,latitude,0,0,self.altitude)
                  #only remember the last values if we have been able to compute
                  previousPosition = [latitudeAverage.cur(), longitudeAverage.cur()]
                  previousAltitude = altitudeAverage.cur()
                else:
                  numNonCompute+=1
                  if numNonCompute > self.maxNonCompute:
                    if isComputing:
                      print("Landing point computation stopped, retrying")
                      isComputing=False
                    numNonCompute=0
                    previousPosition = [latitudeAverage.cur(), longitudeAverage.cur()]
                    previousAltitude = altitudeAverage.cur()
              else:
                debug("cannot compute landing point altValid=%s,previousPosValid=%s,previousAltValid=%s"
                      %(ownAltitudeValid, previousPosition is not None,previousAltitude is not None))
              if longitudeAverage.filled() and latitudeAverage.filled() and previousPosition is None:
                previousPosition=[latitudeAverage.cur(),longitudeAverage.cur()]
              if altitudeAverage.filled() and previousAltitude is None:
                previousAltitude=altitudeAverage.cur()
          except serial.SerialException as e:
            print('Device error: {}'.format(e))
            break
          except pynmea2.ParseError as e:
            print('Parse error')
            print(traceback.format_exc())
            continue
          except Exception as e:
            print('general error')
            print(traceback.format_exc())
            break
      except Exception as e:
        print("exception: %s" % e)
        if not tryForever:
          raise
        time.sleep(2)




if __name__ == '__main__':
  aisopts={}
  args=[]
  args.extend(sys.argv)
  tryForever=False
  positionInput=None
  altitude=None
  average=1
  bearingFromCourse=False
  if len(args) > 0:
    args.pop(0)
  optlist,args=getopt.getopt(args,'drl:a:m:b')
  for flag,arg in optlist:
    if flag == '-d':
      doDebug=1
      continue
    if flag == '-r':
      tryForever=True
      continue
    if flag == '-l':
      positionInput=arg
      continue
    if flag == '-a':
      altitude=float(arg)
      continue
    if flag == '-m':
      average=int(arg)
      assert average >= 1, "average must be >= 1"
      continue
    if flag == '-b':
      bearingFromCourse=True
      continue
    assert False,"unknown arg %s"%flag
  if len(args) < 2:
    print("usage: %s [-d] [-r] [-b] [-l localInput] [-a altitude] [-m number] input output [mmsi=...] [shipname=...]...[mmsi2=...]..."%sys.argv[0])
    print("          input: ser:port:baud or tcp:host:port")
    print("          output: udp:host:port")
    print("          -d: print debug messages")
    print("          -r: retry forever")
    print("          -l input: provide the source for own position")
    print("          -a altitude: own altitude in m")
    print("          -m number: average over that many pos/alt for landing point (default: 1)")
    print("          -b: use GPS course for bearing to landing (instead of pos diff)")
    sys.exit(1)
  for a in args[2:]:
    nv=a.split("=")
    if len(nv) != 2:
      print("invalid arg %s"%a)
      sys.exit(1)
    aisopts[nv[0]]=nv[1]
  runner=NmeaToAis(args[0],args[1])
  runner.aisoptions=aisopts
  runner.tryForever=tryForever
  if altitude is not None:
    runner.altitude=altitude
  if positionInput is not None:
    runner.positionInput=positionInput
  runner.bearingFromCourse=bearingFromCourse
  runner.averageLen=average
  runner.run()
