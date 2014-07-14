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

from util import *
from mapgenerator import LevelGenerator,FailedToConnect
import getpass
from input import Key
from monsters import pickMonsters
import random
MINIMUMDISTANCE=10
MINMONSTERDIST=5
MAPFILENAME='../level.dat'

STARTHEALTH=10
STARTGOLD=0
POSTLEVELREGENPERIOD=50
ARTIFACT="the Orb of Destiny"
ARTIFACTCHAR='o'

class Level(object):
	def __init__(self,size,game,depth=1,movedDown=True):
		self.size=size
		self.depth=depth
		self.game=game
		
		self.wrappedInitializeLevel(game,movedDown=True)
	def draw(self,screen,player):
		for y in range(self.size[1]):
			screen.drawMapLine(y,''.join(self.map[y]))
		for object in self.objects+[player]:
			screen.drawObject(object)
		screen.positionCursor(player)
		
	def sortObjects(self):
		out=[]
		for obj in self.objects:
			v=1
			if isinstance(obj,Stair):
				v=5
			if isinstance(obj,Monster):
				v=99
			out.append((v,obj))
		out.sort(key=lambda x:x[0])
		self.objects=[x[1] for x in out]
				
	def isOnScreen(self,pos):
		w,h=self.size
		x,y=pos
		return 0<=x<w and 0<=y<h
	def wrappedInitializeLevel(self,game,movedDown):
		while 1:
			try:
				return self.initializeLevel(game,movedDown)
			except FailedToConnect:
				pass
	def initializeLevel(self,game,generateNew=True,movedDown=False):
		if generateNew:
			
				
			levelGenerator=self.levelGenerator=LevelGenerator(self.size,self.depth)
			playerPos=self.pickedPlayerPos=levelGenerator.pickPointWithinARoom()
		else:
			levelGenerator=self.levelGenerator
			playerPos=self.pickedPlayerPos
		self.map=levelGenerator.render()
		self.floorCharacters=levelGenerator.getFloorCharacters()
		self.changed=True
		
		if self.depth==1:
			upStairPos=playerPos
		else:
			upStairPos=levelGenerator.pickPointWithinARoom()
			playerPos=self.pickedPlayerPos=upStairPos
		downStairPos=self.pickPosAwayFrom(MINIMUMDISTANCE,playerPos,upStairPos)
		
		depth=self.depth
		self.upStair=Stair(upStairPos,'<',game,'up' if depth>1 else 'leave')
		self.downStair=Stair(downStairPos,'>',game,'down')
		
		self.objects=[self.upStair,self.downStair]
		self.createMonsters(game)
	def createMonsters(self,game):
		monsters=[]
		for mType in pickMonsters(self.depth):
			monsters.append(Monster(self.pickPosAwayFrom(MINMONSTERDIST,*[m.pos for m in monsters]),game,mType))
			
		self.objects.extend(monsters)
			
	def pickPosAwayFrom(self,minDist,*awayFrom):
		levelGenerator=self.levelGenerator
		return firstValid(lambda x:farAway(x,minDist,*awayFrom),levelGenerator.pickPointWithinARoom)
	def isEmpty(self,pos):
		x,y=pos
		return self.map[y][x] in (self.floorCharacters)
	def containsObject(self,pos):
		for obj in self.objects+[self.game.player]:
			if obj.pos==pos:
				return obj
	def getObjects(self,pos,type=None):
		return [obj for obj in self.objects+[self.game.player] if obj.pos==pos and (type is None or isinstance(obj,type))]
	def showPossibles(self):
		self.map=self.levelGenerator.render(withPossibles=True)
		self.changed=True
	def cullDead(self):
		self.objects=[obj for obj in self.objects if not obj.dead]

class LevelObject(object):
	def __init__(self,pos,char,game):
		self.pos=pos
		self.char=char
		self.game=game
		self.dead=False
	def canMoveOnto(self):
		return True
	def standMessage(self):
		return ''
	def think(self,game):
		pass
	def getRelPos(self,dir):
		pos=self.pos
		rel=Key.dirToRel(dir)
		return tuple(v+r for (v,r) in zip(pos,rel))
	def move(self,dir):
		return self.moveTo(self.getRelPos(dir))
	def moveTo(self,newPos):
		if self.game.attemptMove(self,newPos):
			self.pos=newPos
			self.game.level.changed=True
			return True
		else:
			return False
	def pickDirection(self):
		return random.choice(Key.DIRS) # this favors North/East/West/South twice as much as diagonal

class Stair(LevelObject): 
	def __init__(self,pos,char,game,destination):
		LevelObject.__init__(self,pos,char,game)
		self.destination=destination
	def standMessage(self):
		return {
			'up':"There's a set of stairs leading upwards here",
			'down':"There's a set of stairs leading downwards here.",
			'leave':"The exit of the dungeon is here."
		}[self.destination]

class Item(LevelObject):
	def __init__(self,pos,game,char='%',name="An item"):
		LevelObject.__init__(self,pos,char,game)
		self.name=name
	def standMessage(self):
		return "There is %s here" % self.name

class Gold(Item):
	def __init__(self,pos,game,amount):
		Item.__init__(self,pos,game,'$',"%i gold piece%s" % (amount,'s' if amount!=1 else ''))
		self.amount=amount
	def standMessage(self):
		return "There %s %s here." % ('is' if self.amount==1 else 'are', self.name)

