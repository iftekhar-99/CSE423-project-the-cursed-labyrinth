from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random
import sys

# Increase recursion depth for map gen
sys.setrecursionlimit(2000)

# ==========================================
# Global Configuration (Level 3: Stone Labyrinth)
# ==========================================
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

MAP_DIM = 140        
CELL_SIZE = 30       
WALL_HEIGHT = 70    

C_EMPTY = 0
C_WALL = 1
C_BOSS_ARENA = 3
C_START = 4
C_EXIT = 5

map_data = []       
display_list = None 

mines = []          
particles = [] 
animals = []        
animal_rocks = []   
daggers = []        
loot = []           
boulders = []       
boss_minions = []   
gas_clouds = []     

boss_active = False
boss_defeated = False
boss_obj = {
    'x': 0, 'z': 0, 
    'hp': 800,          
    'max_hp': 800, 
    'timer': 0
}

player_pos = [0, 0, 0]
player_angle = 1.57   
player_pitch = 0.0    
base_speed = 3.5
player_speed = base_speed
player_ammo = 40
key_states = {}

player_stamina = 100.0
max_stamina = 100.0
is_exhausted = False
is_sprinting = False
shield_timer = 0      

inventory = []
immunity_timer = 0
infinite_stamina_timer = 0

player_hp = 100.0
game_over = False
level_complete = False 
global_time = 0.0

