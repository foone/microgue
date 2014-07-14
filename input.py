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

import string
class Key:
	ESC=27
	ENTER=10
	a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z=(ord(c) for c in string.ascii_lowercase)
	A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z=(ord(c) for c in string.ascii_uppercase)
	LESS_THAN=60
	GREATER_THAN=62
	COMMA=44
	
	LOG=L
	QUITS=(q,Q)
	HARDQUIT=Q
	GO_UP=LESS_THAN
	GO_DOWN=GREATER_THAN
	STAIRS=(GO_UP,GO_DOWN)
	GETS=(COMMA,g,G)
	INVENTORIES=(I,i)
	DOT=46
	DIR_N= 56
	DIR_S= 50
	DIR_E= 54
	DIR_W= 52
	DIR_NE=57
	DIR_NW=55
	DIR_SE=51
	DIR_SW=49
	DIR_MIDDLE=53
	DIR_ARROW_UP=   259
	DIR_ARROW_DOWN= 258
	DIR_ARROW_LEFT= 260
	DIR_ARROW_RIGHT=261
	SIMPLE_DIRECTIONS=(DIR_N,DIR_S,DIR_E,DIR_W,DIR_NE,DIR_NW,DIR_SE,DIR_SW)
	DIRS=SIMPLE_DIRECTIONS+(DIR_ARROW_UP,DIR_ARROW_DOWN,DIR_ARROW_LEFT,DIR_ARROW_RIGHT)
	DIRECTION_KEY_ALIASES={
		DIR_ARROW_UP   :DIR_N,
		DIR_ARROW_DOWN :DIR_S,
		DIR_ARROW_LEFT :DIR_W,
		DIR_ARROW_RIGHT:DIR_E,
	}
	DIRECTION_TO_RELATIVE={
			DIR_N: ( 0,-1),DIR_S: ( 0,+1),DIR_E: (+1, 0),DIR_W: (-1, 0),
			DIR_NE:(+1,-1),DIR_NW:(-1,-1),DIR_SE:(+1,+1),DIR_SW:(-1,+1),
	}
	WAITKEYS=(DOT,DIR_MIDDLE)
	@staticmethod
	def dirToRel(dir):
		return Key.DIRECTION_TO_RELATIVE[Key.DIRECTION_KEY_ALIASES.get(dir,dir)]

	@staticmethod
	def codeToChar(code):
		try:
			return chr(code)
		except:
			return ''
