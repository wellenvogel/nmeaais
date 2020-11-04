#! /usr/bin/env python
import socket
import sys
#install python-bitstring (pip install bitstring)
import time

import pythonais.aislib as aislib
#install python-nmea2 (or pip install pynmea2)
import pynmea2
#install python-serial (pip install pyserial)
import serial

doDebug=0

def debug(txt):
  if doDebug > 0:
    print("##%s"%txt)

def getShiptype(options):
  typev=options.get('shiptype')
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
    self.baud=baud;
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
    self.socket=socket.create_connection((self.host, int(self.port)),timeout=5)

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

def main(input,output,aisoptions={},tryForever=False):
  while True:
    try:
      reader=createReader(input)
      writer=createOutput(output)
      reader.open()
      print("opened %s"%input)
      writer.open()
      print("opened %s" % output)
      speed=0
      course=0
      altitude=0
      hasData=False
      while True:
        try:
          line = reader.readline()
          if not line.startswith("$"):
            continue
          msg = pynmea2.parse(line)
          debug("msg: %s"%(type(msg)))
          debug(repr(msg))
          if isinstance(msg,pynmea2.RMC):
            speed=msg.spd_over_grnd
            course=msg.true_course
          if isinstance(msg,pynmea2.GGA):
            altitude=msg.altitude
          if isinstance(msg,pynmea2.LatLonFix):
            if not hasData:
              print("Position lat=%f,lon=%f"%(msg.latitude,msg.longitude))
              hasData=True
            else:
              debug("Position lat=%f,lon=%f"%(msg.latitude,msg.longitude))
            mmsi=int(aisoptions.get('mmsi') or 333333333)
            aismsg = aislib.AISPositionReportMessage(
              mmsi=mmsi,
              status=0,
              sog=int(speed*10),
              pa=1,
              lon=int(msg.longitude * 600000.0),
              lat=int(msg.latitude * 600000.0),
              cog=int(course*10),
              ts=0,
              raim=1,
              comm_state=82419
            )
            ais = aislib.AIS(aismsg)
            payload = ais.build_payload(False)
            debug("!!%s"%payload)
            writer.send(payload+"\n")
            aismsg=aislib.AISStaticAndVoyageReportMessage(
              mmsi=mmsi,
              callsign=filterString(aisoptions.get('callsign')),
              destination=filterString(aisoptions.get('destination') or "alt=%d"%int(altitude)),
              shiptype=getShiptype(aisoptions),
              shipname=filterString(aisoptions.get('shipname'))
            )
            ais = aislib.AIS(aismsg)
            payload = ais.build_payload(False)
            debug("!!%s" % payload)
            writer.send(payload + "\n")
        except serial.SerialException as e:
          print('Device error: {}'.format(e))
          break
        except pynmea2.ParseError as e:
          print('Parse error: {}'.format(e))
          continue
        except Exception as e:
          print('general error: {}'.format(e))
          continue
    except Exception as e:
      print("exception: %s"%e)
      if not tryForever:
        raise
      time.sleep(2)


if __name__ == '__main__':
  aisopts={}
  args=[]
  args.extend(sys.argv)
  tryForever=False
  if len(args) > 0:
    args.pop(0)
  while len(args) > 0 and args[0][0] == '-':
    flag=args.pop(0)
    if flag == '-d':
      doDebug=1
      continue
    if flag == '-r':
      tryForever=True
      continue
    print("unknown arg %s",flag)
  if len(args) < 2:
    print("usage: %s [-d] [-r] input output [mmsi=...] [shipname=...]..."%sys.argv[0])
    print("          input: ser:port:baud or tcp:host:port")
    print("          output: udp:host:port")
    print("          -d: print debug messages")
    print("          -r: retry forever")
    sys.exit(1)
  for a in args[2:]:
    nv=a.split("=")
    if len(nv) != 2:
      print("invalid arg %s"%a)
      sys.exit(1)
    aisopts[nv[0]]=nv[1]
  main(args[0],args[1],aisopts,tryForever=tryForever)