# ==========================================
# 1. Map & Entity Generation
# ==========================================
def generate_level_3():
    global map_data, player_pos, display_list, mines, particles, animals, animal_rocks, daggers, loot, boulders, boss_minions, gas_clouds
    global game_over, level_complete, player_hp, player_ammo, boss_active, boss_defeated, boss_obj
    global player_stamina, is_exhausted, player_pitch, shield_timer
    global inventory, immunity_timer, infinite_stamina_timer
    
    map_data = [[C_WALL for _ in range(MAP_DIM)] for _ in range(MAP_DIM)]
    mines = []
    particles = []
    animals = []
    animal_rocks = []
    daggers = []
    loot = []
    boulders = []
    boss_minions = [] 
    gas_clouds = []
    
    game_over = False
    level_complete = False
    boss_active = False
    boss_defeated = False
    player_hp = 100.0
    player_ammo = 50 
    player_stamina = 100.0
    is_exhausted = False
    player_pitch = 0.0
    shield_timer = 0 
    inventory = []
    immunity_timer = 0
    infinite_stamina_timer = 0
    
    def create_rect(r_x, r_y, r_w, r_h, type=C_EMPTY):
        for i in range(r_w):
            for j in range(r_h):
                if 0 <= r_x + i < MAP_DIM and 0 <= r_y + j < MAP_DIM:
                    map_data[r_x + i][r_y + j] = type

    def check_overlap(x, y, w, h, existing_rooms, buffer=2):
        for r in existing_rooms:
            if (x - buffer < r['x'] + r['w'] and x + w + buffer > r['x'] and
                y - buffer < r['y'] + r['h'] and y + h + buffer > r['y']):
                return True
        return False

    def h_tunnel(x1, x2, z):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for w in range(3): 
                if 0 < z+w < MAP_DIM-1: map_data[x][z+w] = C_EMPTY

    def v_tunnel(z1, z2, x):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            for w in range(3): 
                if 0 < x+w < MAP_DIM-1: map_data[x+w][z] = C_EMPTY

    rooms = [] 
    start_room = {'x': 5, 'y': 5, 'w': 10, 'h': 10}
    create_rect(5, 5, 10, 10, C_START)
    start_room['center'] = (10, 10)
    rooms.append(start_room)
    
    boss_room = {'x': MAP_DIM - 35, 'y': MAP_DIM - 35, 'w': 30, 'h': 30}
    create_rect(boss_room['x'], boss_room['y'], 30, 30, C_BOSS_ARENA)
    boss_room['center'] = (boss_room['x'] + 15, boss_room['y'] + 15)
    
    attempts = 0
    while len(rooms) < 25 and attempts < 1000: 
        attempts += 1
        shape_type = random.choice([0, 0, 1, 2]) 
        x = random.randint(10, MAP_DIM - 30); y = random.randint(10, MAP_DIM - 30)
        
        if shape_type == 0: 
            w = random.randint(6, 12); h = random.randint(6, 12)
            if not check_overlap(x, y, w, h, rooms):
                create_rect(x, y, w, h); rooms.append({'x':x, 'y':y, 'w':w, 'h':h, 'center':(x+w//2, y+h//2)})
        elif shape_type == 1: 
            w1 = random.randint(6, 10); h1 = random.randint(6, 10); w2 = random.randint(6, 10); h2 = random.randint(6, 10) 
            if random.random() < 0.5: x2, y2 = x + w1 - 2, y 
            else: x2, y2 = x, y + h1 - 2 
            if not check_overlap(x, y, w1+w2, h1+h2, rooms):
                create_rect(x, y, w1, h1); create_rect(x2, y2, w2, h2); rooms.append({'x':x, 'y':y, 'w':w1+w2, 'h':h1+h2, 'center':(x+w1//2, y+h1//2)})
        elif shape_type == 2:
            if not check_overlap(x, y, 16, 16, rooms):
                create_rect(x + 4, y, 6, 16); create_rect(x, y + 5, 16, 6); rooms.append({'x':x, 'y':y, 'w':16, 'h':16, 'center':(x+8, y+8)})

    rooms.append(boss_room)

    for i in range(len(rooms) - 1):
        r1 = rooms[i]; r2 = rooms[i+1]; x1, y1 = r1['center']; x2, y2 = r2['center']
        if random.random() < 0.5: h_tunnel(x1, x2, y1); v_tunnel(y1, y2, x2)
        else: v_tunnel(y1, y2, x1); h_tunnel(x1, x2, y2)

    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EMPTY:
                wx = x * CELL_SIZE; wz = z * CELL_SIZE
                r = random.random()
                
                if r < 0.015: 
                    mines.append({'x': wx, 'y': 0, 'z': wz, 'state': 'IDLE', 'timer': 120})
                elif r < 0.040: 
                    boss_minions.append({'x': wx, 'z': wz, 'home_x': wx, 'home_z': wz})
                elif r < 0.060: 
                    animals.append({'x': wx, 'z': wz, 'y': 0, 'cooldown': 0, 'angle': 0.0, 'hp': 1})
                elif r < 0.075:
                    gas_clouds.append({'x': wx, 'z': wz, 'y_base': 40, 'timer': 0})
                elif r < 0.10:
                    rr = random.random()
                    if rr < 0.4: l_type = 'HP'
                    elif rr < 0.8: l_type = 'AMMO'
                    elif rr < 0.9: l_type = 'SHIELD' 
                    elif rr < 0.95: l_type = 'STAMINA'
                    else: l_type = 'IMMUNITY'
                    loot.append({'x': wx, 'z': wz, 'type': l_type})

    boss_obj['x'] = (boss_room['x'] + 15) * CELL_SIZE
    boss_obj['z'] = (boss_room['y'] + 15) * CELL_SIZE
    boss_obj['hp'] = 800
    map_data[boss_room['x'] + 15][boss_room['y'] + 5] = C_EXIT
    player_pos = [start_room['center'][0] * CELL_SIZE, 20, start_room['center'][1] * CELL_SIZE]

    if display_list: glDeleteLists(display_list, 1); display_list = None

# ==========================================
# 2. Visuals
# ==========================================
def create_display_list():
    global display_list
    display_list = glGenLists(1)
    glNewList(display_list, GL_COMPILE)
    
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            cell = map_data[x][z]
            wx = x * CELL_SIZE; wz = z * CELL_SIZE
            
            if cell == C_WALL:
                glPushMatrix()
                glTranslatef(wx, WALL_HEIGHT/2, wz)
                glScalef(1, WALL_HEIGHT/CELL_SIZE, 1)
                col = 0.25 + random.uniform(-0.03, 0.03) # Darker stone
                glColor3f(col, col, col) 
                glutSolidCube(CELL_SIZE)
                glPopMatrix()
            elif cell == C_EMPTY or cell == C_START:
                if (x+z)%2 == 0: glColor3f(0.15, 0.12, 0.1) 
                else: glColor3f(0.18, 0.15, 0.12) 
                glBegin(GL_QUADS)
                glVertex3f(wx-CELL_SIZE/2, 0, wz-CELL_SIZE/2); glVertex3f(wx+CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz+CELL_SIZE/2); glVertex3f(wx-CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glEnd()
            elif cell == C_BOSS_ARENA:
                glColor3f(0.05, 0.05, 0.05) 
                glBegin(GL_QUADS)
                glVertex3f(wx-CELL_SIZE/2, 0, wz-CELL_SIZE/2); glVertex3f(wx+CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz+CELL_SIZE/2); glVertex3f(wx-CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glEnd()
            elif cell == C_EXIT:
                glPushMatrix()
                glTranslatef(wx, 10, wz)
                glColor3f(1, 1, 1)
                glutSolidSphere(10, 10, 10)
                glBegin(GL_LINES); glVertex3f(0,0,0); glVertex3f(0, 200, 0); glEnd()
                glPopMatrix()
    glEndList()

def draw_entities():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # FEATURE 2: LANDMINES (Flat Disks)
    for m in mines:
        if m['state'] == 'EXPLODED': continue
        glPushMatrix()
        glTranslatef(m['x'], 0.5, m['z']) # Very low to the floor
        if m['state'] == 'IDLE':
            glColor3f(0.3, 0.3, 0.3)
            glScalef(1.5, 0.1, 1.5) # Flat Disk shape
            glutSolidSphere(8, 16, 16)
            glColor3f(0.8, 0, 0) # Small red center
            glTranslatef(0, 5, 0)
            glutSolidSphere(1.5, 8, 8)
        elif m['state'] == 'ACTIVE':
            # Beeping logic
            if int(global_time * 15) % 2 == 0: glColor3f(1.0, 0.0, 0.0)
            else: glColor3f(0.2, 0.0, 0.0) 
            glScalef(1.6, 0.15, 1.6)
            glutSolidSphere(9, 16, 16)
        glPopMatrix()

    # PARTICLES
    for p in particles:
        glPushMatrix()
        glTranslatef(p['x'], p['y'], p['z'])
        glScalef(p['life']/10.0, p['life']/10.0, p['life']/10.0)
        if p.get('type') == 'SHIELD': glColor3f(0.0, 0.5, 1.0)
        else: glColor3f(1, 0.6 if random.random()>0.5 else 0, 0)
        glutSolidCube(3)
        glPopMatrix()

    # RABBITS
    for a in animals:
        glPushMatrix()
        glTranslatef(a['x'], 3, a['z'])
        glRotatef(math.degrees(a.get('angle', 0)), 0, 1, 0)
        glColor3f(0.5, 0.45, 0.4) 
        glPushMatrix(); glScalef(1, 0.7, 1.5); glutSolidCube(6); glPopMatrix() 
        glPushMatrix(); glTranslatef(0, 3, 3); glutSolidCube(4)
        glPushMatrix(); glTranslatef(-1, 2, 0); glRotatef(-90, 1, 0, 0); glutSolidCone(0.5, 3, 4, 4); glPopMatrix()
        glPushMatrix(); glTranslatef(1, 2, 0); glRotatef(-90, 1, 0, 0); glutSolidCone(0.5, 3, 4, 4); glPopMatrix()
        glPopMatrix() 
        glPushMatrix(); glTranslatef(0, 0, -4); glutSolidCone(1, 2, 4, 4); glPopMatrix() 
        for lx in [-2, 2]:
            for lz in [-2, 2]:
                glPushMatrix(); glTranslatef(lx, -2, lz); glRotatef(90, 1, 0, 0); glutSolidCone(0.5, 2, 4, 4); glPopMatrix() 
        glPopMatrix()

    # PURPLE SPHERES
    glColor3f(0.6, 0.0, 0.8) 
    for e in boss_minions:
        glPushMatrix()
        s = 1.0 + 0.1 * math.sin(global_time * 2)
        glTranslatef(e['x'], 5, e['z'])
        glScalef(s * 1.2, s * 0.4, s * 1.2)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()
        
    # FEATURE 3: GAS CLOUDS (Upgraded Green Spheres)
    glColor4f(0.2, 1.0, 0.2, 0.3) 
    for g in gas_clouds:
        glPushMatrix()
        y_float = g['y_base'] + math.sin(global_time) * 5
        glTranslatef(g['x'], y_float, g['z'])
        glutSolidSphere(15, 12, 12)
        glPopMatrix()

    # ROCKS
    glColor3f(0.4, 0.2, 0.1) 
    for r in animal_rocks:
        glPushMatrix()
        glTranslatef(r['x'], r['y'], r['z'])
        glutSolidSphere(3, 6, 6)
        glPopMatrix()

    # DAGGERS
    glColor3f(0.0, 1.0, 1.0) 
    for d in daggers:
        glPushMatrix()
        glTranslatef(d['x'], d['y'], d['z'])
        glRotatef(math.degrees(-d['angle']), 0, 1, 0)
        glRotatef(math.degrees(d.get('pitch', 0)), 1, 0, 0)
        glScalef(0.5, 0.5, 2.0); glutSolidSphere(2, 6, 6) 
        glPopMatrix()

    # LOOT
    for l in loot:
        glPushMatrix()
        glTranslatef(l['x'], 5 + math.sin(global_time*5)*2, l['z'])
        if l.get('type') == 'HP': glColor3f(1.0, 0.0, 0.0); glutSolidSphere(4, 8, 8)
        elif l.get('type') == 'AMMO': glColor3f(0.0, 1.0, 1.0); glScalef(0.5, 0.5, 2.0); glutSolidSphere(3, 6, 6)
        elif l.get('type') == 'SHIELD': glColor3f(0.0, 0.0, 1.0); glutSolidSphere(4, 8, 8)
        elif l.get('type') == 'STAMINA': glColor3f(0.0, 1.0, 0.8); glScalef(0.5, 2, 0.5); glutSolidCube(5)
        elif l.get('type') == 'IMMUNITY': glColor3f(0.8, 0, 1); glutSolidTorus(1, 2, 8, 8)
        glPopMatrix()

    # BOSS
    if boss_active and not boss_defeated:
        glPushMatrix()
        glTranslatef(boss_obj['x'], 30, boss_obj['z']) 
        glScalef(4, 4, 4) 
        glColor3f(0.3, 0.25, 0.2); glutSolidCube(10) 
        glTranslatef(0, 8, 0); glColor3f(0.4, 0.35, 0.3); glutSolidSphere(4, 10, 10) 
        glColor3f(1, 0, 0); glTranslatef(-2, 0, 3); glutSolidSphere(1, 5, 5)
        glTranslatef(4, 0, 0); glutSolidSphere(1, 5, 5)
        glPopMatrix()

    # BOULDERS (From Boss & Gas Clouds)
    glColor3f(0.2, 0.2, 0.2) 
    for b in boulders:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        glutSolidSphere(15, 10, 10) 
        glPopMatrix()
        
    glDisable(GL_BLEND)

def draw_minimap():
    glDisable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    map_size = 150; margin = 20
    glColor3f(0.1, 0.1, 0.1); glBegin(GL_QUADS)
    glVertex2f(margin, margin); glVertex2f(margin+map_size, margin)
    glVertex2f(margin+map_size, margin+map_size); glVertex2f(margin, margin+map_size); glEnd()
    glColor3f(0.5, 0.5, 0.5); glLineWidth(1); glBegin(GL_LINE_LOOP)
    glVertex2f(margin, margin); glVertex2f(margin+map_size, margin)
    glVertex2f(margin+map_size, margin+map_size); glVertex2f(margin, margin+map_size); glEnd()
    world_max = MAP_DIM * CELL_SIZE
    px = (player_pos[0] / world_max) * map_size
    py = (player_pos[2] / world_max) * map_size
    glColor3f(0, 1, 0); glPushMatrix(); glTranslatef(margin + px, margin + py, 0)
    glBegin(GL_TRIANGLE_FAN)
    for i in range(0, 360, 40): rad = math.radians(i); glVertex2f(math.cos(rad)*3, math.sin(rad)*3)
    glEnd(); glPopMatrix()
    if not boss_defeated:
        bx = (boss_obj['x'] / world_max) * map_size
        bz = (boss_obj['z'] / world_max) * map_size
        glColor3f(1, 0, 0); glPushMatrix(); glTranslatef(margin + bx, margin + bz, 0)
        glBegin(GL_QUADS); glVertex2f(-3, -3); glVertex2f(3, -3); glVertex2f(3, 3); glVertex2f(-3, 3); glEnd(); glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix(); glEnable(GL_DEPTH_TEST) 

def draw_hud():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glColor3f(1, 1, 1); glRasterPos2f(20, WINDOW_HEIGHT - 30)
    msg = f"HP: {int(player_hp)} | AMMO: {player_ammo}"
    for ch in msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    status_y = WINDOW_HEIGHT - 90
    
    # WINNING STRATEGY: HUD DISPLAY
    if shield_timer > 0:
        glColor3f(0, 0.5, 1); glRasterPos2f(20, status_y)
        s_msg = f"FORCEFIELD ACTIVE: {int(shield_timer/60)}s"
        for ch in s_msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        status_y -= 30
        
    if immunity_timer > 0:
        glColor3f(0, 1, 0); glRasterPos2f(20, status_y)
        msg = f"IMMUNITY: {int(immunity_timer/60)}s"
        for ch in msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        status_y -= 30
        
    bar_x = 20; bar_y = WINDOW_HEIGHT - 60; bar_w = 100
    glColor3f(0.3, 0.3, 0.3); glBegin(GL_QUADS); glVertex2f(bar_x, bar_y); glVertex2f(bar_x + bar_w, bar_y); glVertex2f(bar_x + bar_w, bar_y + 10); glVertex2f(bar_x, bar_y + 10); glEnd()
    if infinite_stamina_timer > 0: glColor3f(0, 1, 1)
    elif is_exhausted: glColor3f(1, 0, 0) 
    else: glColor3f(1, 1, 0) 
    fill_w = (player_stamina / max_stamina) * bar_w
    glBegin(GL_QUADS); glVertex2f(bar_x, bar_y); glVertex2f(bar_x + fill_w, bar_y); glVertex2f(bar_x + fill_w, bar_y + 10); glVertex2f(bar_x, bar_y + 10); glEnd()
    glColor3f(1, 1, 1); glRasterPos2f(bar_x + 110, bar_y)
    st_msg = "INF STM" if infinite_stamina_timer > 0 else "STM"
    for ch in st_msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    bag_content = ", ".join([str(item) for item in inventory])
    glRasterPos2f(20, status_y)
    for ch in f"Bag: {bag_content}": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # BOSS HUD & STRATEGY INSTRUCTIONS
    if boss_active and not boss_defeated:
        glColor3f(1, 0.2, 0.2); glRasterPos2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT - 50)
        b_msg = f"GOLEM: {boss_obj['hp']}/{boss_obj['max_hp']}"
        for ch in b_msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        # Player Instruction logic
        glColor3f(1, 1, 0); glRasterPos2f(WINDOW_WIDTH/2 - 200, 50)
        instr = "KEEP MOVING! BOULDERS FALLING! FIRE RAPIDLY TO STOP HEALING!"
        for ch in instr: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    if game_over:
        glColor3f(1, 0, 0); glRasterPos2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2)
        for ch in "YOU DIED": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # VICTORY MESSAGE
    if level_complete:
        glColor3f(0, 1, 0); glRasterPos2f(WINDOW_WIDTH/2 - 120, WINDOW_HEIGHT/2)
        for ch in "TANK DEFEATED! ESCAPED!": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glEnable(GL_DEPTH_TEST); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()

# ==========================================
# 3. Physics & Logic
# ==========================================
def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[2]-p2[2])**2)

def check_sprint():
    global is_sprinting
    is_sprinting = bool(glutGetModifiers() & GLUT_ACTIVE_SHIFT)

def update_physics():
    global player_pos, player_angle, global_time, player_hp, game_over, level_complete, player_ammo
    global mines, particles, animals, animal_rocks, daggers, loot, boulders, boss_minions, gas_clouds
    global boss_active, boss_obj, boss_defeated, player_speed, player_stamina, is_exhausted, is_sprinting
    global player_pitch, shield_timer, immunity_timer, infinite_stamina_timer, inventory
    
    if game_over or level_complete: return

    global_time += 0.05
    if shield_timer > 0: shield_timer -= 1
    if immunity_timer > 0: immunity_timer -= 1
    if infinite_stamina_timer > 0: infinite_stamina_timer -= 1
    
    move_speed = 0; strafe = 0
    if key_states.get(b'w'): move_speed = player_speed
    if key_states.get(b's'): move_speed = -player_speed
    if key_states.get(b'a'): strafe = -player_speed
    if key_states.get(b'd'): strafe = player_speed
    
    is_moving = (move_speed != 0) or (strafe != 0)
    if infinite_stamina_timer > 0:
        player_speed = base_speed * 2.0 if is_sprinting else base_speed
        player_stamina = 100; is_exhausted = False
    else:
        if is_sprinting and is_moving and not is_exhausted:
            player_speed = base_speed * 2.0; player_stamina -= 0.5 
            if player_stamina <= 0: player_stamina = 0; is_exhausted = True
        elif is_exhausted:
            player_speed = base_speed * 0.5; player_stamina += 0.1
            if player_stamina >= 30: is_exhausted = False
        else:
            player_speed = base_speed
            if not is_sprinting: player_stamina = min(100, player_stamina + 0.2)

    if key_states.get(GLUT_KEY_LEFT): player_angle -= 0.04
    if key_states.get(GLUT_KEY_RIGHT): player_angle += 0.04
    if key_states.get(GLUT_KEY_UP): player_pitch += 0.04
    if key_states.get(GLUT_KEY_DOWN): player_pitch -= 0.04
    player_pitch = max(-1.5, min(1.5, player_pitch))
    
    dx = math.sin(player_angle) * move_speed; dz = -math.cos(player_angle) * move_speed
    sdx = math.sin(player_angle + 1.57) * strafe; sdz = -math.cos(player_angle + 1.57) * strafe
    nx = player_pos[0] + dx + sdx; nz = player_pos[2] + dz + sdz
    
    def check_col(tx, tz):
        radius = 5
        for cx in [tx-radius, tx+radius]:
            for cz in [tz-radius, tz+radius]:
                 gx = int(cx // CELL_SIZE); gz = int(cz // CELL_SIZE)
                 if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM:
                     if map_data[gx][gz] == C_WALL: return True
        return False
    if not check_col(nx, player_pos[2]): player_pos[0] = nx
    if not check_col(player_pos[0], nz): player_pos[2] = nz
    
    gx, gz = int(player_pos[0] // CELL_SIZE), int(player_pos[2] // CELL_SIZE)
    if map_data[gx][gz] == C_BOSS_ARENA and not boss_active and not boss_defeated: boss_active = True
    if map_data[gx][gz] == C_EXIT and boss_defeated: level_complete = True

    # FEATURE 2: LANDMINES (Disk triggers & explosions)
    active_mines = []
    for m in mines:
        if m['state'] == 'EXPLODED': continue
        d_player = dist(player_pos, (m['x'], 0, m['z']))
        if m['state'] == 'IDLE' and d_player < 20: m['state'] = 'ACTIVE'
        if m['state'] == 'ACTIVE':
            m['timer'] -= 1
            if m['timer'] <= 0:
                m['state'] = 'EXPLODED'
                for _ in range(30): particles.append({'x': m['x'], 'y': 5, 'z': m['z'], 'dx': random.uniform(-4,4), 'dy': random.uniform(1,7), 'dz': random.uniform(-4,4), 'life': 50})
                
                # WINNING STRATEGY: SHIELD BLOCKS LANDMINES
                if d_player < 45 and immunity_timer <= 0 and shield_timer <= 0: player_hp -= 50
        active_mines.append(m)
    mines = active_mines
    
    # FEATURE 3: GAS CLOUDS (Spawn Boulders)
    for g in gas_clouds:
        d = dist(player_pos, (g['x'], 0, g['z']))
        if d < 350: 
            g['timer'] += 1
            if g['timer'] > 180: # Every ~3 seconds in range
                boulders.append({'x': player_pos[0], 'y': 250, 'z': player_pos[2], 'vy': 0})
                g['timer'] = 0

    # RABBITS & ENEMIES
    for a in animals:
        dx_p = a['x'] - player_pos[0]; dz_p = a['z'] - player_pos[2]
        dist_p = math.sqrt(dx_p**2 + dz_p**2)
        if dist_p < 200: 
            dir_x, dir_z = dx_p / dist_p, dz_p / dist_p
            nx, nz = a['x'] + dir_x * 4.0, a['z'] + dir_z * 4.0
            agx, agz = int(round(nx / CELL_SIZE)), int(round(nz / CELL_SIZE))
            if 0 <= agx < MAP_DIM and 0 <= agz < MAP_DIM and map_data[agx][agz] != C_WALL: a['x'], a['z'] = nx, nz
        if dist_p < 250:
            if a['cooldown'] > 0: a['cooldown'] -= 1
            else:
                vx, vz = (-dx_p / dist_p) * 3.5, (-dz_p / dist_p) * 3.5
                animal_rocks.append({'x': a['x'], 'y': 5, 'z': a['z'], 'vx': vx, 'vz': vz, 'life': 100})
                a['cooldown'] = 120 

    enemy_speed = base_speed / 8.0 
    for m in boss_minions:
        dx, dz = player_pos[0] - m['x'], player_pos[2] - m['z']
        dst = math.sqrt(dx*dx + dz*dz)
        # WINNING STRATEGY: SHIELD BLOCKS MINIONS
        if dst < 15 and immunity_timer <= 0 and shield_timer <= 0: player_hp -= 0.5
        elif dst < 400: m['x'] += (dx/dst) * enemy_speed; m['z'] += (dz/dst) * enemy_speed

    # FEATURE 4: BOSS 3 - THE TANK GOLEM
    if boss_active:
        boss_obj['timer'] += 1
        bx, bz = boss_obj['x'], boss_obj['z']
        v_to_p_x, v_to_p_z = player_pos[0] - bx, player_pos[2] - bz
        d_to_p = math.sqrt(v_to_p_x**2 + v_to_p_z**2)
        
        # Massive Hitbox interaction (Close contact)
        if d_to_p < 30:
            # WINNING STRATEGY: SHIELD BLOCKS BOSS SMACK
            if immunity_timer <= 0 and shield_timer <= 0: player_hp -= 1.0 
            player_pos[0] += (v_to_p_x / d_to_p) * 10; player_pos[2] += (v_to_p_z / d_to_p) * 10
            
        # Movement: Very slow, moves directly at player
        if d_to_p > 25: 
            boss_obj['x'] += (v_to_p_x / d_to_p) * (base_speed * 0.15)
            boss_obj['z'] += (v_to_p_z / d_to_p) * (base_speed * 0.15)
            
        # Attack (Boulder Rain): Spawns rocks at y=200 above player
        if boss_obj['timer'] % 80 == 0: 
            boulders.append({'x': player_pos[0], 'y': 200, 'z': player_pos[2], 'vy': 0})
            
        # Minion Summoning
        if boss_obj['timer'] % 400 == 0: 
            boss_minions.append({'x': boss_obj['x'] + random.randint(-50,50), 'z': boss_obj['z'] + random.randint(-50,50)})
            
        # Healing Logic: Cannot play passively (DPS race)
        if boss_obj['timer'] % 300 == 0 and boss_obj['hp'] < boss_obj['max_hp']: 
            boss_obj['hp'] += 20

    # BOULDERS
    active_boulders = []
    for b in boulders:
        b['vy'] += 0.5; b['y'] -= b['vy']
        if b['y'] <= 0:
            for _ in range(10): particles.append({'x': b['x'], 'y': 2, 'z': b['z'], 'dx': random.uniform(-2,2), 'dy': random.uniform(2,6), 'dz': random.uniform(-2,2), 'life': 20})
            if dist(player_pos, (b['x'], 0, b['z'])) < 30: 
                # WINNING STRATEGY: SHIELD BLOCKS BOULDERS (Logic already existed, but naming updated)
                if shield_timer > 0:
                     for _ in range(20): particles.append({'x': player_pos[0], 'y': 10, 'z': player_pos[2], 'dx': random.uniform(-4,4), 'dy': random.uniform(2,8), 'dz': random.uniform(-4,4), 'life': 30, 'type': 'SHIELD'})
                elif immunity_timer <= 0: player_hp = 0; game_over = True
        else: active_boulders.append(b)
    boulders = active_boulders

    # FEATURE 2: DAGGERS vs MINES (Shoot to clear)
    active_daggers = []
    for d in daggers:
        d['x'] += math.sin(d['angle']) * math.cos(d.get('pitch', 0)) * 8.0
        d['y'] += math.sin(d.get('pitch', 0)) * 8.0
        d['z'] -= math.cos(d['angle']) * math.cos(d.get('pitch', 0)) * 8.0
        d['life'] -= 1
        hit = False
        dgx, dgz = int(round(d['x'] / CELL_SIZE)), int(round(d['z'] / CELL_SIZE))
        if 0 <= dgx < MAP_DIM and 0 <= dgz < MAP_DIM and map_data[dgx][dgz] == C_WALL: hit = True
        if d['y'] < 0: hit = True

        for m in mines:
            if m['state'] != 'EXPLODED' and dist((d['x'], 0, d['z']), (m['x'], 0, m['z'])) < 20:
                m['state'] = 'ACTIVE'; m['timer'] = 0; hit = True

        # VICTORY LOGIC: HP hits 0
        if boss_active and not hit:
            if dist((d['x'], 0, d['z']), (boss_obj['x'], 0, boss_obj['z'])) < 50:
                hit = True; boss_obj['hp'] -= 15
                if boss_obj['hp'] <= 0: 
                    boss_active = False
                    boss_defeated = True
                    level_complete = True # Triggers VICTORY message
                    boulders = []
                    boss_minions = []

        if not hit:
            active_animals = []
            for a in animals:
                if dist((d['x'], 0, d['z']), (a['x'], 0, a['z'])) < 15:
                    hit = True; loot.append({'x': a['x'], 'z': a['z'], 'type': random.choice(['HP', 'AMMO', 'SHIELD', 'STAMINA', 'IMMUNITY'])})
                else: active_animals.append(a)
            animals = active_animals

        if not hit:
            active_minions = []
            for m in boss_minions:
                if dist((d['x'], 0, d['z']), (m['x'], 0, m['z'])) < 15:
                    hit = True; loot.append({'x': m['x'], 'z': m['z'], 'type': random.choice(['HP', 'AMMO', 'SHIELD', 'STAMINA', 'IMMUNITY'])})
                else: active_minions.append(m)
            boss_minions = active_minions
            
        if not hit and d['life'] > 0: active_daggers.append(d)
    daggers = active_daggers

    # LOOT & ROCKS
    active_loot = []
    for l in loot:
        if dist(player_pos, (l['x'], 0, l['z'])) < 15: 
            if l.get('type') == 'HP': 
                if player_hp >= 100: inventory.append("HP Pill")
                else: player_hp = min(100, player_hp + 20)
            elif l.get('type') == 'AMMO': player_ammo += 5
            
            # WINNING STRATEGY: SHIELD ORB (Blue Sphere)
            elif l.get('type') == 'SHIELD': 
                shield_timer = 600 # 10 Seconds (60fps * 10)
                
            # WINNING STRATEGY: STAMINA PILL (Cyan Cube)
            elif l.get('type') == 'STAMINA': 
                inventory.append("Stamina Pill")
                
            elif l.get('type') == 'IMMUNITY': inventory.append("Immunity")
        else: active_loot.append(l)
    loot = active_loot

    active_rocks = []
    for r in animal_rocks:
        r['x'] += r['vx']; r['z'] += r['vz']; r['life'] -= 1
        if dist(player_pos, (r['x'], 0, r['z'])) < 10:
            # WINNING STRATEGY: SHIELD BLOCKS ROCKS
            if immunity_timer <= 0 and shield_timer <= 0: player_hp -= 5
            continue 
        if 0 <= int(r['x'] // CELL_SIZE) < MAP_DIM and r['life'] > 0: active_rocks.append(r)
    animal_rocks = active_rocks

    if player_hp <= 0: game_over = True
    active_particles = []
    for p in particles:
        p['x'] += p['dx']; p['y'] += p['dy']; p['z'] += p['dz']; p['dy'] -= 0.1; p['life'] -= 1
        if p['life'] > 0 and p['y'] > 0: active_particles.append(p)
    particles = active_particles

def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluPerspective(60, WINDOW_WIDTH/WINDOW_HEIGHT, 1, 1000); glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    lx, ly, lz = math.sin(player_angle) * math.cos(player_pitch), math.sin(player_pitch), -math.cos(player_angle) * math.cos(player_pitch)
    gluLookAt(player_pos[0], 25, player_pos[2], player_pos[0] + lx, 25 + ly, player_pos[2] + lz, 0, 1, 0)

def keyDown(key, x, y):
    global immunity_timer, player_hp, infinite_stamina_timer, inventory
    check_sprint(); key_states[key] = True; key_states[key.lower()] = True 
    if key == b'r': generate_level_3()
    if key == b'1' and "Immunity" in inventory: inventory.remove("Immunity"); immunity_timer = 360
    if key == b'2' and "HP Pill" in inventory and player_hp < 100: inventory.remove("HP Pill"); player_hp = min(100, player_hp+20)
    
    # WINNING STRATEGY: USE STAMINA PILL
    if key == b'3' and "Stamina Pill" in inventory: 
        inventory.remove("Stamina Pill")
        infinite_stamina_timer = 600

def keyUp(key, x, y): check_sprint(); key_states[key] = False; key_states[key.lower()] = False
def specialDown(key, x, y): check_sprint(); key_states[key] = True
def specialUp(key, x, y): check_sprint(); key_states[key] = False

def mouseListener(button, state, x, y):
    global player_ammo
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        if player_ammo > 0:
            player_ammo -= 1
            daggers.append({'x': player_pos[0], 'y': 20, 'z': player_pos[2], 'angle': player_angle, 'pitch': player_pitch, 'life': 60})

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); setup_camera()
    if display_list is None: create_display_list()
    glCallList(display_list); draw_entities(); draw_minimap(); draw_hud(); glutSwapBuffers()

def idle(): update_physics(); glutPostRedisplay()

def init_fog():
    glEnable(GL_FOG)
    fog_color = (0.05, 0.05, 0.05, 1.0) # Very dark grey
    glFogfv(GL_FOG_COLOR, fog_color)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 50.0)
    glFogf(GL_FOG_END, 600.0)
    glClearColor(0.05, 0.05, 0.05, 1.0)

def main():
    glutInit(); glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH); glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT); glutCreateWindow(b"Level 3: The Final Stand")
    glEnable(GL_DEPTH_TEST); init_fog(); generate_level_3()
    glutDisplayFunc(showScreen); glutIdleFunc(idle); glutKeyboardFunc(keyDown); glutKeyboardUpFunc(keyUp); glutSpecialFunc(specialDown); glutSpecialUpFunc(specialUp); glutMouseFunc(mouseListener); glutMainLoop()

if __name__ == "__main__":
    main()