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

import random
import level
CERTAIN=0
BADGUY="Wizard Enku"
ALWAYS=1.1
class MonsterType(object):
	def __init__(self,name,char,health,attack,gold,xp,rarity,dropRate=0.8,minLevel=1,maxLevel=999,moveEvery=2,hostile=True,
							pronoun='a ',viewDist=7,verb="bites",enragedViewDist=12,droppedItem=None,deathMessage=None,xpLevel=1):
		self.name=name
		self.char=char
		self.health=health
		self.attack=attack
		self.dropRate=dropRate
		self.gold=gold
		self.xp=xp
		self.rarity=rarity # HIGHER RARITY=MORE MONSTERS
		self.minLevel=minLevel
		self.maxLevel=maxLevel
		self.moveEvery=moveEvery
		self.hostile=hostile # attack the player if he gets near, not just if he whacks us
		self.pronoun=pronoun
		self.viewDist=viewDist
		self.enragedViewDist=min(enragedViewDist,viewDist)
		self.verb=verb
		self.droppedItem=droppedItem
		self.deathMessage=deathMessage
		self.xpLevel=xpLevel
MONSTERS=[
	MonsterType('Cave Bat','b',
								health=3,
								attack=1,
								gold=0,
								xp=3,
								rarity=8,
								hostile=False,
								maxLevel=3,),
	MonsterType('Plague Rat','r',
								health=5,
								attack=1,
								gold=4,
								xp=6,
								rarity=7,
								maxLevel=4),
	MonsterType('Rabid Dog','d',
								health=10,
								attack=2,
								gold=10,
								xp=10,
								rarity=5,
								xpLevel=3,
								minLevel=3,
								maxLevel=6),
	MonsterType('Floating Eye','e',
								health=10,
								attack=2,
								gold=10,
								xp=15,
								rarity=2,
								xpLevel=3,
								minLevel=2,
								maxLevel=6,
								viewDist=17,
								verb='blasts'),
	MonsterType('Kobold','k',
								health=12,
								attack=3,
								gold=25,
								xp=20,
								rarity=3,
								moveEvery=1,
								xpLevel=4,
								viewDist=15,
								minLevel=3,verb='slashes'),
	MonsterType('Vampire','v',
								health=15,
								attack=4,
								gold=60,
								xp=35,
								rarity=2,
								moveEvery=1,
								xpLevel=6,
								viewDist=50,
								minLevel=5),
	MonsterType('Naga','n',
								health=15,
								attack=6,
								gold=25,
								xp=40,
								rarity=3,
								moveEvery=1,
								xpLevel=7,
								viewDist=20,
								minLevel=5,verb='crushes'),
	MonsterType(BADGUY,'W',
								health=30,
								attack=10,
								gold=100,
								xp=100,
								rarity=CERTAIN,
								moveEvery=1,
								minLevel=7,
								maxLevel=7,
								xpLevel=99,
								pronoun='the ',
								verb='zaps',
								dropRate=ALWAYS,
								viewDist=1000, # he sees you everwhere
								droppedItem=(lambda pos,game: level.Artifact(pos,game)),
								deathMessage='As the wizard fades to dust, he mutters "curse you, hero!".' 
						)								
]

def pickMonsters(level):
	num=int(2.5*level+1.1**level)
	applicable=[m for m in MONSTERS if m.minLevel<=level<=m.maxLevel]
	weighted=[]
	for m in applicable:
		weighted.extend([m]*m.rarity)
	
	certains=[m for m in applicable if m.rarity==CERTAIN]
	num-=len(certains)
	while len(weighted)<num:
		weighted=weighted+weighted
	return certains+random.sample(weighted,num)
		