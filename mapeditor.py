from PIL import Image
import pygame
import tkinter as tk
import tkinter.filedialog, tkinter.messagebox
import time, random, os, sys

# constants
K_LEFT = pygame.K_LEFT
K_RIGHT = pygame.K_RIGHT
K_DOWN = pygame.K_DOWN
K_UP = pygame.K_UP
K_ESCAPE = pygame.K_ESCAPE
K_o = pygame.K_o
K_w = pygame.K_w
K_h = pygame.K_h

# create some colors
BLACK = (0,0,0)
GREY = (200,200,200)
RED = (255,0,0)
white = (255,255,255)
# object data
TILE_SIZE = 16+1
WIDTH = 64
HEIGHT = 40
DISPLAY_W = TILE_SIZE*WIDTH+1
DISPLAY_H = TILE_SIZE*HEIGHT
TILE_ROWS = 4
MAX_WIDTH = 300
MAX_HEIGHT = 300
STATUS_Y = DISPLAY_H-TILE_SIZE+2
EDIT_X = 200
EDIT_Y = 200

TITLE = 'Map Editor'

# set up pygame
pygame.display.init()
pygame.font.init()
# create our surface
screen = pygame.display.set_mode((DISPLAY_W,DISPLAY_H))
# set title
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# width and height boxes
BOX_W = 40
WIDTH_XY = (400,0)
WIDTH_RECT = (WIDTH_XY[0]+56,0,BOX_W,17)
HEIGHT_XY = (WIDTH_RECT[0]+BOX_W+10,0,BOX_W,17)
HEIGHT_RECT = (HEIGHT_XY[0]+66,0,BOX_W,17)

## Classes ##############################
class StatusBar:
	def __init__(self,message='',counter=0):
		self.message = message
		self.counter = counter
	def set(self,message,counter = 60):
		self.message = message
		self.counter = counter

class Tile:
	def __init__(self,sprite,passable=True,bg=0,flag=[0,0,0,0]):
		self.sprite = pygame.image.fromstring(sprite,(16,16),'RGB').convert()
		self.passable=passable
		self.bg=bg
		self.flag = flag

class Mouse:
	def __init__(self,spriteL=-1,spriteR=0,x=0,y=0):
		self.x = x
		self.y = y
		self.spriteL = spriteL
		self.spriteR = spriteR
		self.w_or_h = ''
	def onMap(self):						# Check if mouse is on map area
		height = level.height
		if height > HEIGHT-TILE_ROWS-1:
			height = HEIGHT-TILE_ROWS-1		# - 1 because the top row is the menu
		width = level.width
		if width > WIDTH:
			width = WIDTH
		return self.y > TILE_SIZE and self.y < (height+1)*TILE_SIZE and self.x < width*TILE_SIZE

class MenuButton:
	def __init__(self,text='button',x=0,y=0,width=10,height=10,action=''):
		self.text = text
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.hover = False
		self.action = action
	def __repr__(self):
		return "MenuButton: ['{}',{},{},{},{},{}]".format(self.text,self.x,self.y,self.width,self.height,self.hover)

