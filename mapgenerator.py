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

import sys,pickle,string
from random import randint,choice,sample
from util import *
from geometry import Rect,getContainingRect
from mapcoloring import MapColorizer
MINROOMRATIO=0.55
MAXROOMRATIO=sys.maxint
LEVELBORDER=2
ROOMBORDER=4
HALLLENGTHH=12
HALLLENGTHV=5


MAXITERATIONS=50


THEME=Theme("+-+"
						"|.|"
						"+-+"
						"=#"
			)
if '--graphics' in sys.argv:
	THEME=Theme('\xDA' '\xC4' '\xBF'
							'\xB3' '.'    '\xB3'
							'\xc0' '\xC4' '\xD9'
							"\xFE\xB0"
				)

class Room(Rect):
	def __init__(self,params):
		Rect.__init__(self,params)
		self.connected=set()
	def possibleHallways(self,levelRect):
		edges=(
			(-1, 0,HALLLENGTHH,Hallway(self.leftEdge)),
			(+1, 0,HALLLENGTHH,Hallway(self.rightEdge)),
			( 0,-1,HALLLENGTHV,Hallway(self.topEdge)),
			( 0,+1,HALLLENGTHV,Hallway(self.bottomEdge))
		)
		for rx,ry,length,hall in edges:
			hall.owner=self
			hall.shift(rx*2,ry*2)
			hall.extend(rx*length,ry*length)
			hall.cropWithin(levelRect)
		return [x[3] for x in edges]	
	def isConnectedTo(self,otheri):
		return otheri in self.connected
	def connectTo(self,rooms,other):
		newi=set(rooms.index(room) for room in (self,other))
		self.connected|=newi
		other.connected|=newi
	def __str__(self):
		return '<Room %s %s>' % (Rect.__str__(self),self.connected)
	def pointsOnEdges(self):
		edges=(
			(-1, 0,self.leftEdge),
			(+1, 0,self.rightEdge),
			( 0,-1,self.topEdge),
			( 0,+1,self.bottomEdge)
		)
		for rx,ry,edge in edges:
			edge.shift(rx,ry)
		return [edge.pickPointWithin() for _,_,edge in edges]
			
class Hallway(Rect): 
	def pickLineIntersecting(self,room,levelRect):
		possible=(
			[Hallway(vline).extendBothWays(0,3).cropWithin(levelRect) for vline in self.vlines] +
			[Hallway(hline).extendBothWays(3,0).cropWithin(levelRect) for hline in self.hlines]
		) 
		
		picks=[adjusted for adjusted in possible if adjusted.overlaps(self.owner) and adjusted.overlaps(room)]
		if picks:
			return choice(picks)
	def truncateUntilNotWithin(self,room):
		if self.w>1:
			if room.x>self.x:
				while self.overlaps(room):
					self[2]-=1
			else:
				while self.overlaps(room):
					self[2]-=1
					self[0]+=1
		else:
			if room.y>self.y:
				while self.overlaps(room):
					self[3]-=1
			else:
				while self.overlaps(room):
					self[3]-=1
					self[1]+=1
	def buildHallway(self,room1,room2):
		self.cropWithin(getContainingRect(room1,room2))
		self.truncateUntilNotWithin(room1)
		self.truncateUntilNotWithin(room2)
		return self
	def isVertical(self):
		return self.h>1