class Artifact(Item):
	def __init__(self,pos,game):
		Item.__init__(self,pos,game,ARTIFACTCHAR,ARTIFACT)
	

class LivingCreature(LevelObject):
	def __init__(self,pos,char,game,health):
		LevelObject.__init__(self,pos,char,game)
		self.health=self.maxHealth=health
		self.attack=1
	def getAttackDamage(self):
		attack=self.attack
		attackRange=range(0,attack+1)
		low=int(attack*0.5)
		return random.choice(attackRange[low:])
	def hurt(self,dmg):
		self.health-=dmg
		if self.health<=0:
			self.dead=True
	def die(self):
		pass
	def canMoveOnto(self):
		return False

class Monster(LivingCreature):
	def __init__(self,pos,game,monsterType):
		LivingCreature.__init__(self,pos,monsterType.char,game,monsterType.health)
		self.pos=pos
		self.type=monsterType
		self.lastMoved=None
		self.title=monsterType.pronoun+monsterType.name
		self.hostile=self.type.hostile
		self.enraged=False
		self.viewDistSquared=monsterType.viewDist**2
		self.attack=monsterType.attack
		self.health=self.maxHealth=monsterType.health
	def think(self,game):
		player=game.player
		if self.dead:
			return
		if self.lastMoved is None or game.turn-self.lastMoved>self.type.moveEvery:
			self.lastMoved=game.turn
			if self.hostile:
				dir=self.nearbyPlayerDirection()
				if dir is not None:
					if not self.move(dir):
						if self.getRelPos(dir)==self.game.player.pos:
							damage=self.getAttackDamage()
							if damage>0: 
								player.hurt(damage)
								if player.dead:
									self.game.schedule("%s furiously %s you, and you collapse to the ground!" % (self.title,self.type.verb))
									self.game.schedule("You die...")
									self.game.schedule("")
									player.fate=" was killed by "+self.title
								else:
									self.game.schedule("%s %s you for %i damage!" % (self.title.capitalize(),self.type.verb,damage))
					return
			self.move(self.pickDirection())
	def hurt(self,dmg):
		LivingCreature.hurt(self,dmg)
		self.hostile=self.enraged=True
		self.viewDistSquared=self.type.enragedViewDist**2
	def nearbyPlayerDirection(self):
		playerPos=self.game.player.pos
		level=self.game.level
		if distSquared(self.pos,playerPos)<self.viewDistSquared:
			possibilities=dict([(self.getRelPos(dir),dir) for dir in Key.SIMPLE_DIRECTIONS])
			return possibilities[closest(playerPos, [pos for pos in possibilities.keys() if level.isEmpty(pos)])]
		else:
			return None
	def droppedItem(self):
		if self.type.droppedItem:
			return self.type.droppedItem(self.pos,self.game)
		elif self.type.gold>0:
			if random.random()<self.type.dropRate:
				maxGold=self.type.gold
				amt=int(random.triangular(0,maxGold,maxGold*0.75))
				if amt>0:
					return Gold(self.pos,self.game,amt)
					
	def die(self):
		if self.type.deathMessage:
			self.game.schedule(self.type.deathMessage)
		

	
	
class Player(LivingCreature):
	def __init__(self,game,pos):
		LivingCreature.__init__(self,pos,'@',game,STARTHEALTH)
		self.name=getpass.getuser().lower().capitalize()
		self.className='Warrior'
		self.gold=STARTGOLD
		self.kills=[]
		self.xp=0
		self.xpLevel=0
		self.nextRegenerate=0
		self.gainLevel() # cheap way to initialize stats
		self.health=self.maxHealth
		self.fate=" never returned."
		self.inventory=[]
	def recordKill(self,monster):
		self.kills.append(monster)
		baseXP=monster.type.xp
		divisor=1
		if monster.type.xpLevel<self.xpLevel:
			divisor=1.5**(self.xpLevel-monster.type.xpLevel)
		self.xp+=int(baseXP/divisor)
		ret=False
		while self.xp>self.nextLevelXP: # while to handle killing a monster and getting multiple levels off it
			self.gainLevel()
			ret=True
		return ret
	def gainLevel(self):
		self.xpLevel+=1
		n=self.xpLevel
		self.attack=int(1+0.3*n+1.3**n)
		self.maxHealth=int(STARTHEALTH+2*n+1.3**n)
		self.nextLevelXP=self.xp+int(7+3*n+1.3**n)
		self.regenDelay=int(max(1,50-2*n-1.05**n))
		self.lastLeveled=self.game.turn
	def rest(self,turn): # every other turn the player is resting, accelerate how soon we regen by one step
		if turn&1:
			self.nextRegenerate-=1
		if turn-self.lastLeveled<POSTLEVELREGENPERIOD: # for X turns after leveling, regen is accelerated greatly by resting
			self.nextRegenerate-=4
	def regenerate(self):
		if self.game.turn>=self.nextRegenerate:
			if self.health<self.maxHealth:
				self.health+=1
			self.nextRegenerate=self.game.turn+self.regenDelay
	def getItem(self,item):
		self.inventory.append(item)
	def hasArtifact(self):
		return any(isinstance(obj,Artifact) for obj in self.inventory)