class Level:
	def __init__(self,width=32,height=32,x=0,y=0,filename=''):
		self.map = []
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.saved = False
		self.filename = filename
		self.objects = {}
		self.loadMap()
	def loadMap(self):
		self.objects.clear()
		for y in range(MAX_HEIGHT):
			self.map.append([])
			for x in range(MAX_WIDTH):
				self.map[y].append(0)
		if self.filename != '':
			with open(self.filename,"r") as f:
				# first line is object data (actions assigned to a tile)
				line = f.readline().rstrip('/\n')
				if not line == '':
					for item in line.split('/'):
						key,action,data = item.split(' ')
						self.objects[key] = {'action': int(action),'data': int(data)}
				# next line is width and height
				line = f.readline().rstrip('\n')
				w,h = line.split(' ')
				self.width = int(w)
				self.height = int(h)
				y = 0
				for line in f:
					x = 0
					line = line[:-2]
					for tile in line.split(','):
						self.map[y][x] = int(tile)
						x += 1
					y += 1
			self.saved = True
	def drawMap(self):
		# make sure map doesn't get drawn past screen limits
		height = self.height
		if height > HEIGHT-TILE_ROWS-1:
			height = HEIGHT-TILE_ROWS-1		# - 1 because the top row is the menu
		width = self.width
		if width > WIDTH:
			width = WIDTH
		for y in range(height):
			for x in range(width):
				obj_name = str(x+self.x)+','+str(y+self.y)
				if obj_name in self.objects:
					pygame.draw.rect(screen,RED,(x*TILE_SIZE,(y+1)*TILE_SIZE,TILE_SIZE+1,TILE_SIZE+1),1)
				blitSprite(tiles[self.map[y+self.y][x+self.x]].sprite,x*TILE_SIZE+1,y*TILE_SIZE+TILE_SIZE+1)
	def __repr__(self):
		return "Level: ['{}',{},{},{},{},{}]".format(self.filename,self.width,self.height,self.x,self.y,self.saved)

#########################################

#### File functions #####################
def quitSave():
	''' Test if file has been saved before quitting.
		If not, prompt to save. Returns true if we have saved
		and can safely exit or if the user doesn't want to save.
		Returns false if there is some problem. '''
	root = tk.Tk()
	root.withdraw()
	success = False
	if level.saved == False:
		if tk.messagebox.askyesno('Map not saved', 'Save before quitting?'):
			success = saveFile()
		else:
			success = True
	else:
		success = True
	root.destroy()
	return success

def newFile():
	level.map = []
	level.width = 32
	level.height = 32
	level.x = 0
	level.y = 0
	level.filename = ''
	level.saved = False
	level.loadMap()
	statusbar.set("New map")

def openFile():
	root = tk.Tk()
	root.withdraw()
	level.filename = tk.filedialog.askopenfilename(title = "Load a map",initialdir = "maps", filetypes = (("map files","*.map"),("all files","*.*")),defaultextension=".map")
	if not level.filename:
		level.filename = ''
	root.destroy()
	level.loadMap()
	statusbar.set("Map loaded")

def saveFile():
	# save map_jumps
	with open(mj_file,"wt") as f:
		for map_jump in map_jumps:
			for entry in map_jump[:-1]:
				f.write("{} ".format(entry))
			f.write("{}\n".format(str(map_jump[-1])))

	if level.filename == '':
		root = tk.Tk()
		root.withdraw()
		level.filename = tk.filedialog.asksaveasfilename(title = "Save your map",initialdir = "maps",filetypes = (("map files","*.map"),("all files","*.*")),defaultextension=".map")
		root.destroy()
	if level.filename:
		with open(level.filename,"wt") as f:
			# first save object data
			for key in level.objects.keys():
				f.write("{} {} {}/".format(key,level.objects[key]['action'],level.objects[key]['data']))
			f.write("\n")
			# next the width and height
			f.write("{} {}\n".format(level.width,level.height))
			for y in range(level.height):
				for x in range(level.width):
					f.write(str(level.map[y][x])+',')
				f.write('\n')
		level.saved = True
		statusbar.set("File saved")
		return True
	else:
		level.filename = ''