class FreeformHallway(object):
	def __init__(self,p1,p2):
		self.points,self.spots=self.renderToPoints(p1,p2)
	def renderToPoints(self,p1,p2):
		p1x,p1y=p1
		p2x,p2y=p2
		
		print 'freeform',p1,p2
		orig=p1

		moreY=abs(p2y-p1y) > abs(p2x-p1x)
		
		if moreY:
			p1x,p1y=p1y,p1x
			p2x,p2y=p2y,p2x
		if p1x>p2x:
			p1x,p2x=p2x,p1x
			p1y,p2y=p2y,p1y
			
		dx=p2x-p1x
		dy=abs(p2y-p1y)
		error=dx//2
		yStep=1 if p1y<p2y else -1
		
		spots=[]

		y=p1y
		for x in (range(p1x,p2x+1) if p1x<=p2x else range(p1x,p2x-1,-1)):
			spots.append((y,x) if moreY else (x,y))
			error-=dy
			if error<0:
				y+=yStep
				error+=dx
		
		if spots[0]!=orig:
			spots.reverse()
		
		return (p1,p2),spots+[p2]
	def intersectsAny(self,otherRooms):
		spots=self.spots
		for px,py in spots[::5]:
			if Rect(px,py,1,1).overlaps(otherRooms, border=2):
				return True
		return False

