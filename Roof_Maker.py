#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [2021] [Susan Zakar], [sue.zakar@gmail.com]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# This program for 3D papercraft will construct the pieces needed to make a roof
# for a house or other structure, as well as for dormer windows that can fit against the roof.
# There are a number of configurable options, including the size of the roof and dormers.
#
#

import inkex
import math
import copy
from inkex import PathElement, Style
from inkex.paths import Move, Line, ZoneClose, Path
from inkex.transforms import Vector2d
from inkex.elements._groups import Group

class pathStruct(object):
    def __init__(self):
        self.id="path0000"
        self.path= Path()
        self.enclosed=False
        self.style = None
    def __str__(self):
        return self.path
    

################################ INSET CODE *****
class pnPoint(object):
   # This class came from https://github.com/JoJocoder/PNPOLY
    def __init__(self,p):
        self.p=p
    def __str__(self):
        return self.p
    def InPolygon(self,polygon,BoundCheck=False):
        inside=False
        if BoundCheck:
            minX=polygon[0][0]
            maxX=polygon[0][0]
            minY=polygon[0][1]
            maxY=polygon[0][1]
            for p in polygon:
                minX=min(p[0],minX)
                maxX=max(p[0],maxX)
                minY=min(p[1],minY)
                maxY=max(p[1],maxY)
            if self.p[0]<minX or self.p[0]>maxX or self.p[1]<minY or self.p[1]>maxY:
                return False
        j=len(polygon)-1
        for i in range(len(polygon)):
            if ((polygon[i][1]>self.p[1])!=(polygon[j][1]>self.p[1]) and (self.p[0]<(polygon[j][0]-polygon[i][0])*(self.p[1]-polygon[i][1])/( polygon[j][1] - polygon[i][1] ) + polygon[i][0])):
                    inside =not inside
            j=i
        return inside
 