def exportFile():
	global level_list
	if level.filename == '':
		if not saveFile():
			return

	map_array = []

	# individual tilemaps
	for entry in level_list:
		if entry.filename != '':
			filename,ext = os.path.basename(entry.filename).split('.')
			map_array.append([filename,entry.width,entry.height])
			with open('export/'+filename+'.h',"wt") as header:
				header.write('#include "aux_macros.h"\n\n')
				# export tile data
				header.write("tile_t {}_tiledata[][2] = {{".format(filename))
				for t in tiles:
					header.write("{{{},{},0b{}{}{}{}}},\n\t\t".format(str(t.passable).lower(),t.bg,t.flag[0],t.flag[1],t.flag[2],t.flag[3]))
				header.write("};\n\n")
				# export object data
				header.write("s16 {}_obj_data[] = {{".format(filename))
				for key in entry.objects.keys():
					header.write("{},{},{},\n\t\t".format(key,entry.objects[key]['action'],entry.objects[key]['data']))
				header.write("EOF};\n\n")
				# export map data
				header.write("//Width: {}\t Height: {}\nglobal_variable u16 {}[] = {{".format(entry.width,entry.height,filename))
				for y in range(entry.height):
					header.write('\n\t')
					for x in range(entry.width):
						header.write(str(entry.map[y][x])+',')
				header.write('\n};')
	# the main maps file
	with open('export/maps.h','wt') as maps:
		print(len(map_array))
		# include all the maps
		for entry in map_array:
			maps.write('#include "{}.h"\n'.format(entry[0]))
		# make a list of tilemap data: pointers to tilemap, tile data, and object data
		maps.write("\nmap_t map_list[{}] = {{".format(len(map_array)))
		for entry in map_array:
			maps.write("{{{},{}_tiledata,{}_obj_data,{},{}}},\n\t\t".format(entry[0],entry[0],entry[0],entry[1],entry[2]))
		maps.write("};\n\n")
		
		# map changes
		if len(map_jumps) > 0:
			mj_len = len(map_jumps)-1
		else:
			mj_len = 0
		maps.write("u16 map_change_list[{}][{}] = {{".format(len(map_jumps),mj_len))	# first value is the hint
		for map_jump in map_jumps:
			maps.write("{{{},{},{},{},{}}},\n\t\t".format(map_jump[MJ_MAP],map_jump[MJ_MAPX],map_jump[MJ_MAPY],map_jump[MJ_PLAYERX],map_jump[MJ_PLAYERY]))
		maps.write("};")
	statusbar.set("Map(s) exported")
			

def changeMaps():
	def changeMap(event):
		# load new map
		global cur_map,level,level_list
		level_list[cur_map] = level
		cur_map = event.widget.curselection()[0]
		level = level_list[cur_map]
		root.destroy()

	def cancel(event=''):
		# quit without saving values
		root.destroy()

	root = tk.Tk()
	root.bind('<Escape>',cancel)
	root.wm_title("List of maps")
	name_list = list()
	for level in level_list:
		d,f = level.filename.split('/')
		if not level.saved:
			f = '*'+f
		name_list.append(f)

	l = tk.Listbox(root)
	l.insert(0,*name_list)
	l.pack()
	l.bind('<<ListboxSelect>>', changeMap)
	root.mainloop()

#############################################

ACTIONS = ('--Pick Action--','New Map','Display Text')