class LevelGenerator(object):
	def __init__(self,size,depth,theme=THEME):
		self.size=size
		self.theme=theme
		self.data=self.blankLevel(size)
		self.levelRect=Room(size)
		self.makeRooms(random.choice((4,5,6)))
		self.generateHallways()
		self.generateAdditionalHallways()
	def randomPoint(self):
		return tuple(LEVELBORDER+randint(0,v-LEVELBORDER*2) for v in self.size)
	def blankLevel(self,size):
		w,h=size
		map=[
					[' ' for _x in range(w) ]
					for _y in range(h)
				]
		return map
	def makeRooms(self,numRooms):
		self.rooms=rooms=[]
		for _ in range(numRooms):
			rooms.append(firstValid(self.isValidRoom,self.makeRoom,rooms))
	def makeRoom(self,rooms):
		room=Room(self.randomPoint()+(randint(3,20),randint(3,7)))
		room.fitWithin(self.levelRect)
		return room
	def isValidRoom(self,room):
		return MINROOMRATIO<=room.ratio<=MAXROOMRATIO and not room.overlaps(self.rooms,ROOMBORDER)
	def renderRoom(self,room):
		rx,ry,rw,rh=room.params
		theme=self.theme
		
		self.hline(rx-1 ,ry-1 ,rw+2,theme.top   )
		self.hline(rx-1 ,ry+rh,rw+2,theme.bottom)
		self.vline(rx-1 ,ry-1 ,rh+2,theme.left  )
		self.vline(rx+rw,ry-1 ,rh+2,theme.right )
	def renderHallway(self,hall):
		theme=self.theme
		if hall.isVertical():
			self.vline(hall.x,hall.y,hall.h,theme.hallway)
		else:
			self.hline(hall.x,hall.y,hall.w,theme.hallway)
	def renderInterior(self,room):
		c=self.theme.floor
		rx,ry,rw,rh=room.params
		for y in range(ry,ry+rh):
			self.data[y][rx:rx+rw]=[c]*(rw)
	def renderFreeformHallway(self,hall):
		start,middle,end=self.theme.hallway
		for x,y in hall.spots:
			self.data[y][x]=middle
		for (x,y),t in zip(hall.points,start+end):
			self.data[y][x]=t
	def render(self,withPossibles=False,theme=THEME):
		for room in self.rooms:
			self.renderInterior(room)
			self.renderRoom(room)
		for hallway in self.hallways:
			self.renderHallway(hallway)
		for freeform in self.freeformHallways:
			self.renderFreeformHallway(freeform)
		return self.data
	def hline(self,x,y,w,chars):
		line=self.data[y]
		line[x]=chars[0]
		line[x+w-1]=chars[2]
		for i in range(x+1,x+w-1):
			line[i]=chars[1]
	def vline(self,x,y,h,chars):
		data=self.data
		data[y][x]=chars[0]
		data[y+h-1][x]=chars[2]
		for i in range(y+1,y+h-1):
			data[i][x]=chars[1]
	def pickPointWithinARoom(self):
		return choice(self.rooms).pickPointWithin()
	def generateHallways(self):
		self.findLikelyConnections()
	def isMapFullyConnected(self):
		return len(MapColorizer(self.rooms).colorize())==1
	def findLikelyConnections(self):
		levelRect=self.levelRect
		rooms=[
				(room,room.possibleHallways(levelRect))
				 for room in self.rooms
		]
		self.hallways=savedHallways=[]
		for room,hallways in rooms:
			ohallsList=sum([ohalls for (_,ohalls) in rooms if ohalls is not hallways],[])
			room.hallways=room.possibleHallways(self.levelRect)
			possibles=[hall for hall in hallways if hall.overlaps(ohallsList)]
			for hall in possibles:
				for other in ohallsList:
					if hall.overlaps(other):
						if hall.overlaps(other.owner):
							if not room.isConnectedTo(self.rooms.index(other.owner)):
								picked=hall.pickLineIntersecting(other.owner,levelRect)
								if picked is not None:
									savedHallways.append(picked.buildHallway(room,other.owner))
									room.connectTo(self.rooms,other.owner)
	def generateAdditionalHallways(self):
		self.freeformHallways=[]
		while not self.isMapFullyConnected():
			self.connectIslandsWithHallway(*self.pickTwoDisconnectedIslands())
	def pickTwoDisconnectedIslands(self):
		return sample(MapColorizer(self.rooms).colorize().values(),2)
	def annotatePoints(self,points,owner):
		return [(x,y,owner) for (x,y) in points]
	def deannottatePoints(self,points):
		return [(x,y) for (x,y,_) in points]
	def connectIslandsWithHallway(self,i1,i2):
		iterations=0
		bad=True
		while bad:
			iterations+=1
			if iterations>MAXITERATIONS:
				raise FailedToConnect()
			r1p=sum([self.annotatePoints(ri.room.pointsOnEdges(),ri)for ri in i1],[])
			r2p=sum([self.annotatePoints(ri.room.pointsOnEdges(),ri) for ri in i2],[])
			p1,p2=findTwoClosestPoints(r1p,r2p)
			hallway=FreeformHallway(p1[0:2],p2[0:2])
			
			if not hallway.intersectsAny([room for room in self.rooms if room is not p1[2].room and room is not p2[2].room]):
				bad=False
			
		self.freeformHallways.append(hallway)
		p1[2].room.connectTo(self.rooms,p2[2].room)
	def save(self,filename,player):
		print 'Saving',filename
		saved=dict(
				size=self.size,
				rooms=[(room.params,room.connected) for room in self.rooms],
				playerPos=player.pos,
				hallways=[hall.params for hall in self.hallways]
		)
		with open(filename,'wb') as f:
			pickle.dump(saved,f)
	def load(self,filename):
		print 'Loading',filename
		with open(filename,'rb') as f:
			saved=pickle.load(f)
		self.size=size=saved['size']
		self.levelRect=Room(size)
		self.rooms=rooms=[]
		for params,connected in saved['rooms']:
			room=Room(params)
			room.connected=connected
			rooms.append(room)
		
		self.data=self.blankLevel(size)
		self.hallways=[Hallway(params) for params in saved['hallways']]
		return saved['playerPos']
	def getFloorCharacters(self):
		return THEME.floor+THEME.hallway[0:2]

if __name__=='__main__':
		import unittest
		class TestHallWay(unittest.TestCase):
			def testTruncateUntilWithin(self):
				room1=Rect(5+0,5+0,5,5)
				room2=Rect(5+7,5+2,5,5)
				hall=Hallway(5-2,5+3,21,1)
				containing=getContainingRect(room1,room2)
				rectDump('out0.ppm',room1,room2,containing)
				rectDump('out1.ppm',room1,room2,hall)
				hall.cropWithin(containing)
				rectDump('out2.ppm',room1,room2,hall)
				hall.truncateUntilNotWithin(room2)
				rectDump('out3.ppm',room1,room2,hall)
				hall.truncateUntilNotWithin(room1)
				rectDump('out4.ppm',room1,room2,hall)
		unittest.main()
		