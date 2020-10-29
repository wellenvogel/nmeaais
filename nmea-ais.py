#! /usr/bin/env python
import socket
import sys
#install python-bitstring (pip install bitstring)
import pythonais.aislib as aislib
#install python-nmea2 (or pip install pynmea2)
import pynmea2
#install python-serial (pip install pyserial)
import serial


def debug(txt):
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

def main(port,baud,targetPort,aisoptions):
  ser = serial.Serial(port, baud, timeout=5.0,xonxoff=True)
  if ser is None:
    raise Exception("unable to open port %s"%(port))
  cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  addr="localhost"
  destination=int(targetPort)
  speed=0
  course=0
  altitude=0
  while True:
    try:
      line = ser.readline()
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
        print("Position lat=%f,lon=%f"%(msg.latitude,msg.longitude))
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
        print("!!%s"%payload)
        cs.sendto(payload+"\n", (addr, destination))
        aismsg=aislib.AISStaticAndVoyageReportMessage(
          mmsi=mmsi,
          callsign=filterString(aisoptions.get('callsign')),
          destination=filterString(aisoptions.get('destination') or "alt=%d"%int(altitude)),
          shiptype=getShiptype(aisoptions),
          shipname=filterString(aisoptions.get('shipname'))
        )
        ais = aislib.AIS(aismsg)
        payload = ais.build_payload(False)
        print("!!%s" % payload)
        cs.sendto(payload + "\n", (addr, destination))
    except serial.SerialException as e:
      print('Device error: {}'.format(e))
      break
    except pynmea2.ParseError as e:
      print('Parse error: {}'.format(e))
      continue
    except Exception as e:
      print('general error: {}'.format(e))
      continue


if __name__ == '__main__':
  if len(sys.argv) < 4:
    print("usage: %s serialPort baud udpTargetPort [mmsi=...] [shipname=...]..."%sys.argv[0])
    sys.exit(1)
  aisopts={}
  for a in sys.argv[4:]:
    nv=a.split("=")
    if len(nv) != 2:
      print("invalid arg %s"%a)
      sys.exit(1)
    aisopts[nv[0]]=nv[1]
  main(sys.argv[1],int(sys.argv[2]),sys.argv[3],aisopts)