def editObject(x,y):
	global level,map_jumps,level_list
	name = str(x)+','+str(y)
	# build object if it doesn't exist
	if not name in level.objects:
		level.objects[name] = {'action': -1,'data': 0}

	def updateTile():
		# save values and quit
		action_id = ACTIONS.index(action.get())
		level.objects[name]['action'] = action_id-1
		if action_id == 0:
			del level.objects[name]
			root.destroy()

		# if id = 1, we are creating a new map action entry
		if action_id == 1:
			map_action_id = map_action_txt.index(map_action_choice.get())
			map_id = ma_list.index(ma_txt.get())
			if map_action_id > 0:
				i = map_action_id - 1
				# update values
				map_jumps[i] = [hint.get(),map_id,mapx.get(),mapy.get(),playerx.get(),playery.get()]
			else:
				map_jumps.append([hint.get(),map_id,mapx.get(),mapy.get(),playerx.get(),playery.get()])
				map_action_id = len(map_jumps)
			
			print(map_jumps)

			level.objects[name]['data'] = map_action_id-1
		root.destroy()

	def cancelTile(event=''):
		# quit without saving values
		if level.objects[name]['action'] == -1:	# delete object if it was empty
			del level.objects[name]
		root.destroy()
	
	def changeAction(event):
		index = ACTIONS.index(action.get())
		for i in range(len(ACTIONS)-1):
			if i+1 == index:
				actionframe[i].grid(column=0,row=1,columnspan=2,sticky=tk.W)
			else:
				actionframe[i].grid_forget()

	def changeMapAction(event):
		index = map_action_txt.index(map_action_choice.get())
		if index > 0:
			i = index - 1
			# update values
			hint.set(map_jumps[i][MJ_NAME])
			ma_txt.set(ma_list[map_jumps[i][MJ_MAP]])
			mapx.set(map_jumps[i][MJ_MAPX])
			mapy.set(map_jumps[i][MJ_MAPY])
			playerx.set(map_jumps[i][MJ_PLAYERX])
			playery.set(map_jumps[i][MJ_PLAYERY])
		else:
			ma_txt.set(ma_list[0])
			hint.set('')
			mapx.set(0)
			mapy.set(0)
			playerx.set(0)
			playery.set(0)
			

	root = tk.Tk()
	root.bind('<Escape>',cancelTile)
	root.wm_title("Tile {x},{y}".format(**locals()))
	# create frame and build grid
	mainframe = tk.Frame(root)

	# fill out frame
	action_txt = tk.Label(mainframe,text="Action:")
	action_txt.grid(column=0,row=0)

	# find the currently selected textid, if any
	action = tk.StringVar()
	i = level.objects[name]['action']+1
	action.set(ACTIONS[i])

	action_choice = tk.OptionMenu(mainframe,action,*ACTIONS,command=changeAction)
	action_choice.config(width=10,anchor=tk.W)
	action_choice.grid(column=1,row=0,sticky=tk.W)

	# frame that changes depending on what action you've picked
	actionframe = []
	for i in range(len(ACTIONS)-1):
		actionframe.append(tk.Frame(mainframe))
		
# ----New Map----
	mj_id = level.objects[name]['data']

	map_action_txt = ["New Map Jump"]
	for map_jump in map_jumps:
		# remove the folder path and extension
		map_name,ext = os.path.basename(level_list[map_jump[1]].filename).split('.')
		string = "{}: {} [{},{}]".format(str(map_jump[MJ_NAME]),map_name,map_jump[MJ_PLAYERX],map_jump[MJ_PLAYERY])
		map_action_txt.append(string)
	map_action_choice = tk.StringVar()
	map_action_choice.set(map_action_txt[mj_id+1])

	map_action = tk.OptionMenu(actionframe[0],map_action_choice,*map_action_txt,command=changeMapAction)
	map_action.config(width=18,anchor=tk.W)
	map_action.grid(column=0,row=0,columnspan=4,sticky=tk.W)

	label = tk.Label(actionframe[0],text="Name:")
	label.grid(column=0,row=2)

	hint = tk.StringVar()
	hint.set(map_jumps[mj_id][MJ_NAME])
	hint_input = tk.Entry(actionframe[0],width=8,textvariable=hint)
	hint_input.grid(column=1,row=2,sticky=tk.W)
	
	label = tk.Label(actionframe[0],text="Map:")
	label.grid(column=0,row=3)

	# draw list of maps
	ma_list = []
	for l in level_list:
		filename,ext = os.path.basename(l.filename).split('.')
		ma_list.append(filename)
	
	ma_txt = tk.StringVar()
	ma_txt.set(ma_list[map_jumps[mj_id][MJ_MAP]])
	map_action = tk.OptionMenu(actionframe[0],ma_txt,*ma_list)
	map_action.grid(column=1,row=3,columnspan=3,sticky=tk.W)

	label = tk.Label(actionframe[0],text="MapX:")
	label.grid(column=0,row=4)
	label = tk.Label(actionframe[0],text="MapY:")
	label.grid(column=0,row=5)
	label = tk.Label(actionframe[0],text="PlayerX:")
	label.grid(column=2,row=4)
	label = tk.Label(actionframe[0],text="PlayerY:")
	label.grid(column=2,row=5)

	mapx = tk.IntVar()
	mapx.set(map_jumps[mj_id][MJ_MAPX])
	mapx_input = tk.Entry(actionframe[0],width=3,textvariable=mapx)
	mapx_input.grid(column=1,row=4,sticky=tk.W)

	mapy = tk.IntVar()
	mapy.set(map_jumps[mj_id][MJ_MAPY])
	mapy_input = tk.Entry(actionframe[0],width=3,textvariable=mapy)
	mapy_input.grid(column=1,row=5,sticky=tk.W)

	playerx = tk.IntVar()
	playerx.set(map_jumps[mj_id][MJ_PLAYERX])
	playerx_input = tk.Entry(actionframe[0],width=3,textvariable=playerx)
	playerx_input.grid(column=3,row=4,sticky=tk.W)

	playery = tk.IntVar()
	playery.set(map_jumps[mj_id][MJ_PLAYERY])
	playery_input = tk.Entry(actionframe[0],width=3,textvariable=playery)
	playery_input.grid(column=3,row=5,sticky=tk.W)
