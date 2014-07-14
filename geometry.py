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

from random import randint
def getContainingRect(*rects):
	lr=tuple(max(r.lowerRight[i] for r in rects) for i in (0,1))
	ul=tuple(min(r.upperLeft[i] for r in rects) for i in (0,1))
	x,y,=ul
	w=lr[0]-x
	h=lr[1]-y
	return Rect(x,y,w+1,h+1)
	
class Rect(object):
	def __init__(self,*params):
		if len(params)==1:
			params=params[0]
		try:
			x,y,w,h=params
		except ValueError:
			x=y=0
			w,h=params
		self.params=(x,y,w,h)
	def overlaps(self,others,border=0):
		if isinstance(others,Rect): # allow supplying a single Rect instead of a list
			others=(others,)
		x,y,w,h=self.getBorderedParams(border)
		for other in others:
			ox,oy,ow,oh=other.params
			if not (x>ox+ow-1 or y>oy+oh-1 or x+w-1<ox or y+h-1<oy):
				return True
		return False
	def getBorderedParams(self,border):
		x,y,w,h=self.params
		return (
				x-border,
				y-border,
				w+border*2,
				h+border*2,
		)
	def pickPointWithin(self):
		x,y,w,h=self.params
		return (randint(x,x+w-1),randint(y,y+h-1))
	def fitWithin(self,otherRect):
		lw,lh=otherRect.size
		x,y,w,h=self.params
		if x<0:
			x=0
		if y<0:
			y=0
		if x+w>=lw-1:
			x=lw-2-w
		if y+h>=lh-1:
			y=lh-2-h
		self.params=x,y,w,h
		return self
	def cropWithin(self,otherRect):
		x,y,w,h=self.params
		ox,oy,ow,oh=otherRect.params
		nx,ny=max(x,ox),max(y,oy)
		ncx,ncy=min(x+w,ox+ow),min(y+h,oy+oh)
		nw,nh=max(0,ncx-nx),max(0,ncy-ny)
		self.params=(nx,ny,nw,nh)
		return self
	def shift(self,rx,ry):
		x,y,w,h=self.params
		self.params=(x+rx,y+ry,w,h)
		return self
	def extend(self,rx,ry):
		x,y,w,h=self.params
		if rx<0:
			x+=rx
			w-=rx
		else:
			w+=rx
		if ry<0:
			y+=ry
			h-=ry
		else:
			h+=ry
		self.params=(x,y,w,h)
		return self # chaining yo
	def extendBothWays(self,rx,ry):
		self.extend(rx,ry)
		self.extend(-rx,-ry)
		return self
	def __str__(self):
		return '<Rect (%i,%i) %ix%i>' % self.params
	def __repr__(self):
		return 'Rect(%i,%i,%i,%i)' % self.params
	def __eq__(self,other):
		return self.params==other.params
	def __getitem__(self,i):
		return self.params[i]
	def __setitem__(self,i,nv): # woefully inefficient if you actually do this a lot. Don't.
		params=list(self.params)
		params[i]=nv
		self.params=tuple(params)
	def __len__(self):
		return 4
	
	@property
	def size(self):
		return self.params[2:4]
	@property
	def pos(self):
		return self.params[0:2]
	@property
	def x(self):
		return self.params[0]
	@property
	def y(self):
		return self. params[1]
	@property
	def w(self):
		return self.params[2]
	@property
	def h(self):
		return self.params[3]
	@property
	def ratio(self):
		return float(self.params[2])/float(self.params[3])
	@property
	def leftEdge(self):
		x,y,_,h=self.params
		return Rect(x,y,1,h)
	@property
	def rightEdge(self):
		x,y,w,h=self.params
		return Rect(x+w-1,y,1,h)
	@property
	def bottomEdge(self):
		x,y,w,h=self.params
		return Rect(x,y+h-1,w,1)
	@property
	def topEdge(self):
		x,y,w,_=self.params
		return Rect(x,y,w,1)
	@property
	def empty(self):
		return self.params[2]==0 or self.params[3]==0
	@property
	def lowerRight(self):
		x,y,w,h=self.params
		return (x+w-1,y+h-1)
	@property
	def upperLeft(self):
		return self.pos
	@property
	def hlines(self):
		out=[]
		x,y,w,h=self.params
		for i in range(y,y+h):
			out.append(Rect(x,i,w,1))
		return out
	@property
	def vlines(self):
		out=[]
		x,y,w,h=self.params
		for i in range(x,x+w):
			out.append(Rect(i,y,1,h))
		return out
	@property
	def points(self):
		rx,ry,w,h=self.params
		for y in range(ry,ry+h):
			for x in range(rx,rx+w):
				yield x,y
