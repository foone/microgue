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
#   
#   microgue 0.2

import curses,re
from util import *
from input import Key
from level import *
from monsters import BADGUY
MINTERMSIZE=(80,24)
GAMENAME='microgue'
STATUSHEIGHT=1
STATROWS=2

DEBUG=False
DEBUGKEYS=False
INTROMSG=("""Welcome to %s! The evil %s has stolen %s from the good King Munlankansan. 
As his devoted son, you've sworn to retrieve it and bring an early end to Enku's campaign of darkness 
which blights the otherwise happy peninsula of Lotesin!""" % (GAMENAME,BADGUY,ARTIFACT))

class Screen(object):
	def __init__(self,log):
		win=self.window=curses.initscr()
		curses.cbreak() # get keys one at a time, don't wait for return
		curses.noecho() # don't show keys entered
		win.keypad(1)
		curses.start_color()
		self.lastStatus=''
		self.log=log
	def getKey(self): # yes, it is weird to get keys from the screen. I blame curses
		return self.window.getch()
	def getSize(self):
		h,w=self.window.getmaxyx()
		return (w,h)
	def getUsableSize(self):
		w,h=self.getSize()
		return (w,h-(STATUSHEIGHT+STATROWS))
	def shutdown(self,message=None):
		if self.window is None:
			return # we've already shut down
		curses.endwin()
		if message is not None:
			print message
		self.window=None
	def checkMinimumSize(self):
		if any(actual<expected for (actual,expected) in zip(self.getSize(),MINTERMSIZE)):
			self.shutdown("Your terminal must be at least %sx%s to run %s" % (MINTERMSIZE+(GAMENAME,)))
			return True
	def setStatus(self,msg,more=False):
		self.window.addstr(0,0,msg)
		self.window.clrtoeol() # clear rest of line
		if more is not False:
			self.window.addstr(0,self.getSize()[0]-7,'[more]')
		self.lastStatus=msg
	def getStatus(self):
		return self.lastStatus
	def setStatLines(self,first,second):
		h=self.getSize()[1]
		self.window.addstr(h-2,0,first)
		self.window.clrtoeol() # clear rest of line
		self.window.addstr(h-1,0,second)
		self.window.clrtoeol() # clear rest of line
	def setDebug(self,*args,**kwargs):
		msg=' '.join([str(x) for x in args]+[('%s=%s' % v) for v in kwargs.items()])
		oldpos=self.window.getyx()
		self.window.addstr(self.getSize()[1]-1,0,msg) # clear line too
		self.window.clrtoeol() # clear rest of line
		self.window.move(*oldpos)
	def refresh(self):
		self.window.refresh()
	def ask(self,message,options=None,defaultKey=Key.ENTER):
		with StatusDiversion(self):
			self.setStatus(message)
			if options is None:
				m=re.search(r'\[([^\]]+)\]',message)
				if m:
					options=''.join(set(m.group(1).lower()+m.group(1).upper()))
				else:
					raise ValueError("options was not specified and couldn\'t extract options from '%s'" % message)
			while True:
				k=self.getKey()
				if k==Key.ENTER:
					return defaultKey
				ch=Key.codeToChar(k)
				if options is None or ch in options:
					return ch
	def confirm(self,msg):
		return self.ask(msg+" [Yn]",options='ynqYNQ',defaultKey='Y') in 'yYqQ'
	def drawMapLine(self,y,chars):
		self.window.addstr(y+STATUSHEIGHT,0,chars)
	def drawObject(self,object):
		x,y=object.pos
		self.window.addch(y+STATUSHEIGHT,x,object.char,curses.A_BOLD)
	def positionCursor(self,object):
		x,y=object.pos
		self.window.move(y+STATUSHEIGHT,x)
	def showLog(self):
		w,h=self.getSize()
		h-=2 # for the "press any key to return to game" lines 
		self.showTextWindow(self.log.getLastScreenful(w,h))
	def showTextWindow(self,lines,returnmsg='Press any key to return to '+GAMENAME):
		self.refresh()
		with StatusDiversion(self):
			logwin=curses.newwin(0,0)
			h,w=logwin.getmaxyx()
			h-=2 # for the "press any key to return to game" lines 
			
			
			for i,line in enumerate(lines):
				logwin.addstr(i,0,line)
			logwin.hline(h,0,'-',w)
			logwin.addstr(h+1,0,returnmsg)
			logwin.refresh()
			self.getKey()
		self.refresh()
	

