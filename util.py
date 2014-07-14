#!/usr/bin/python
#		microgue, a simple curses-based roguelike
#		Copyright (C) 2010 Philip D. Bober
# 
#		This program is free software: you can redistribute it and/or modify
#		it under the terms of the GNU General Public License as published by
#		the Free Software Foundation, either version 3 of the License, or
#		(at your option) any later version.
# 
#		This program is distributed in the hope that it will be useful,
#		but WITHOUT ANY WARRANTY; without even the implied warranty of
#		MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
#		GNU General Public License for more details.
# 
#		You should have received a copy of the GNU General Public License
#		along with this program.	If not, see <http://www.gnu.org/licenses/>.

import sys,re,random
try:
	import cStringIO as StringIO #@UnusedImport
except:
	import StringIO #@Reimport
import geometry

class FailedToConnect(Exception):
	pass
MAXITERATIONS=200
class StatusDiversion(object):
	def __init__(self,screen):
		self.screen=screen
	def __enter__(self):
		self.message=self.screen.getStatus()
	def __exit__(self,excType,val,tb):
		if excType is None:
			self.screen.setStatus(self.message)

class StdoutRedirect(object):
	def __enter__(self):
		self.savedOrginalStdout=sys.stdout
		sys.stdout=StringIO.StringIO()
		return self
	def __exit__(self,excType,val,tb):
		if excType is not None:
			redirected=sys.stdout
			stdout=sys.stdout=self.savedOrginalStdout
			stdout.write(redirected.getvalue())
	def getLastScreenful(self,w,h):
		lines=[]
		for line in sys.stdout.getvalue().rsplit('\n',h)[-h:]: 
			if not line:
				lines.append('') # special case blank lines, since the below split ignores them (range(0,0,n) is empty!)
			lines.extend(line[i:i+w] for i in range(0,len(line),w)) # split overlong lines into multiple lines
		lines=lines[-h:] # trim back to the last height-2 lines, since we may have more now that overlong lines have been wrapped
		return lines

def firstValid(pred,func,*args,**kwargs):
	iter=0
	ret=func(*args,**kwargs)
	while not pred(ret):
		iter+=1
		if iter>MAXITERATIONS:
			raise FailedToConnect()
		ret=func(*args,**kwargs)
	return ret 
def distSquared(p1,p2):
	dx,dy=p1[0]-p2[0],p1[1]-p2[1]
	return dx*dx+dy*dy
def closest(target,points):
	smallestDist=None
	for point in points:
		dist=distSquared(target,point)
		if smallestDist is None or dist<smallestDist[0]:
			smallestDist=(dist,point)
	return smallestDist[1]
def farAway(pos,under,*oposes):
	underSquared=under*under
	for opos in oposes:
		if distSquared(pos,opos)<underSquared:
			return False # too close
	return True # nothing was under the distance
def findTwoClosestPoints(p1s,p2s):
	smallestPair=None
	for p1 in p1s:
		for p2 in p2s:
			dist=distSquared(p1,p2)
			if smallestPair is None or dist<smallestPair[0]:
				smallestPair=(dist,p1,p2)
	return smallestPair[1:]

class Theme():
	def __init__(self,data):
		self.top,_,self.bottom=lines=[data[i:i+3] for i in (0,3,6)]
		self.left,self.right=''.join(x[0] for x in lines),''.join(x[2] for x in lines)
		self.hallway=data[9:11]+data[9]
		self.floor=data[4]
	def __str__(self):
		data=''.join(getattr(self,key) for key in 'top left right bottom hallway floor'.split())
		template="""
<Theme:
   012      C
 3     6    D
 4  F  7  CDDDC
 5     8    D
   9AB      C
>"""
		return re.sub('[0-9A-F]',lambda m:data[int(m.group(0),16)],template.strip())

def shuffled(seq):
	temp=list(seq)
	random.shuffle(temp)
	return temp

def mergeShortLines(lines,width,separator='  '):
	running=[]
	for item in lines:
		line=separator.join(running+[item])
		if len(line)>width:
			yield separator.join(running)
			running=[item]
		else:
			running.append(item)
	if running:
		yield separator.join(running)

def rectDump(filename,rect1,rect2=None,rect3=None):
	rects=[r for r in (rect1,rect2,rect3) if r is not None]
	w,h=size=geometry.getContainingRect(*rects).extend(6,6).lowerRight
	data=[[[0,0,0] for _x in range(w)] for _y in range(h)]
	for i,r in enumerate(rects):
		for x,y in r.points:
			data[y][x][i]=255
	with open(filename,'w') as f:
		print >>f,'P3'
		print >>f,'%i %i' % size
		print >>f,'255'
		for y in range(h):
			print >>f,' '.join([('%i %i %i' % tuple(c)) for c in data[y]])