if __name__=='__main__':
	import unittest
	
	class TestRect(unittest.TestCase):
		def testOverlaps(self):
			r=Rect(0,0,5,5)
			r2=Rect(0,5,1,1)
			self.assertFalse(r.overlaps(r2))
			self.assertFalse(r2.overlaps(r))
		def testCropWithinEquals(self):
			r=Rect(0,0,10,10)
			r2=Rect(0,0,10,10)
			r.cropWithin(r2)
			self.assertEquals(Rect(0,0,10,10),r)
			self.assertEquals(Rect(0,0,10,10),r2)
			self.assertEquals(r,r2)
		def testCropWithinCorner(self):
			r=Rect(0,0,10,10)
			r2=Rect(5,5,10,10)
			r.cropWithin(r2)
			self.assertEquals(Rect(5,5,5,5),r)
		def testCropWithinDisjoint(self):
			r=Rect(0,0,10,10)
			r2=Rect(25,25,10,10)
			r.cropWithin(r2)
			self.assertTrue(r.empty)
		def testCropWithinTouching(self):
			r=Rect(0,0,10,10)
			r2=Rect(0,10,10,10)
			r.cropWithin(r2)
			self.assertTrue(r.empty)
		def testExtend(self):
			r=Rect(5,5,1,1)
			r.extend(1,0)
			self.assertEquals(Rect(5,5,2,1),r)

			r=Rect(5,5,1,1)
			r.extend(-1,0)
			self.assertEquals(Rect(4,5,2,1),r)

			r=Rect(5,5,1,1)
			r.extend(0,+1)
			self.assertEquals(Rect(5,5,1,2),r)

			r=Rect(5,5,1,1)
			r.extend(0,-1)
			self.assertEquals(Rect(5,4,1,2),r)
			
			r=Rect(5,5,1,1)
			r.extend(0,-1)
			self.assertEquals(Rect(5,4,1,2),r)
			r.extend(0,1)
			self.assertEquals(Rect(5,4,1,3),r)
		def testIndexing(self):
			r=Rect(1,2,3,4)
			self.assertEquals(1,r[0])
			self.assertEquals(2,r[1])
			self.assertEquals(3,r[2])
			self.assertEquals(4,r[3])
		def testClone(self):
			r=Rect(1,2,3,4)
			r2=Rect(r)
			self.assertEquals(r,r2)
			self.assertFalse(r is r2)
		def testVlines(self):
			r=Rect(5,5,3,3)
			vlines=r.vlines
			self.assertEquals(Rect(5,5,1,3),vlines[0])
			self.assertEquals(Rect(6,5,1,3),vlines[1])
			self.assertEquals(Rect(7,5,1,3),vlines[2])
		def testCorners(self):
			r=Rect(3,3,5,5)
			self.assertEquals((3+4,3+4),r.lowerRight)
			self.assertEquals((3,3),r.upperLeft)
			
			r=Rect(3,3,1,1)
			self.assertEquals((3,3),r.lowerRight)
			self.assertEquals((3,3),r.upperLeft)

	unittest.main()