# -------------

# ----Text----
	data_txt = tk.Label(actionframe[1],text="Placeholder for now:")
	data_txt.grid(column=0,row=1)

	data = tk.IntVar()
	data.set(level.objects[name]['data'])
	data_input = tk.Entry(actionframe[1],width=3,textvariable=data)
	data_input.grid(column=1,row=1,sticky=tk.W)
# ------------

	# draw buttons
	update_button = tk.Button(mainframe, text="Update", command=updateTile)
	update_button.grid(row=2,column=0)
	cancel_button = tk.Button(mainframe, text="Cancel", command=cancelTile)
	cancel_button.grid(row=2,column=1,sticky=tk.W)
	mainframe.pack(side=tk.LEFT)

	if level.objects[name]['action'] >= 0:
		changeAction('')

	root.mainloop()
	

TF = 0
INPUT = 1

def editTile(tileid):
	tile = tiles[tileid]
	TILE_PROPERTIES = (("Passable?",tile.passable,TF),
					("Map BGX:",tile.bg,INPUT),
					("U",tile.flag[0],TF),
					("R",tile.flag[1],TF),
					("D",tile.flag[2],TF),
					("L",tile.flag[3],TF))

	def updateTile():
		# save values and quit
		tile.passable = var[0].get() == 1
		tile.bg = var[1].get()
		tile.flag = [var[i].get()==1 for i in range(2,6)]
		print([var[i].get() for i in range(6)])
		print(tile.flag)
		root.destroy()

	def cancelTile(event=''):
		# quit without saving values
		root.destroy()

	root = tk.Tk()
	root.bind('<Escape>',cancelTile)
	root.wm_title("Tile "+str(tileid))
	mainframe = tk.Frame(root)
	# create grid: columns
	mainframe.columnconfigure(0,pad=1)
	mainframe.columnconfigure(1,pad=1)
	# grid: rows
	for i in range(len(TILE_PROPERTIES)+1):
		mainframe.rowconfigure(i,pad=0)
	item_input = list()
	var = list()
	i=0
	for item in TILE_PROPERTIES:
		item_label = tk.Label(mainframe,text=item[0])
		item_label.grid(column=0,row=i,stick=tk.E)
		# True or False box
		if item[2] == TF:
			var.append(tk.IntVar())
			var[i].set(item[1])
			item_input = tk.Checkbutton(mainframe,variable=var[i])
		# number input box
		elif item[2] == INPUT:
			var.append(tk.IntVar())
			value = item[1]
			var[i].set(value)
			item_input = tk.Entry(mainframe,width=3,textvariable=var[i])
		item_input.grid(column=1,row=i,sticky=tk.W)
		i+=1
	# draw two buttons at the bottom
	update_button = tk.Button(mainframe, text="Update", command=updateTile)
	update_button.grid(row=i,column=0)
	cancel_button = tk.Button(mainframe, text="Cancel", command=cancelTile)
	cancel_button.grid(row=i,column=1,sticky=tk.W)
	mainframe.pack(side=tk.LEFT)
	root.mainloop()
	tiles[tileid] = tile