class Game(object):
	def __init__(self,screen):
		self.screen=screen
		self.turn=0
		self.savedLevels={}
		self.depth=depth=1
		self.level=level=self.getLevel(depth)
		self.player=Player(self,self.level.pickedPlayerPos)
		self.statsChanged=True
		self.scheduledMessages=[]
	def schedule(self,msg):
		self.scheduledMessages.append(msg)
	def scheduleLines(self,lines):
		for line in lines:
			if line:
				self.schedule(line)
	def play(self):
		self.showIntro()
		self.schedule("Welcome to %s!" % GAMENAME)
		self.showScheduledMessages()
		screen,level,player=self.screen,self.level,self.player
		while not player.dead:
			
			if level.changed:
				level.draw(screen,player)
				self.level.sortObjects()
			if self.statsChanged:
				self.drawStats()
			key=screen.getKey()
			if key in Key.QUITS:
				if key==Key.HARDQUIT or screen.confirm("Are you sure you want to quit?"):
					return key==Key.HARDQUIT
			if key in Key.DIRS:
				player.move(key)
				self.nextTurn()
			if key in Key.WAITKEYS:
				self.player.rest(self.turn)
				self.nextTurn()
			if key==Key.LOG:
				screen.showLog()
			if key in Key.STAIRS:
				ret=self.tryStairs(key==Key.GO_UP)
				if ret=='left':
					return
				if ret=='new level':
					level=self.level
				self.nextTurn()
			if key in Key.GETS:
				self.tryGet()
				self.nextTurn()
			if key in Key.INVENTORIES:
				self.showInventory()
				self.nextTurn()

	def attemptMove(self,movingObject,newPos):
		level=self.level
		if not self.level.isOnScreen(newPos):
			return False
		if not level.isEmpty(newPos):
			return False
		
		objects=level.getObjects(newPos)
		if not objects:
			return True # nothing there, move move on!
		if movingObject is self.player:
			canMove=all(obj.canMoveOnto() for obj in objects)
			if canMove:
				self.scheduleLines(obj.standMessage() for obj in objects)
				return True
			else:
				monsters=[obj for obj in objects if isinstance(obj,Monster)]
				if monsters:
					monster=monsters[0] # only attack the first monster in the stack
					damage=self.player.getAttackDamage()
					if damage:
						monster.hurt(damage)
						if monster.dead:
							newLevel=self.player.recordKill(monster)
							suffix=', and feel more confident in your skills!' if newLevel else '!' 
							self.schedule("You strike %s down%s" % (monster.title,suffix))
							
							drop=monster.droppedItem()
							if drop:
								level.objects.append(drop)
							monster.die()
							level.cullDead()
						else:
							self.schedule("You hit %s for %i damage." % (monster.title,damage))
					else:
						self.schedule("You swing at %s and miss!" % monster.title)
				else:
					self.schedule("You cannot pass.")
				return False
		else:
			return all(obj.canMoveOnto() for obj in objects)
	def tryStairs(self,goUp):
		screen,level=self.screen,self.level
		stairs=level.getObjects(self.player.pos,Stair)
		assert len(stairs)<2 # two or more stairs means the stair placement broke 
		if not stairs:
			self.schedule("There are no stairs here!")
		else:
			dest=stairs[0].destination
			if dest=='leave':
				if self.player.hasArtifact():
					if screen.confirm("You hesitate at the exit. Are you ready to leave?"):
						self.player.fate=" successfully returned with %s and was richly rewarded." % ARTIFACT
						return 'left'
				else:
					if screen.confirm("There's no coming back! Are you sure you want to leave?"):
						self.player.fate=" deserted his duty and fled into hiding, never to be seen again"
						return 'left'
			elif dest=='down':
				self.schedule("You descend into the darkness...")
				self.changeLevel(+1)
				return 'new level'
			elif dest=='up':
				self.schedule("You climb back towards the surface.")
				self.changeLevel(-1)
				return 'new level'
	def tryGet(self):
		for obj in self.level.getObjects(self.player.pos,Item):
			obj.dead=True
			if isinstance(obj,Gold):
				self.player.gold+=obj.amount
			else:
				self.player.getItem(obj)
			self.schedule("You pick up %s." % obj.name)
			
		self.level.cullDead()
	def showInventory(self):
		player=self.player
		if not player.inventory:
			self.schedule("You're not carrying anything other than your weapon.")
		else:
			self.screen.showTextWindow([item.name for item in player.inventory])
	def changeLevel(self,rel):
		level,player=self.level,self.player
		level=self.level=self.getLevel(level.depth+rel)
		player.moveTo((level.upStair if rel>0 else level.downStair).pos)
		player.level=level
	def getLevel(self,i):
		if i not in self.savedLevels:
			self.savedLevels[i]=Level(self.screen.getUsableSize(),self,i)
		return self.savedLevels[i]
	def drawStats(self):
		player,level=self.player,self.level
		name=('%s the %s' % (player.name,player.className)).ljust(30)
		name+='ATK: %i' % self.player.attack
		statLine='Level: %i HP: %i/%i Gold: %i XP: %i Skill Level: %i (next at XP %i)' % (level.depth,player.health,
																																										player.maxHealth,player.gold,player.xp,player.xpLevel,
																																										player.nextLevelXP)
		self.screen.setStatLines(name,statLine)
	def nextTurn(self):
		self.turn+=1
		self.monstersMove()
		self.player.regenerate()
		self.showScheduledMessages()
	def monstersMove(self):
		for obj in self.level.objects:
			obj.think(self)
	def showScheduledMessages(self):
		
		w=self.screen.getSize()[0]-6
		scheduled=list(mergeShortLines(self.scheduledMessages,w))
		if scheduled:
			if len(scheduled)==1:
				self.screen.setStatus(scheduled[0])
			else:
				last=scheduled[-1]
				for message in scheduled:
					self.screen.setStatus(message,more=message is not last)
					if message is not last:
						self.screen.getKey()
			self.scheduledMessages=[] # reset messages
		else:
			self.screen.setStatus('')
	def postGameScoreboard(self):
		player=self.player
		monsterCount=len(player.kills)
		lines=[
			("You played for %i turn%s" % (self.turn,'s' if self.turn!=1 else '')),
			("You killed %i monster%s." % (monsterCount,'s' if monsterCount!=1 else '')),
		]
		if player.gold>0:
			lines.append("You collected %i gold piece%s." % (player.gold,'s' if player.gold!=0 else ''))
		lines.extend([
			'',
			("%s%s" % (player.name,player.fate))
		])
		self.screen.showTextWindow(lines,"Press any key to quit.") 
	def showIntro(self):
		import textwrap 
		intro=re.sub(r'\s ',' ',INTROMSG.replace('\n',' '))
		lines=['']+textwrap.wrap(intro,self.screen.getSize()[0]-4,initial_indent='  ',subsequent_indent='  ')
		self.screen.showTextWindow(lines,"Press any key to begin %s" % GAMENAME)
	


def main():
	with StdoutRedirect() as log:
		screen=Screen(log)
		try:
			if not screen.checkMinimumSize():
				game=Game(screen)
				if not game.play():
					game.postGameScoreboard()
				screen.shutdown()
		except:
			screen.shutdown()
			raise
if __name__=='__main__':
	main()