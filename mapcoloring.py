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

import itertools,collections
colorSource=itertools.count()

# Used to determine how many islands there are in the map. There'll be one color if the whole map is connected.
class MapColorizer(object):
	def __init__(self,rooms):
		self.rooms=crooms=[]
		for i,room in enumerate(rooms):
			crooms.append(ColoredRoom(i,room,crooms))
	def colorize(self):
		for room in self.rooms:
			room.colorTouched(colorSource.next())
			
		for room in self.rooms:
			room.unlink()

		return self.differentColors()
	def differentColors(self):
		colors=collections.defaultdict(list)
		for room in self.rooms:
			colors[room.color].append(room)
		return colors
	def dump(self,colorMap):
		for key in sorted(colorMap.keys()):
			print key,':',colorMap[key]
			
class ColoredRoom(object):
	def __init__(self,i,room,rooms):
		self.room=room
		self.rooms=rooms
		self.color=None
		self.index=i
		self.connected=set([i])
	def colorTouched(self,color):
		if self.color is not None:
			return
		self.color=color
		rooms=self.rooms
		for otheri in self.room.connected:
			rooms[otheri].colorTouched(color)
	def unlink(self):
		del self.rooms