def drawMenu(buttons, width, height):
	fontobject = pygame.font.Font(None,25)

	# menu buttons
	for b in buttons:
		border = 1
		if b.hover:
			border = 0
		pygame.draw.rect(screen, (154,125,254),(b.x,b.y,b.width,b.height), border)
		screen.blit(fontobject.render(b.text, 0, BLACK),(b.x+2,b.y))

	# width and height boxes
	screen.blit(fontobject.render("Width: ", 0, BLACK),WIDTH_XY)
	screen.blit(fontobject.render("Height: ", 0, BLACK),HEIGHT_XY)
	border = 1
	if mouse.w_or_h == 'w':
		border = 0
	pygame.draw.rect(screen, (154,125,254),WIDTH_RECT, border)
	border = 1
	if mouse.w_or_h == 'h':
		border = 0
	pygame.draw.rect(screen, (154,125,254),HEIGHT_RECT, border)

	screen.blit(fontobject.render(width, 0, BLACK),(WIDTH_RECT[0]+2,2))
	screen.blit(fontobject.render(height, 0, BLACK),(HEIGHT_RECT[0]+2,2))

def drawStatusBar():
	fontobject = pygame.font.Font(None,21)
	# check if there's a status message to display
	if statusbar.counter > 0:
		screen.blit(fontobject.render(statusbar.message, 0, BLACK),(10,STATUS_Y))
		statusbar.counter -= 1
	# draw map coords
	string = "Map - {},{}".format(str(level.x),str(level.y))
	screen.blit(fontobject.render(string, 0, BLACK),(DISPLAY_W//2-100,STATUS_Y))
	# draw the mouse coords if the mouse is on top of the map
	if mouse.onMap():
		string = "Mouse - {},{}".format(str(mouse.x//TILE_SIZE+level.x),str(mouse.y//TILE_SIZE-1+level.y))
		screen.blit(fontobject.render(string, 0, BLACK),(DISPLAY_W//2,STATUS_Y))
	# draw currently selected tiles
	blitSprite(tiles[mouse.spriteL].sprite,160,STATUS_Y-1)
	blitSprite(tiles[mouse.spriteR].sprite,180,STATUS_Y-1)

def blitSprite(sprite,x,y):
	screen.blit(sprite,(x,y))

def drawMouse():
	if mouse.y < DISPLAY_H-TILE_SIZE:
		sprite = tiles[mouse.spriteL].sprite
		if mouse.y > DISPLAY_H-TILE_ROWS*TILE_SIZE:
			sprite = tiles[-1].sprite					# if cursor is over tiles, switch to main cursor sprite
		surface = pygame.Surface((16,16), depth=24)
		surface.set_alpha(255)
		surface.set_colorkey((255,255,255))
		surface.blit(sprite,(0,0))
		screen.blit(surface,(mouse.x,mouse.y))

def drawTileList():
	x = 1
	y = (HEIGHT-TILE_ROWS)*TILE_SIZE+1
	for tile in tiles[:-1]:
		blitSprite(tile.sprite,x,y)
		x += TILE_SIZE

def drawGrid():
	width = level.width
	height = level.height
	if level.width > WIDTH:
		width = WIDTH
	if level.height > HEIGHT-TILE_ROWS-1:
		height = HEIGHT-TILE_ROWS-1
	for x in range(width+1):
		pygame.draw.line(screen,BLACK,(x*TILE_SIZE,TILE_SIZE),(x*TILE_SIZE,(height+1)*TILE_SIZE))
	for y in range(1,height+2):
		pygame.draw.line(screen,BLACK,(0,y*TILE_SIZE),(width*TILE_SIZE,y*TILE_SIZE))
	pygame.draw.line(screen,BLACK,(0,DISPLAY_H-TILE_SIZE),(DISPLAY_W,DISPLAY_H-TILE_SIZE))

def checkMouse(buttons):
	for b in buttons:
		if mouse.y < TILE_SIZE and b.x < mouse.x < b.x+b.width:
			b.hover = True
		else:
			b.hover = False
	mouseClick = pygame.mouse.get_pressed()
	if mouseClick[0] == 1 or mouseClick[2] == 1:
		keys = pygame.key.get_pressed()
		# buttons up top
		if mouse.y < TILE_SIZE:
			if WIDTH_RECT[0]+BOX_W > mouse.x > WIDTH_RECT[0]:
				mouse.w_or_h = 'w'
			if HEIGHT_RECT[0]+BOX_W > mouse.x > HEIGHT_RECT[0]:
				mouse.w_or_h = 'h'
			
		# list of tiles at bottom
		if mouse.y > DISPLAY_H-TILE_ROWS*TILE_SIZE:
			y = (mouse.y - (DISPLAY_H-TILE_ROWS*TILE_SIZE))//TILE_SIZE 
			x = mouse.x//TILE_SIZE
			tileid = y*WIDTH + x
			if len(tiles)-1 > tileid:
				if keys[pygame.K_LCTRL]:
					editTile(tileid)
				elif mouseClick[0] == 1:
					mouse.spriteL = tileid
				else:
					mouse.spriteR = tileid
		# tilemap
		if mouse.onMap():
			y = (mouse.y-TILE_SIZE) // TILE_SIZE			# don't forget top row is the menu
			x = mouse.x // TILE_SIZE
			# if CTRL is pressed, edit that tile's action data
			if keys[pygame.K_LCTRL]:
				editObject(x+level.x,y+level.y)
				return
			# otherwise, load the tile into the map
			if mouseClick[0] == 1 and mouse.spriteL != -1:
				level.map[y+level.y][x+level.x] = mouse.spriteL
			elif mouseClick[2] == 1:
				level.map[y+level.y][x+level.x] = mouse.spriteR
			level.saved = False

BUTTONS = [	('New',0,0,50,16,newFile),
			('Load',50,0,50,16,openFile),
			('Save',100,0,50,16,saveFile),
			('Export',150,0,60,16,exportFile),
			('Change Maps',210,0,120,16,changeMaps)]

### Main ################################################
def main():
	global level,level_list
	dirs = ('maps/','export/')
	for d in dirs:
		os.makedirs(d,exist_ok=True)
	d = dirs[0]
	for f in sorted(os.listdir(d)):
		if f.endswith('.map'):
			level_list.append(Level(filename=d+f))
			level_list[-1].loadMap()
	if level_list:
		level = level_list[cur_map]
		print("Loading",level_list[cur_map])
	else:
		print("No maps found, creating new map")

	buttons = []
	for text,x,y,width,height,action in BUTTONS:
		buttons.append(MenuButton(text,x,y,width,height,action))

	running = True
	width_str = str(level.width)
	height_str = str(level.height)
	while running:
		filename = os.path.basename(level.filename)
		if not level.saved:
			pygame.display.set_caption(TITLE+' '+filename+' [not saved]')
		else:
			pygame.display.set_caption(TITLE+' '+filename)
		key = 0
		keys = pygame.key.get_pressed()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				if quitSave():
					running = False
			# check keyboard commands
			if event.type == pygame.KEYDOWN:
				if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
					if event.key == pygame.K_s:
						saveFile()
					if event.key == K_o:
						openFile()
					if event.key == pygame.K_n:
						newFile()
					if event.key == pygame.K_e:
						exportFile()
				if event.key == K_ESCAPE:
					if mouse.w_or_h == '':
						if quitSave():
							running = False
					else:
						width_str = str(level.width)
						height_str = str(level.height)
						mouse.w_or_h = ''
				if event.key == K_w:
					if mouse.w_or_h == '':
						mouse.w_or_h = 'w'			# update width
					else:
						width_str = str(level.width)
						mouse.w_or_h = ''
				if event.key == K_h:
					if mouse.w_or_h == '':
						mouse.w_or_h = 'h'			# update height
					else:
						height_str = str(level.height)
						mouse.w_or_h = ''
				if event.key == pygame.K_BACKSPACE:
					key = 'backspace'
				if event.key == pygame.K_RETURN:
					key = 'enter'
				if 47 < event.key < 59:
					key = event.key
			# update mouse x/y
			if event.type == pygame.MOUSEMOTION:
				mousePos = pygame.mouse.get_pos()
				mouse.x = mousePos[0]
				mouse.y = (mousePos[1]//TILE_SIZE)*TILE_SIZE+1
				if mouse.y > TILE_SIZE:
					mouse.x = (mousePos[0]//TILE_SIZE)*TILE_SIZE+1
			# check for mouseclick on menu buttons
			if event.type == pygame.MOUSEBUTTONDOWN:
				if event.button < 4:
					for b in buttons:
						if mouse.y < TILE_SIZE and b.x < mouse.x < b.x+b.width:
							b.action()
				# check for scroll wheel
				if event.button == 4:				# middle mouse down
					if mouse.spriteL > -1:
						mouse.spriteL -= 1
				if event.button == 5:				# middle mouse down
					if -1 <= mouse.spriteL < NUMTILES -1:
						mouse.spriteL += 1
		if mouse.w_or_h != '' and key != 0:
			# fill out width/height box
			if mouse.w_or_h == 'w':
				if key == 'backspace':
					width_str = width_str[:-1]
				elif key == 'enter':
					if not width_str:
						width_str = '8'
					if int(width_str) > MAX_WIDTH:
						width_str = str(MAX_WIDTH)
					level.width = int('0'+width_str)
					mouse.w_or_h = ''
				elif len(width_str) < 3:
					width_str += chr(key)
			elif mouse.w_or_h == 'h':
				if key == 'backspace':
					height_str = height_str[:-1]
				elif key == 'enter':
					if not height_str:
						height_str = '8'
					if int(height_str) > MAX_HEIGHT:
						height_str = str(MAX_HEIGHT)
					level.height = int('0'+height_str)
					mouse.w_or_h = ''
				elif len(height_str) < 3:
					height_str += chr(key)
		elif mouse.w_or_h == '':
			width_str = str(level.width)
			height_str = str(level.height)
		if keys[K_LEFT]:
			if level.x > 0:
				level.x -= 1
		if keys[K_UP]:
			if level.y > 0:
				level.y -= 1
		if keys[K_RIGHT]:
			if level.x < level.width-WIDTH:
				level.x += 1
		if keys[K_DOWN]:
			if level.y < level.height-(HEIGHT-1-TILE_ROWS):
				level.y += 1

		# erase screen
		screen.fill(white)

		# draw grid
		drawGrid()

		# draw tilemap
		level.drawMap()

		# draw tile list
		drawTileList()

		# draw menu
		drawMenu(buttons, width_str, height_str)

		# handle mouse
		if mouse.onMap() or mouse.y > DISPLAY_H-TILE_ROWS*TILE_SIZE:
			drawMouse()
		checkMouse(buttons)	# check for mouse clicks

		drawStatusBar()

		# update screen
		pygame.display.update()

		# 60 Mhz
		clock.tick(60)
	pygame.quit()

# load map jumps
MJ_NAME		= 0
MJ_MAP		= 1
MJ_MAPX		= 2
MJ_MAPY		= 3
MJ_PLAYERX	= 4
MJ_PLAYERY	= 5
map_jumps = []

mj_file = 'mapjumps.lst'
if os.path.isfile(mj_file):
	with open(mj_file,'r') as mapjumps:
		for line in mapjumps:
			line = line.rstrip('\n')
			array = line.split(' ')
			for i in range(1,len(array)):
				array[i] = int(array[i])
			map_jumps.append(array)

# load texts

# load tiles
tiles = []
directory = os.path.dirname(os.path.realpath(sys.argv[0]))+'/'
im = Image.open(directory+'tiles/tiles.png','r')
width,height = im.size
NUMTILES = 0
for i in range(1,height//16):
	tile = im.crop((0,i*16,width,i*16+16))
	data = tile.tostring()
	tiles.append(Tile(data))
	NUMTILES += 1

im = Image.open(directory+'cursor.bmp','r')
tiles.append(Tile(im.tostring()))

mouse = Mouse()
level = Level()
level_list = list()
cur_map = 0
statusbar = StatusBar()
main()
