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

import math

R=6371000 #earth radius in m

# Haversine formula example in Python
# Author: Wayne Dyck
#distance in M
def distanceM(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = (R * c )
    return d

#bearing from one point the next originally by DirkHH
#http://www.movable-type.co.uk/scripts/latlong.html

def calcBearing(curP,endP):
    clat,clon=curP
    elat,elon=endP
    y = math.sin(math.radians(elon)-math.radians(clon)) * math.cos(math.radians(elat))
    x = math.cos(math.radians(clat))*math.sin(math.radians(elat)) - \
        math.sin(math.radians(clat))*math.cos(math.radians(elat))*math.cos(math.radians(elon)-math.radians(clon))
    return ((math.atan2(y, x) * 180 / math.pi) + 360) % 360.0

#https://www.movable-type.co.uk/scripts/latlong.html
def targetPoint(curP,bearing,distance):
  lat,lon=curP
  lat1=math.radians(lat)
  lon1=math.radians(lon)
  bearing=math.radians(bearing)
  dist=distance/R
  lat2 = math.asin(math.sin(lat1) * math.cos(dist) +
                   math.cos(lat1) * math.sin(dist) * math.cos(bearing))
  lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(dist) * math.cos(lat1),
                           math.cos(dist) - math.sin(lat1) * math.sin(lat2))
  lon2 = (lon2 + 3 * math.pi) % (2 * math.pi) - math.pi

  return (math.degrees(lat2),math.degrees(lon2))