class Roofmaker(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--usermenu")
        pars.add_argument("--unit", default="in",\
            help="Dimensional units")
        pars.add_argument("--scoretype",default="dash",\
            help="Use cut-dash scorelines or solid scorelines")        
        pars.add_argument("--isbarn",default="False",\
            help="User barn style top on roof (two angles)")
        pars.add_argument("--sides", default="12",\
            help="Dormer Top Poly Sides")
        pars.add_argument("--basewidth", type=float, default=1.0,\
            help="Dormer Width (in Dimensional Units)")
        pars.add_argument("--dormerht", type=float, default=1.5,\
            help="Dormer Height (in Dimensional Units; zero for no dormer)")
        pars.add_argument("--dormertopht", type=float, default=.5,\
            help="Dormer Top Height (in Dimensional Units;")        
        pars.add_argument("--roof_inset", type=float, default=1.0,\
            help="Roof Inset (in Dimensional Units)")
        pars.add_argument("--roofpeak", type=float, default=2.0,\
            help="Roof Peak Height (in Dimensional Units)")
        pars.add_argument("--roofdepth", type=float, default=3.0,\
            help="Roof Base Depth (in Dimensional Units)")
        pars.add_argument("--roofwidth", type=float, default=7.0,\
        help="Roof Base Cutout (in Dimensional Units)")
        pars.add_argument("--basecutout", type=float, default=1.0,\
            help="Roof Base Width (in Dimensional Units)")
        pars.add_argument("--chimney_ht", type=float, default=45.0,\
            help="Height above roof on peak side")
            
        pars.add_argument("--chimney_wd", type=float, default=1.0,\
            help="width of chimney")
        pars.add_argument("--chimney_depth", type=float, default=.75,\
            help="depth of chimney")        
        pars.add_argument("--off_center", type=float, default=.5,\
            help="Amount off_center from peak")        
        pars.add_argument("--shrink",type=float,default=0.67,\
            help="Reduction amount for chimney tabs and scores")             
        pars.add_argument("--isabase",default="True",\
            help="There is a base on the dormer")

        pars.add_argument("--stickout",type=float,default=0.0,\
            help="Extend base of dormer from flush with roof")
        pars.add_argument("--paper",type=float,default=0.01,\
            help="Adjust dormer cutout for paper thickness")       
        pars.add_argument("--window_frame",type=float,default=0.125,\
            help="Relative thickness of dormer window frame")

        pars.add_argument("--bhratio",type=float,default=0.2,\
            help="Relative thickness of dormer window frame")
        pars.add_argument("--bdratio",type=float,default=0.4,\
            help="Relative thickness of dormer window frame")
        
    def insidePath(self, path, p):
        point = pnPoint((p.x, p.y))
        pverts = []
        for pnum in path:
            if pnum.letter == 'Z':
                pverts.append((path[0].x, path[0].y))
            else:
                pverts.append((pnum.x, pnum.y))
        isInside = point.InPolygon(pverts, True)
        return isInside # True if point p is inside path

    def makescore(self, pt1, pt2, dashlength):
        # Draws a dashed line of dashlength between two points
        # Dash = dashlength space followed by dashlength mark
        # if dashlength is zero, we want a solid line
        # Returns dashed line as a Path object
        apt1 = Line(0.0,0.0)
        apt2 = Line(0.0,0.0)
        ddash = Path()
        if math.isclose(dashlength, 0.0):
            
            ddash.append(Move(pt1.x,pt1.y))
            ddash.append(Line(pt2.x,pt2.y))
        else:
            if math.isclose(pt1.y, pt2.y):
                
                if pt1.x < pt2.x:
                    xcushion = pt2.x - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    xcushion = pt1.x - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                done = False
                while not(done):
                    if (xpt + dashlength*2) <= xcushion:
                        xpt = xpt + dashlength
                        ddash.append(Move(xpt,ypt))
                        xpt = xpt + dashlength
                        ddash.append(Line(xpt,ypt))
                    else:
                        done = True
            elif math.isclose(pt1.x, pt2.x):
                
                if pt1.y < pt2.y:
                    ycushion = pt2.y - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    ycushion = pt1.y - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                done = False
                while not(done):
                    if(ypt + dashlength*2) <= ycushion:
                        ypt = ypt + dashlength         
                        ddash.append(Move(xpt,ypt))
                        ypt = ypt + dashlength
                        ddash.append(Line(xpt,ypt))
                    else:
                        done = True
            else:
               
                if pt1.y > pt2.y:
                    apt1.x = pt1.x
                    apt1.y = pt1.y
                    apt2.x = pt2.x
                    apt2.y = pt2.y
                else:
                    apt1.x = pt2.x
                    apt1.y = pt2.y
                    apt2.x = pt1.x
                    apt2.y = pt1.y
                m = (apt1.y-apt2.y)/(apt1.x-apt2.x)
                theta = math.atan(m)
                msign = (m>0) - (m<0)
                ycushion = apt2.y + dashlength*math.sin(theta)
                xcushion = apt2.x + msign*dashlength*math.cos(theta)
                xpt = apt1.x
                ypt = apt1.y
                done = False
                while not(done):
                    nypt = ypt - dashlength*2*math.sin(theta)
                    nxpt = xpt - msign*dashlength*2*math.cos(theta)
                    if (nypt >= ycushion) and (((m<0) and (nxpt <= xcushion)) or ((m>0) and (nxpt >= xcushion))):
                        # move to end of space / beginning of mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash.append(Move(xpt,ypt))
                        # draw the mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash.append(Line(xpt,ypt))
                    else:
                        done = True
        return ddash

    def detectIntersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        td = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        if td == 0:
            # These line segments are parallel
            return False
        t = ((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/td
        if (0.0 <= t) and (t <= 1.0):
            return True
        else:
            return False

    def orientTab(self,pt1,pt2,height,angle,theta,orient):
        tpt1 = Line(0.0,0.0)
        tpt2 = Line(0.0,0.0)
        tpt1.x = pt1.x + orient[0]*height + orient[1]*height/math.tan(math.radians(angle))
        tpt2.x = pt2.x + orient[2]*height + orient[3]*height/math.tan(math.radians(angle))
        tpt1.y = pt1.y + orient[4]*height + orient[5]*height/math.tan(math.radians(angle))
        tpt2.y = pt2.y + orient[6]*height + orient[7]*height/math.tan(math.radians(angle))
        if not math.isclose(theta, 0.0):
            t11 = Path([Move(pt1.x,pt1.y),Line(tpt1.x, tpt1.y)])
            t12 = Path([Move(pt1.x,pt1.y),Line(tpt2.x, tpt2.y)])
            thetal1 = t11.rotate(theta, [pt1.x,pt1.y])
            thetal2 = t12.rotate(theta, [pt2.x,pt2.y])
            tpt1.x = thetal1[1].x
            tpt1.y = thetal1[1].y
            tpt2.x = thetal2[1].x
            tpt2.y = thetal2[1].y
        return tpt1,tpt2

    def makeTab(self, tpath, pt1, pt2, tabht, taba):
        # tpath - the pathstructure containing pt1 and pt2
        # pt1, pt2 - the two points where the tab will be inserted
        # tabht - the height of the tab
        # taba - the angle of the tab sides
        # returns the two tab points (Line objects) in order of closest to pt1
        tpt1 = Line(0.0,0.0)
        tpt2 = Line(0.0,0.0)
        currTabHt = tabht
        currTabAngle = taba
        testAngle = 1.0
        testHt = currTabHt * 0.001
        adjustTab = 0
        tabDone = False
        while not tabDone:
            # Let's find out the orientation of the tab
            if math.isclose(pt1.x, pt2.x):
                # It's vertical. Let's try the right side
                if pt1.y < pt2.y:
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[1,0,1,0,0,1,0,-1])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[-1,0,-1,0,0,1,0,-1]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[1,0,1,0,0,1,0,-1]) # Guessed right
                else: # pt2.y < pt1.y
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[1,0,1,0,0,-1,0,1])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[-1,0,-1,0,0,-1,0,1]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[1,0,1,0,0,-1,0,1]) # Guessed right
            elif math.isclose(pt1.y, pt2.y):
                # It's horizontal. Let's try the top
                if pt1.x < pt2.x:
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[0,1,0,-1,-1,0,-1,0])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,1,0,-1,1,0,1,0]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,1,0,-1,-1,0,-1,0]) # Guessed right
                else: # pt2.x < pt1.x
                    pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,0.0,[0,-1,0,1,-1,0,-1,0])
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,-1,0,1,1,0,1,0]) # Guessed wrong
                    else:
                        tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,0.0,[0,-1,0,1,-1,0,-1,0]) # Guessed right

            else: # the orientation is neither horizontal nor vertical
                # Let's get the slope of the line between the points
                # Because Inkscape's origin is in the upper-left corner,
                # a positive slope (/) will yield a negative value
                slope = (pt2.y - pt1.y)/(pt2.x - pt1.x)
                # Let's get the angle to the horizontal
                theta = math.degrees(math.atan(slope))
                # Let's construct a horizontal tab
                seglength = math.sqrt((pt1.x-pt2.x)**2 +(pt1.y-pt2.y)**2)
                if slope < 0.0:
                    if pt1.x < pt2.x:
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,1,0,-1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,-1,0,-1,0]) # Guessed right
                    else: # pt1.x > pt2.x
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,-1,0,1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,-1,0,-1,0]) # Guessed right
                else: # slope > 0.0
                    if pt1.x < pt2.x:
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,1,0,-1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,1,0,-1,-1,0,-1,0]) # Guessed right
                    else: # pt1.x > pt2.x
                        pnpt1,pnpt2 = self.orientTab(pt1,pt2,testHt,testAngle,theta,[0,-1,0,+1,-1,0,-1,0])
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,1,0,1,0]) # Guessed wrong
                        else:
                            tpt1,tpt2 = self.orientTab(pt1,pt2,currTabHt,currTabAngle,theta,[0,-1,0,1,-1,0,-1,0]) # Guessed right
            # Check to see if any tabs intersect each other
            if self.detectIntersect(pt1.x, pt1.y, tpt1.x, tpt1.y, pt2.x, pt2.y, tpt2.x, tpt2.y):
                # Found an intersection.
                if adjustTab == 0:
                    # Try increasing the tab angle in one-degree increments
                    currTabAngle = currTabAngle + 1.0
                    if currTabAngle > 88.0: # We're not increasing the tab angle above 89 degrees
                        adjustTab = 1
                        currTabAngle = taba
                if adjustTab == 1:
                    # So, try reducing the tab height in 20% increments instead
                    currTabHt = currTabHt - tabht*0.2 # Could this lead to a zero tab_height?
                    if currTabHt <= 0.0:
                        # Give up
                        currTabHt = tabht
                        adjustTab = 2
                if adjustTab == 2:
                    tabDone = True # Just show the failure
            else:
                tabDone = True
            
        return tpt1,tpt2

    #draw SVG line segment(s) between the given (raw) points
    def drawline(self, dstr, name, parent, sstr=None):
        line_style   = {'stroke':'#000000','stroke-width':'0.25','fill':'#eeeeee'}
        if sstr == None:
            stylestr = str(inkex.Style(line_style))
        else:
            stylestr = sstr
        el = parent.add(inkex.PathElement())
        el.path = dstr
        el.style = stylestr
        el.label = name
  
    def insetPolygon(self, points, insetDist):

            # Converted from
            # public-domain code by Darel Rex Finley, 2007
            # See diagrams at http://alienryderflex.com/polygon_inset

            # points = list of clockwise path commands (e.g. [Mcmd, Lcmd, Lcmd, ...])
            # insetDist = positive inset distance
            # NOTE: To outset the polygon, provide CCW path commands or negative insetDist (not both)
            corners = len(points)
            startX = points[0].x
            startY = points[0].y
            # Polygon must have at least three corners to be inset
            if corners < 3:
                return
            # Inset the polygon
            c = points[corners-1].x
            d = points[corners-1].y
            e = points[0].x
            f = points[0].y
            for i in range(corners-1):
                a = c #last x
                b = d #last y
                c = e #first x
                d = f #first y
                e = points[i+1].x #following x
                f = points[i+1].y #following y
                #status, px, py = self.insetCorner(a,b,c,d,e,f,insetDist)
                status, px, py = self.insetCorner(a,b,c,d,e,f,insetDist)
                if status == 1:
                    points[i].x = px
                    points[i].y = py
                
            #status, px, py = self.insetCorner(c,d,e,f,startX,startY,insetDist)
            status, px, py = self.insetCorner(c,d,e,f,startX,startY,insetDist)
            if status == 1:
                points[-1].x = px
                points[-1].y = py
                
    def insetCorner(self, a,b,c,d,e,f,insetDist):
        # Converted from
        # public-domain code by Darel Rex Finley, 2007
        # Given the sequentially connected points (a,b), (c,d), and (e,f), this
        # function returns, in (C,D), a bevel-inset replacement for point (c,d).

        # Note:  If vectors (a,b)->(c,d) and (c,d)->(e,f) are exactly 180° opposed,
        #         or if either segment is zero-length, this function will do
        #         nothing; i.e. point (C,D) will not be set.

        c1 = c #first x
        d1 = d #first y
        c2 = c #first x
        d2 = d #first y
        # Calculate length of line segments
        dx1 = c - a  #first x  - last x
        dy1 = d - b  #first y - last y
        dist1 = math.sqrt(dx1**2 + dy1**2) #diagonal of the distance
        dx2 = e - c #the following x - the first x
        dy2 = f - d #the following y - the first y
        dist2 = math.sqrt(dx2**2 + dy2**2)  #diagnonal of those
        # Exit if either segment is zero-length
        if math.isclose(dist1, 0.0,abs_tol=1e-09) or math.isclose(dist2, 0.0,abs_tol=1e-09):
            return 0,0,0
        # Inset each of the two line segments
        insetX = dy1/dist1*insetDist
        a += insetX
        c1 += insetX
        insetY = -dx1/dist1*insetDist
        b += insetY
        d1 += insetY
        insetX = dy2/dist2*insetDist
        e += insetX
        c2 += insetX
        insetY = -dx2/dist2*insetDist
        f += insetY
        d2 += insetY
        # If inset segments connect perfectly, return the connection point
        if math.isclose(c1, c2) and math.isclose(d1, d2,abs_tol=1e-09):
            return 1, c1, d1
        # Return the intersection point of the two inset segments (if any)
        #status, inX, inY = self.lineIntersection(a,b,c1,d1,c2,d2,e,f)
        status, inX, inY = self.lineIntersection(a,b,c1,d1,c2,d2,e,f)
        if status == 1:
            insetX = inX
            insetY = inY
            return 1, insetX, insetY

    def lineIntersection(self, Ax,Ay,Bx,By,Cx,Cy,Dx,Dy):
        # Converted from
        # public domain function by Darel Rex Finley, 2006

        # Determines the intersection point of the line defined by points A and B with the
        # line defined by points C and D.

        # Returns 1 if the intersection point was found, and returns that point in X,Y.
        # Returns 0 if there is no determinable intersection point, in which case X,Y will
        #be unmodified.

        # Fail if either line is undefined
        if (math.isclose(Ax, Bx) and math.isclose(Ay, By)) or (math.isclose(Cx, Dx) and math.isclose(Cy, Dy)):
            return 0, 0, 0
        # (1) Translate the system so that point A is on the origin
        Bx -= Ax
        By -= Ay
        Cx -= Ax
        Cy -= Ay
        Dx -= Ax
        Dy -= Ay
        # Discover the length of segment A-B
        distAB = math.sqrt(Bx**2 + By**2)
        # (2) Rotate the system so that point B is on the positive X axis
        theCos = Bx/distAB
        theSin = By/distAB
        newX = Cx*theCos + Cy*theSin
        Cy = Cy*theCos - Cx*theSin
        Cx = newX
        newX = Dx*theCos + Dy*theSin
        Dy = Dy*theCos - Dx*theSin
        Dx = newX
        # Fail if the lines are parallel
        if math.isclose(Cy, Dy):
            return 0,0,0
        # (3) Discover the position of the intersection point along line A-B
        ABpos = Dx + (Cx - Dx)*Dy/(Dy - Cy)
        # (4) Apply the discovered position to line A-B in the original coordinate system
        X = Ax + ABpos*theCos
        Y = Ay + ABpos*theSin
        return 1, X, Y

    ###############################


   

    def stringmeup(self,list1,scores,scores2,tscoremap,zerotab,cutout,cutoutpath,piece,layer,stylestring,tab_height,dashlength,tab_angle,mkpath,inset_only,isabase):
        dscore = Path()
        plist1 = pathStruct()
        plist2 = pathStruct() 
        plist3 = pathStruct()
        saveid = "a01"
        #if there is not a base then we are missing the last point.
        
        if not( math.isclose(cutout,0)): # we have a cutout path
            #for the cutout, if the first and last are NOT the same, then append an ending node so insetPolygon works as expected
            jj = math.isclose(cutoutpath[0].x,cutoutpath[-1].x)
            jk = math.isclose(cutoutpath[0].y,cutoutpath[-1].y)
            if  not(jk and jj):
                cutoutpath.append(Vector2d(cutoutpath[0].x,cutoutpath[0].y))
        #but if our list has the same first and last elements, delete the last element
        jj = math.isclose(list1[0].x,list1[-1].x)
        jk = math.isclose(list1[0].y,list1[-1].y)
        if (jj and jk):
            list1.pop()
        
        for pt in range(len(list1)):
            if pt == 0:
                plist1.path.append(Move(list1[pt].x, list1[pt].y))
                plist2.path.append(Move(list1[pt].x, list1[pt].y))
            else:
                plist1.path.append(Line(list1[pt].x, list1[pt].y))                
                plist2.path.append(Line(list1[pt].x, list1[pt].y))        
                #Looks ok here  -- p1list and p2 list have the expected nodes
                
        
        if (cutout != 0):  #here we handle second path which is inset and will be added to path
            if isabase == True:
                cj = 0
            else:
                cj = 0
            for pt in range(len(cutoutpath)-cj):
                if pt == 0:
                    plist3.path.append(Move(cutoutpath[pt].x, cutoutpath[pt].y))
                else:
                    plist3.path.append(Line(cutoutpath[pt].x, cutoutpath[pt].y))

            self.insetPolygon(plist3.path[0:-1],cutout)
            ###########
            
            #create new string from this
            istring = 'M ' + str(plist3.path[0].x) + ', '+str(plist3.path[0].y)
            if (cutout != 0):
                for nd in reversed(range(1,len(plist3.path)-1)):
                    istring += ' L '+ str(plist3.path[nd].x) +', '+ str(plist3.path[nd].y)
            istring += ' Z'
            
            
        if len(scores) == 0:
            noscores = True
        else:
            noscores = False
        if len(tscoremap) == 0:
            notabs = True
        else:
            notabs = False
        #now build the path strings with move and line commands
        newstring = 'M ' + str(round(list1[0].x ,4)) + ','+ str(round(list1[0].y,4))  #move to starting node
        #here we build the final shape with any tabs and scorelines that we use                                         
        for i in range(1,len(list1)):  #before moving to each node, check if there should be a tab there and insert it if so
            if i in tscoremap:                
                tabpt2, tabpt1 = self.makeTab(plist2, list1[i], list1[i-1], tab_height, tab_angle)
                dscore = dscore + self.makescore(plist1.path[i],plist1.path[i-1],dashlength)  #the tab will join to the one before it
                newstring += ' L ' + str(round(tabpt1.x,4)) + ','+ str(round(tabpt1.y,4))  #first tab node
                newstring += ' L ' + str(round(tabpt2.x,4)) + ','+ str(round(tabpt2.y,4))  #second tab node
            newstring += ' L ' + str(round(list1[i].x,4)) + ','+ str(round(list1[i].y,4))  #line to this node
            
        #before closing this string up, see if we should have a tab between the last node and the first
        
        if zerotab:  
            
            zt= len(list1)-1 # the last point on the list
                     
            tabpt2, tabpt1 = self.makeTab(plist2,list1[0], list1[zt], tab_height,tab_angle) 
            dscore = dscore + self.makescore(plist1.path[0],plist1.path[zt],dashlength)
            newstring += ' L ' + str(round(tabpt1.x,4)) + ','+ str(round(tabpt1.y,4))
            newstring += ' L ' + str(round(tabpt2.x,4)) + ','+ str(round(tabpt2.y,4))
        
        #we are either at the last node of the list, or, if there's a zero tab, at the second node  of the zero tab so time to close this one up.
        
        newstring += ' Z '

        for i in range (len(scores)):
            dscore = dscore + self.makescore(plist1.path[scores[i]], plist1.path[scores2[i]],dashlength)
            

        if (cutout !=0) :  #we are cutting out a hole from the piece
            if inset_only == False:                 
                newstring1 = newstring+ istring
                newstring = newstring1
            else:
                newstring = istring
            
        
        #NEED TO DRAW THIS
        dprop = Path(newstring)
        if math.isclose(dashlength, 0.0) or mkpath==False:
            # lump together all the score lines
            group = Group()
            group.label = 'group'+piece
            self.drawline(newstring,'model'+piece,group,stylestring) # Output the model
            if not (len(dscore)==0):
                stylestring2 =  {'stroke':'#009900','stroke-width':'0.25','fill':'#eeeeee'}
                self.drawline(str(dscore),'score'+piece,group,stylestring2) # Output the scorelines separately
            layer.append(group)
        else:
            dprop = dprop + dscore
            self.drawline(str(dprop),piece,layer,stylestring)
        #pc += 1
        return newstring

    #function to return the xy values for the top of the dormer.
    #when changing to inkscape we will need to call these with self.

    def geo_b_alpha_a(self,b, alpha):
        c= b/math.cos(math.radians(alpha))
        a = math.sqrt(c**2-b**2)
        return a
    
    def geo_b_alpha_c(self,b, alpha):
        c=b/math.cos(math.radians(alpha))
        return c

    def geo_a_b_alpha(self,a,b):
        c=math.sqrt(a**2+b**2)
        alpha = math.asin(a/c)
        return math.degrees(alpha)

    def geo_a_b_c(self,a,b):
        c=math.sqrt(a**2+b**2)
        return c

    def geo_c_a_b(self,c,a):
        b= math.sqrt(c**2 - a**2)
        return b
        
    def geo_a_alpha_b(self,a, alpha):
        c=a/math.sin(math.radians(alpha))
        b= math.sqrt(c**2 - a**2)
        return b
        
    def geo_c_alpha_b(self,c,alpha):
        a = c * math.sin(math.radians(alpha))
        b = math.sqrt(c**2 - a**2)
        return(b)   
    def geo_c_alpha_a(self,c,alpha):
        a= c * math.sin(math.radians(alpha))
        return(a)
    def circleCalc(self,b, c, d):
        temp = c[0]**2 + c[1]**2
        bc = (b[0]**2 + b[1]**2 - temp) / 2
        cd = (temp - d[0]**2 - d[1]**2) / 2
        det = (b[0] - c[0]) * (c[1] - d[1]) - (c[0] - d[0]) * (b[1] - c[1])

        if abs(det) < 1.0e-10:
            return None

        # Center of circle
        cx = (bc*(c[1] - d[1]) - cd*(b[1] - c[1])) / det
        cy = ((b[0] - c[0]) * cd - (c[0] - d[0]) * bc) / det

        radius = ((cx - b[0])**2 + (cy - b[1])**2)**.5

        return cx,cy,radius
        


    def intersectionPoints(self,a,b,origin,pt1,pt2):
        #Credit to yashjain12yj from post on stackoverflow
        #xi1, yi1, xi2, yi2 <- intersection points
        x1=pt1.x
        x2 = pt2.x
        y1 = pt2.y
        y2 = pt2.y
        h=origin.x
        k=origin.y
        xi1, yi1, xi2, yi2, aa, bb, cc, m = 0, 0, 0, 0, 0, 0, 0, 0
        if x1 != x2:
            m = (y2 - y1)/(x2 - x1)
            c = y1 - m * x1
            aa = b * b + a * a * m * m
            bb = 2 * a * a * c * m - 2 * a * a * k * m - 2 * h * b * b
            cc = b * b * h * h + a * a * c * c - 2 * a * a * k * c + a * a * k * k - a * a * b * b
        else:
            # vertical line case
            aa = a * a
            bb = -2.0 * k * a * a
            cc = -a * a * b * b + b * b * (x1 - h) * (x1 - h)
        d = bb * bb - 4 * aa * cc
        # intersection points : (xi1,yi1) and (xi2,yi2)
        if d > 0:
            if (x1 != x2):
                xi1 = (-bb + (d**0.5)) / (2 * aa)
                xi2 = (-bb - (d**0.5)) / (2 * aa)
                yi1 = y1 + m * (xi1 - x1)
                yi2 = y1 + m * (xi2 - x1)
            else:
                yi1 = (-bb + (d**0.5)) / (2 * aa)
                yi2 = (-bb - (d**0.5)) / (2 * aa)
                xi1 = x1
                xi2 = x1
        return (Vector2d(xi1, yi1),Vector2d(xi2, yi2))

    def linelength(self,a,b):
    #def linelength(self,a,b):
        t1 = (a.x-b.x)**2
       
        t2 = (a.y-b.y)**2
        t = abs(t1+t2)  
        if t == 0:
            lineln = 0
        else:
            lineln = math.sqrt(t)
        return (lineln)
    def ellipse_pt(self,a,b,theta): #a is len axis1; b=len axis2; theta is angle in degrees
        theta = math.radians(theta)
        v=a*b*math.sin(theta)
        w = math.sqrt( ((b*math.cos(theta))**2) +((a*math.sin(theta))**2))
        y= v/w
        v = a*b*math.cos(theta)
        w = math.sqrt(((b*math.cos(theta))**2) + ((a * math.sin(theta))**2))
        x = v/w
        return(Vector2d(x,y))

    def ellipseg(self,a,b,segs):  #calculate the node endpoints for segments of approximately equal length in ellipse x+ y- quadrant
        odd = (segs%2)!=0
        d= 1
        starti = 270
        stopi = 360
        stepi = 1/d
        rangestop = 360
        lensegs =[]
        allsegs = []
        lenfull = 0  #running total of length
        seglist = []
        seg2 = segs/2
        firstpiece = True
        ilist = []
        lensegs.append(0)
        allsegs.append(self.ellipse_pt(a,b,starti))
        seglist.append(Vector2d(0,-b))
        
        i = starti
        for k in range(271,360):
            i = i + stepi
            allsegs.append(self.ellipse_pt(a,b,i))
            qx = allsegs[-1].x
            qy = allsegs[-1].y
            g = self.linelength(allsegs[-1],allsegs[-2])
            lenfull += g
            lensegs.append(g)
            f=len(lensegs)-1
            h=len(allsegs)-1
        

        #divide lenfull by seg2 to calculate approx length of a segment piece
        segpiece  = lenfull/seg2  #this is the length of a full segment we are looking for
        segtot = 0
        i = 0

        
        segmeasure = segpiece
        doloop = True
        while doloop:  #go through our segment lengths and add them up
            if odd and firstpiece:
                segmeasure = segpiece/2  #if we have an odd number of pieces the first one will be half
                        
            while(segtot <= segmeasure):
                i += 1
                if i>len(lensegs)-1:
                    i = len(lensegs)-1
                    doloop = False
                segtot += lensegs[i]
                         
            #found first segment  -- get the xy vals from allsegs
            if doloop == False:
                    seglist.append(Vector2d(a,0))
            else:
                seglist.append(allsegs[i])

            segtot = 0
            firstpiece = False
            segmeasure = segpiece
        return(seglist)
            
    def topnodescalc(self,axisx,axisy,sidect):
        #SIDE NODE CALCUATION FOR DORMER TOP
        #set these variables to appropriate values in the extension
        
        #-----------------
        axisy2=axisy
        odd = ( sidect % 2 != 0)
        ilist =[]
        pass1 = []
        pass1 = self.ellipseg(axisx,axisy,sidect)

        if (odd):  #need to do second pass which is taller than first then omit the topmost point and join the next topmost
            #there is a fudge factor here.  Instead of using the y value for those two points, we use the requested height

            eplus = pass1[1].y - pass1[0].y 
            axisy += eplus  
            pass1 = []
            pass1 = self.ellipseg(axisx,axisy,sidect)
            
            pass1.pop(0) #get rid of first element
            pass1.pop(0) #and the second element,because we replace these
            pt1 = Vector2d(-axisx -10, -axisy2)
            pt2 = Vector2d(axisx +10, -axisy2)
            origin = Vector2d(0,0)
            ppt1,ppt2 = self.intersectionPoints(axisx,axisy,origin,pt1,pt2)
            pass1.insert(0,ppt1)

        #reverse for other side of dormer top
        if odd:
            rs =0
        else:
            rs =1
        
        for i in range(rs,len(pass1)):
            ilist.append(Vector2d(-pass1[i].x,pass1[i].y))
        for i in range(len(ilist)):
            pass1.insert(0,ilist[i])
          
       
        return (pass1)

    def nodesloc (self,fwidth,baseht,topheight,segnum,isabase,notop):  #in this revision also construct the lenlist at same time
        #use self.topnodes to get the nodes along the top.  The bottom center of the top will be a 0,0
        xlist = []
        ylist = []
        lenlist = []
        outset = []
        
        width = fwidth/2

        axisy2 = topheight
        
            
        if notop:
            #just make the base 
            xsert = [width,-width,-width,width,width]
            ysert = [baseht,baseht,0,0,baseht]
            lensert = [2*width,baseht,2*width,baseht]
            xlist.extend(xsert)
            ylist.extend(ysert)
            lenlist.extend(lensert)

        else:
            dorm = self.topnodescalc(width,topheight,segnum)
           #if we have a base (with a top), insert it here  -- start lower right and draw bottom segment
            if isabase:
                b1 = Vector2d(width,baseht)
                b2 = Vector2d(-width,baseht)
                dorm.insert(0,b2)
                dorm.insert(0,b1)
            xlist.append(dorm[0].x)
            ylist.append(dorm[0].y)
            xlist.append(dorm[1].x)
            ylist.append(dorm[1].y)
            lenlist.append(self.linelength(dorm[1],dorm[0]))
            for i in range(2,len(dorm)):
                xlist.append(dorm[i].x)
                ylist.append(dorm[i].y)
                lenlist.append(self.linelength(dorm[i],dorm[i-1]))   

        return xlist,ylist,lenlist
        

    def outsets (self,ylist,lenlist,isabase,baseht,stickout,roofangle):  #how far will our dormer nodes be from the roof?
        
        outsetlen = []
        #In order to calculate this as we like, for purposes of calculation, either the bottom of the base will be at zero or if no base then the bottom of the dormer top. 
        #in addition if there is a stickout, then we need to figure that in as well on our x values
        y2 = ylist[0]  #bottommost
        
        
        stopy = math.floor(len(ylist)/2)+1
        rpty =  int(len(ylist)%2 == 1) 
        
        for i in range(1,stopy): 
            y2 = y2 - ylist[i]  #moving upward 
            
            #calculate the hypotenuse given alpha=roofangle and a=totht
            oa =( self.geo_b_alpha_a(y2,90-roofangle))
            outsetlen.append = oa
            
            
        #we have half the outsets. To get the rest, reverse the list
        ii = len(outsetlen)
        for i in reversed(range(ii-rpty)):
            outsetlen.append(outsetlen[i])
        
        
        return outsetlen  #contains the outsets for the points in the top     
        
    def sidenodes(self,inlenlist,yinlist,xlist,isabase,roofangle,baseht,stickout,sides,notop,width):
        spathlist = []
        x1v = []
        y1v = []
        
        totht = 0   
        scount =0
        if math.isclose(stickout,0,abs_tol=1e-09):
            isstickout = False
            stickout = 0.0
        else:
            isstickout = True
        if notop:  #just do the four points since the base is always a rectangle
            x2 = self.geo_b_alpha_a(baseht,90-roofangle)
            yy = [0,baseht,baseht+width,(2*baseht)+width]
            xx = [0,x2,x2,0]
            if isstickout:
                xx1 = -stickout
                xx.append(-stickout)
                yy.append((2*baseht)+width)
            else:
                xx1 = 0
            yydown = [baseht+width,baseht,0]  
            xxdown = [xx1,xx1,xx1]
            tadd=0
            if isstickout:
                tadd = 1
                xxdown.append(0)
                yydown.append(0)
            xx.extend(xxdown)
            yy.extend(yydown)
            for i in range(len(xx)):
                spathlist.append(Vector2d(xx[i],yy[i]))
            tmap = [1,2,3]
            
            smap = [1,2]
            smapr = [5+tadd,4+tadd]
            decosmap = copy.deepcopy(smap)
            decosmapr = copy.deepcopy(smapr)
        else:
            
            lenlist = copy.deepcopy(inlenlist)
            ylist = copy.deepcopy(yinlist)
            lenlist.insert(0,0)
            
            if isabase:
                #first point will be 0,baseht
                #pop the first two entries from ylist so it corresponds
                ylist.pop(0)
                ylist.pop(0)
                ylist.insert(0,baseht)
                ylist.append(baseht)
                
                addlen = baseht
                lenlist.pop(1)
                lenlist.append(baseht)
                

            #roof angle is base_angle.

            xzero = stickout #if base sticks out, the left side will be adjusted accordingly
            smap = []
            smapr = []
            decosmap=[]
            decosmapr=[]
            tmap = []    
            totht = 0
            if sides%2 == 0:
                even = 1
            else:
                even = 0
           
            

            yval = 0
            y1vtot = 0
     
               
            if not(isabase):
                ylist.append(ylist[0])
                yval = baseht
            else:
                y1vtot = baseht
            for i in range(len(lenlist)):  #find the y axis values
                y1vtot = y1vtot-lenlist[i]
                y1v.append(y1vtot)
                
                
            #find the x axis values
            #lenlist has values for the top of the dormer only.  If therere is a base, we handle it separately.
            
            x1v.append(0)
            if isabase:
                b=0
            else:
                b=1
            for i in range(1,len(ylist)-b):
                x2 = abs(ylist[i]- baseht)
                xval = self.geo_b_alpha_a(x2,90-roofangle)
                x1v.append(xval)
            
           
            
            for i in range(len(x1v)):
                spathlist.append(Vector2d(x1v[i],y1v[i]))
            
            

            #finally just traverse back down the left side 
            xout =0
            if (isstickout):
                spathlist.append(Vector2d(-stickout,y1v[-1]))
                xout = -stickout

            for i in reversed(range(len(y1v)-1)):
                spathlist.append(Vector2d(xout,y1v[i]))
            if isstickout:
                spathlist.append(Vector2d(0,y1v[0]))
                
                
            #and tabs only on right side
            if isabase: 
                bm = 2
                ij = 0
            else:
                bm=0
                ij = 1
            for i in range((sides+bm)):  
                tmap.append(i+1)
                
                
                         
                
                
                
                
            #we now have the perimeter of the side piece (UNCLOSED)  Now need to map out the scorelines and tabs
            #for now just put scorelines only at the top and bottom parts and at the middle
            # if sides is odd then there won't be a top point and we need scorelines in two points across the middle
            # if sides is even then we have a score line at the top only
            # we have tabs only along the right side (the part that will fit into the hole in the roof
            # SCORE MARKS
            
            cj = 1
            if (isstickout): #if we have a stickout
                cj = 2
            
            z = math.floor(len(spathlist)/2)
            for i in range(1,z):
                        q = (len(spathlist)-cj )-i
                        
                        smap.append(i)
                        smapr.append(q)
            bout=0 
            sout = 0
            #now put scorelines on the deco.
            if isstickout:
                sout = 1
            if isabase:
                bout = 1
            #if even math.floor((len(spathlist)+sout)/4)
            #if odd math.floor((len(spathlist)+sout)/4) and previous one
            
            za = math.floor(sides/2) 
            
            if isabase:
                za = za+1
            if even:
                q = 3*za
                if isstickout:
                    q= q+1
                decosmap.append(za)
                decosmapr.append(q)
                                        
            else:
                if isstickout:
                    sk =1
                else:
                    sk=0
                z1 = za+1
                q = (3*za)+2+sk
                q1 = q-1
                decosmap.append(za)
                decosmap.append(z1)
                decosmapr.append(q)
                decosmapr.append(q1)
           
        return spathlist,smap,smapr,tmap,decosmap,decosmapr   #the function returns a path list for the side, a scoremap, a reverse score map and a tab map.     
            
    def holenodes(self,xlist,ylist, baseht, basewd,roofangle,isabase):  #plot the hole part
        hpathlist = []
        hpath =[]
        halfbase = .5*basewd
        
        #increase the hole size just a bit to accommodate paper thickness.
        #since xlist and ylist have the values for the shape, we do not need to account for the base separately.
        #except for where we begin and end
        
        for i in range(len(ylist)):
            #calculate stretched y)
            oldy = baseht+(-ylist[i])
            
            if oldy ==0 :
                hpath=(Vector2d(xlist[i],ylist[i]))
            else:
                newy = (self.geo_b_alpha_c(oldy,90-roofangle))-baseht                
                hpath = Vector2d(xlist[i],-newy)
            hpathlist.append(hpath)
        hpath = hpathlist[0]
        hpathlist.append(hpath)
        return hpathlist

       

    def frontnodes(self,xlist,ylist,stickout,width,baseht,notop):
        #we already have our front nodes.  They are in xlist and ylist
        #so just put them into fpathlist and make a tab and score list
        # the only addition here is that if we have a "stickout" then we are going to add in a bottom piece that extends downward a distance of stickout and is the width of the dormer. 
        
        if math.isclose(baseht,0,abs_tol=1e-09):
            isabase = False
        else:
            isabase = True
        fpathlist =[]
        fshortlist = []   #used for cutout    
        tmap = []
        smap = []
        smapr = []
        t=0
        if notop:
            xlist =[]
            ylist = []
            xx = [width/2,-width/2,-width/2,width/2]
            yy = [baseht,baseht,0,0]
            xlist.extend(xx)
            ylist.extend(yy)
           
        
        for i in range(len(xlist)):
            fpath = Vector2d(xlist[i],ylist[i])
            fpathlist.append(fpath)
            fshortlist.append(fpath)
        ept = fshortlist[0]
        fshortlist.append(ept)
        if stickout>0:
            if isabase:
                fpathlist.insert(1,Vector2d(width/2,baseht+stickout))
                fpathlist.insert(2,Vector2d(-width/2,baseht+stickout))
                smap.append(0)
                smapr.append(3)  #need a scoreline to fold stickout under
            else:
                fpathlist.insert(0,Vector2d(width/2,baseht+stickout))
                fpathlist.insert(1,Vector2d(-width/2,baseht+stickout))
                smap.append(len(fpathlist)-1)
                smapr.append(2)  #need a scoreline to fold stickout under
            

        

        #need to set up the tabs -- basically tabs on all the segment edges 
        for i in range(1,len(fpathlist)):
            ck = 1
            tmap.append(i)
        #see what is in these paths
    

    
        return fpathlist,fshortlist,smap,smapr,tmap

    def roofsidenodes(self,halfdepth,side_inset_ht,bbx,bty,roofpeak,isbarn):
        rsidepathlist = []
        #btx = bdratio*halfdepth  
        #bty = roofpeak*bhratio  
        #bbx = halfdepth - btx           
        #bby = roofpeak-bty   
        #fixed 12-31-2021
        smap = []
        smapr = []
        if  not isbarn: # not a barn
            rsidepath = Vector2d(0,0)
            rsidepathlist.append(rsidepath) #0
            rsidepath = Vector2d(halfdepth,side_inset_ht)
            rsidepathlist.append(rsidepath) #1
            rsidepath = Vector2d(-halfdepth,side_inset_ht)
            rsidepathlist.append(rsidepath) #2
            rsidepath = Vector2d(0,0)
            rsidepathlist.append(rsidepath) #3
            tmap = [1,2]
            smap =[]
            smapr = []
            
        else: #is a barn
            rsidepath = Vector2d(0,0)
            rsidepathlist.append(rsidepath) #0
            
            rsidepath = Vector2d(bbx,bty)
            rsidepathlist.append(rsidepath) #1
            
            rsidepath = Vector2d(halfdepth,roofpeak)
            rsidepathlist.append(rsidepath) #2
            
            rsidepath = Vector2d(-halfdepth,roofpeak)
            rsidepathlist.append(rsidepath) #3
            
            rsidepath = Vector2d(-bbx,bty)
            rsidepathlist.append(rsidepath) #4 
            
            rsidepath = Vector2d(0,0) #back to origin
            rsidepathlist.append(rsidepath) #5
            
            tmap = [1,2,3,4,5]
            
            #smap =[1]
            #smapr = [4]
        
        return rsidepathlist,smap,smapr,tmap

    def roofmainnodes(self,roof_inset,roof_top_width,roofwidth,roof_actual_ht,bbx,bby,btx,bty,bb_ln,bt_ln,isbarn):
        smap=[]
        smapr=[]
        tmap = []
        rpathlist=[]
        if not(isbarn):
            rpath = Vector2d(roof_inset,0) #0
            rpathlist.append(rpath)
            
            rpath = Vector2d(roof_inset+roof_top_width,0)
            rpathlist.append(rpath) #1
            
            rpath = Vector2d(roofwidth,roof_actual_ht)
            rpathlist.append(rpath) #2
            
            rpath = Vector2d(0,roof_actual_ht)
            rpathlist.append(rpath) #3
            
            rpath = Vector2d(roof_inset,0)
            rpathlist.append(rpath) #4
            tmap.append(1)
            tmap.append(3)
                    
        else:
            
            rpathlist =[]
            bbtoty = bb_ln+bt_ln
            rpath = Vector2d(0,0)
            rpathlist.append(rpath) #0
            rpath = Vector2d(roofwidth,0)
            rpathlist.append(rpath) #1
            rpath = Vector2d(roofwidth,bt_ln)
            rpathlist.append(rpath) #2
            rpath = Vector2d(roofwidth,bbtoty)
            rpathlist.append(rpath) #3
            rpath = Vector2d(0,bbtoty)
            rpathlist.append(rpath) #4
            rpath = Vector2d(0,bt_ln)
            rpathlist.append(rpath) #5
            rpath = Vector2d(0,0)
            rpathlist.append(rpath) #6
            smap.append(2)   #one end of score mark
            smapr.append(5)  #other end of score mark
            tmap.append(1)
            tmap.append(4)       
        return rpathlist,smap,smapr, tmap
        
    def makeChimney(self,rp,rd,ch,cw,cd,oc):
        chholelist = []
        mypath = pathStruct()
        tmap = [1,2,3,4,5]
        smap =[1]
        smapr = [5]
        chpathlist =[]
        fslant = 0
        bslant = 0
        ra = self.geo_a_b_alpha(rp,rd)	#roof angle
        ca = 90-ra                      #outside angle

        fsd = oc*cd #proportion toward front.
        
        bsd = cd-fsd  #the rest 
        
        bsh = self.geo_a_alpha_b(bsd, ca) #back side height
        
        fsh = self.geo_a_alpha_b(fsd,ca)  #front side height 
        

        chhole = Vector2d(0,0)
        chholelist.append(chhole)
        if fsd> 0:
            fslant = self.geo_a_b_c(fsd,fsh)
        if bsd >0:
           bslant = self.geo_a_b_c(bsd,bsh)
           chhole = Vector2d(bslant,0)
           chholelist.append(chhole)
        chhole = Vector2d(bslant+fslant, 0)
        chholelist.append(chhole)
        chhole = Vector2d(bslant+fslant,cw)
        chholelist.append(chhole)
        if bsd > 0:
            chhole = Vector2d(bslant,cw)
            chholelist.append(chhole)
        chhole = Vector2d(0,cw)
        chholelist.append(chhole)
        chhole = Vector2d(0,0)
        chholelist.append(chhole)
        if (bsd > 0) and (fsd >0):
            chholescore = [1]
            chholescore2 = [4]
        
            
        cpathx = [0, bsd, cd, cd+cw,  cw+(2*cd)-bsd, (2*cd)+cw, 2*(cd+cw)]
        cpathy = [ch+bsh,ch,ch+fsh,ch+fsh,ch,ch+bsh,ch+bsh]
        
        mypath.path.append(Move(0,0))
        rpath = Vector2d(0,0)
        chpathlist.append(rpath)
        
        plen = len(cpathx)
        for i in range(1,plen):
            if cpathx[i]  != mypath.path[-1].x:
                mypath.path.append(Line(cpathx[i],0))
                rpath = Vector2d(cpathx[i],0)
                chpathlist.append(rpath)
                
        for i in reversed(range(plen)):
            yp = cpathy[i]
            if not ((cpathx[i] == mypath.path[-1].x) and  (yp == mypath.path[-1].y)):
                mypath.path.append(Line(cpathx[i],yp))
                rpath = Vector2d(cpathx[i],yp)
                chpathlist.append(rpath)
        mypath.path.append(ZoneClose())
        rpath = Vector2d(0,0)
        chpathlist.append(rpath)
        if len(chpathlist) == 11:  #this is not off-center
            smap = [1,2,3]
            smapr = [8,7,6]
            tmap = [5,6,7,8,9]
        else:
            tmap= [7,8,9,10,11,12,13]
            smap = [2,3,5]
            smapr = [11,10,8]
            
            
        #and the hole template:
        #add a node to the end so it cuts fully
        cj = chholelist[0]
        chholelist.append(cj)
        return(chpathlist,smap,smapr,tmap,chholelist,chholescore,chholescore2)
        
        
    def roofbasenodes(self,roofwidth,roofdepth):
        smap=[]
        smapr=[]
        tmap = []
        rbaselist=[]
        rpath = Vector2d(0,0) #0
        rbaselist.append(rpath)
        
        rpath = Vector2d(roofwidth,0)
        rbaselist.append(rpath) #1
        
        rpath = Vector2d(roofwidth,roofdepth)
        rbaselist.append(rpath) #2
        
        rpath = Vector2d(0,roofdepth)
        rbaselist.append(rpath) #3
        
        rpath = Vector2d(0,0)
        rbaselist.append(rpath) #4
        return rbaselist


        
    def effect(self):
        ###############################################      
        ###START ROOF MAKER PROPER
        scale = self.svg.unittouu('1'+self.options.unit)
        layer = self.svg.get_current_layer()
        
        #Get the input options 
        if self.options.isbarn == "True":
            isbarn = True
        else:
            isbarn = False

        inset_only = False
        dormerht = float(self.options.dormerht)*scale
        dormertopht = float(self.options.dormertopht)*scale
        sides = int(self.options.sides)
        basewidth  = float(self.options.basewidth)*scale
        roofpeak  = float(self.options.roofpeak)*scale
        roofdepth = float(self.options.roofdepth)*scale
        roofwidth = float(self.options.roofwidth)*scale
        roof_inset  = float(self.options.roof_inset)*scale
        basecutout = float(self.options.basecutout)*scale
        bhratio = float(self.options.bhratio)
        bdratio = float(self.options.bdratio)
        stickout = float(self.options.stickout)*scale
        paper = float(self.options.paper) * scale * 2.0
        window_frame = float(self.options.window_frame)
        scoretype = self.options.scoretype
        chimney_ht = float(self.options.chimney_ht)*scale
        chimney_wd = float(self.options.chimney_wd)*scale
        chimney_depth =float(self.options.chimney_depth)*scale
        off_center = float(self.options.off_center)
        shrink = float(self.options.shrink)
        #Set some defaults
        notop = math.isclose(dormertopht,0,abs_tol=1e-09)
        mincutout = 1*scale #used for cutout in roof base
        tabht = 0.25*scale
        if scoretype == "dash":
            dashln = 0.1*scale
        else:
            dashln = 0
        tabangle = 45
        struct_style   = {'stroke':'#000000','stroke-width':'0.25','fill':'#ffd5d5'}
        deco_style = {'stroke':'#000000','stroke-width':'0.25','fill':'#80e5ff'}
        hole_style = {'stroke':'#000000','stroke-width':'0.25','fill':'#aaaaaa'}
        
        #initialize some variables
        btx = bty = bbx = bby = bt_ln = 0
        
        xlist =[]
        ylist = []
        outsetslist = []
        rpathlist = []
        chpathlist =[]
        cutout = 0
        dmult = 1.04
        sidescores = []
        sidescores2 = []
        sidetabs = []
        side_deco_scores =[]
        side_deco_scores2 = []
        emptyset = []
        isabase = True
        if math.isclose(dormerht,0,abs_tol=1e-09):
            dodormers = False
        else:
            dodormers = True
            if (dormertopht > dormerht):  #don't allow nonsensical number the top can't be larger than the whole thing
                dormertopht = dormerht
            baseht = dormerht - dormertopht
            if math.isclose(baseht,0,abs_tol=1e-09):
                isabase = False
            else:
                isabase = True
            dhalfwidth = .5*basewidth

        ##initial calculations

        if math.isclose(roof_inset,0,abs_tol=1e-09):
            no_inset = True
        else:
            no_inset = False

        halfdepth = roofdepth/2
        base_angle = self.geo_a_b_alpha(roofpeak, halfdepth)
        roof_actual_ht = self.geo_a_b_c(roofpeak, roofdepth/2)
        roof_inset_ht = self.geo_a_b_c(roof_actual_ht,roof_inset)
        roof_top_width = roofwidth-(2*roof_inset)
               
        if no_inset:
            side_inset_ht = roofpeak
        else :
            side_inset_ht = self.geo_c_a_b(roof_inset_ht, halfdepth)
        self.ellipseg(72,144,5)
        #Do some dormer calculations
        mkpath = True

            
        if dodormers:
            sidelen = 0
            peaky=0
            xlist, ylist,lenlist = self.nodesloc(basewidth,baseht,dormertopht,sides,isabase,notop)

        #Now the roof proper    
        btx = bdratio*halfdepth  
        bty = roofpeak*bhratio  
        
        bbx = halfdepth - btx           
        bby = roofpeak-bty   
        if (isbarn):
            barn_base_angle = self.geo_a_b_alpha(bby, bbx)
        bt_ln = self.geo_a_b_c(bbx,bty) 
        #fixed 12-31-2021
        bb_ln = self.geo_a_b_c( btx,bby) 
        #fixed 12-31-2021
        bbtoty = bt_ln + bb_ln          
        
        
        zerotab = False
        #start construction
        
        #ROOF BASE
        mincutout= tabht
        maxcutout1 = .5*roofwidth
        maxcutout2 = .5*roofdepth
        maxcutout = min(maxcutout1,maxcutout2)
        if (basecutout < mincutout):
            basecutout = mincutout
        if (basecutout >= maxcutout):
            basecutout = 0
            
        ctout = basecutout
        
        cutout = -ctout
        zerotab = False
        roofbaselist = self.roofbasenodes(roofwidth,roofdepth)
        roofbasecutout = copy.deepcopy(roofbaselist)
        
        #no scorelines, no tabs, just an inset
        svgroofbase = self.stringmeup(roofbaselist,emptyset,emptyset,emptyset, zerotab,cutout,roofbasecutout,"Roof_Base",layer,struct_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
                                    
        
        #ROOF SIDE AND ROOF SIDE DECO
        cutout = 0
        inset_only = False
        roofsidelist,roofsidescore,roofsidescore2,roofsidetabs = self.roofsidenodes(halfdepth,side_inset_ht,bbx,bty,roofpeak,isbarn)
        #fixed 12-31-2021
        zerotab = True
        
        svgroofside = self.stringmeup(roofsidelist,roofsidescore,roofsidescore2,roofsidetabs,zerotab,cutout,emptyset,"Side_of_Roof",layer,struct_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
        svgroofside = self.stringmeup(roofsidelist,roofsidescore,roofsidescore2,roofsidetabs,zerotab,cutout,emptyset,"Side_of_Roof2",layer,struct_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
        zerotab = False
        svgroofside_deco = self.stringmeup(roofsidelist,roofsidescore, roofsidescore2,emptyset,zerotab,0,emptyset,"Side_of_RoofDeco",layer,deco_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
        svgroofside_deco = self.stringmeup(roofsidelist,roofsidescore, roofsidescore2,emptyset,zerotab,0,emptyset,"Side_of_RoofDeco2",layer,deco_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
         
        #ROOF MAIN, ROOF MAIN 2 AND ROOF MAIN DECO
        roofmainlist,roofmainscore,roofmainscore2,roofmaintabs = self.roofmainnodes(roof_inset,roof_top_width,roofwidth,roof_actual_ht,bbx,bby,btx,bty,bb_ln,bt_ln,isbarn)
        zerotab = False
        svgroofmain = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,roofmaintabs,zerotab,cutout,emptyset,"Main_Roof",layer,struct_style,tabht,dashln,tabangle,not mkpath,inset_only,isabase)
        #remove the top tab on this one,but leave the bottom
        roofmaintabs.pop(0)
        svgroofmain2 = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,roofmaintabs,zerotab,cutout,emptyset,"Main_Roof_2",layer,struct_style,tabht,dashln,tabangle,not mkpath,inset_only,isabase)
        zerotab = False
        svgroofmain_deco = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,emptyset,zerotab,0,roofmainlist,"Main_Roof_Deco",layer,deco_style,tabht,dashln,tabangle,not mkpath,inset_only,isabase)
        svgroofmain_deco = self.stringmeup(roofmainlist,roofmainscore, roofmainscore2,emptyset,zerotab,0,roofmainlist,"Main_Roof_Deco2",layer,deco_style,tabht,dashln,tabangle,not mkpath,inset_only,isabase)
        if dodormers:
             #DORMERS FRONT PANE, FRONT AND FRONT DECO
            window_inset = window_frame*basewidth
            if (window_inset> dhalfwidth) or  (window_inset>.5 * peaky):
                window_inset = window_frame * min(dhalfwidth*.75, peaky) 
            if peaky == 0:
                window_inset = window_frame*basewidth
            cutout = -window_inset
            
            frontlist,frontshortlist,frontscore,frontscore2,fronttabs = self.frontnodes(xlist,ylist,stickout,basewidth,baseht,notop) #front of dormer        
            zerotab = True  #add a tab between start and end nodes
            svgfront = self.stringmeup(frontlist,frontscore,frontscore2,fronttabs,zerotab,cutout,frontshortlist,"Front_Path",layer,struct_style,tabht,dashln/2,tabangle,mkpath,inset_only,isabase)
            
            #DOING DECO
            frontshortlist2 = copy.deepcopy(frontshortlist)
            svgfront_deco = self.stringmeup(frontshortlist,emptyset,emptyset,emptyset,not zerotab,cutout,frontshortlist2,"Front_Deco_Path",layer,deco_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
            
            #HOLE 12-30
            if (isbarn):
                base_angle = barn_base_angle
            
            holepathlist = self.holenodes(xlist,ylist,baseht,basewidth,base_angle,isabase) #hole path
            
            
            inset_only = True
            holecutlist = copy.deepcopy(holepathlist)
            #for the cutout to work we need to add the last node equal first
            
            self.stringmeup(holepathlist,emptyset,emptyset,emptyset,0,paper,holecutlist,"Hole",layer,hole_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
            inset_only = False
            #DORMER SIDE
            #
            #alter svgside to allow us to retrieve the decorative scorelines as well: decosmap and decosmapr

            sidepathlist,sidescores,sidescores2,sidetabs,decosmap,decosmapr = self.sidenodes(lenlist,ylist,xlist,isabase,base_angle,baseht,stickout,sides,notop,basewidth) #side of dormer
            
            zerotab = False
            cutout = 0
            
            # 
            svgside = self.stringmeup(sidepathlist,sidescores,sidescores2,sidetabs,zerotab,cutout,emptyset,"Dormer_Side",layer,struct_style,tabht,dashln/2,tabangle/2,mkpath,inset_only,isabase)
            #now draw the decorative piece and score lines
            svgside_deco = self.stringmeup(sidepathlist,decosmap,decosmapr,emptyset,zerotab,cutout,emptyset,"Dormer_Side_Deco",layer,deco_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
            
        #CHIMNEY
        
        if not( (chimney_wd==0) or (chimney_depth==0) or chimney_ht ==0):
            chimneylist,chscores, chscores2,chtabs,chholelist,chholescore,chholescore2=self.makeChimney(roofpeak,roofdepth,chimney_ht,chimney_wd,chimney_depth,off_center)
            zerotab = False
            cutout = 0
            chimneypiece = self.stringmeup(chimneylist,chscores,chscores2, chtabs,zerotab,cutout,chimneylist,"Chimney",layer,struct_style,tabht*shrink,dashln*shrink,tabangle*shrink,mkpath,inset_only,isabase)
            chimneylist2 = copy.deepcopy(chimneylist)
            chimneypiece2 = self.stringmeup(chimneylist,chscores,chscores2, emptyset,zerotab,cutout,chimneylist,"Chimneydeco",layer,deco_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
            inset_only = True
            cutout = -paper
            #test
            chholelist = self.stringmeup(chholelist,chholescore,chholescore2, emptyset,zerotab,cutout,chholelist,"Chimneyhole",layer,hole_style,tabht,dashln,tabangle,mkpath,inset_only,isabase)
            
if __name__ == '__main__':
    Roofmaker().run()
