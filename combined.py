from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys

# Import the level modules
import level1
import level2
import level3

# ==========================================
# Global Configuration
# ==========================================
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

# Game State
current_level = 1
game_won = False

# ==========================================
# Level Transition Logic
# ==========================================
def init_game():
    print(">>> STARTING LEVEL 1: THE TOXIC SWAMPLANDS <<<")
    # Level 1 uses generate_level_1
    level1.generate_level_1() 

def transition_to_level_2():
    global current_level
    print("\n>>> LEVEL 1 COMPLETE! ENTERING LEVEL 2: THE CRIMSON ARENA <<<")
    
    # 1. Capture Stats from Level 1
    saved_hp = level1.player_hp
    saved_ammo = level1.player_ammo
    # (Level 1 uses 'inventory' list, Level 2 tracks diamonds differently, but we pass HP/Ammo)
    
    # 2. Init Level 2 (Uses generate_level)
    level2.generate_level()
    
    # 3. Inject Stats
    level2.player_hp = saved_hp
    level2.player_ammo = saved_ammo
    
    current_level = 2

def transition_to_level_3():
    global current_level
    print("\n>>> LEVEL 2 COMPLETE! ENTERING LEVEL 3: THE IRON STRONGHOLD <<<")
    
    # 1. Capture Stats from Level 2
    saved_hp = level2.player_hp
    saved_ammo = level2.player_ammo
    
    # 2. Init Level 3 (Uses generate_level_3)
    level3.generate_level_3()
    
    # 3. Inject Stats
    level3.player_hp = saved_hp
    level3.player_ammo = saved_ammo
    
    current_level = 3

# ==========================================
# Master Callbacks (Routing Logic)
# ==========================================
def showScreen():
    if game_won:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        
        glColor3f(0, 1, 0)
        glRasterPos2f(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2)
        for ch in "YOU WIN! GAME OVER":
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
            
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glutSwapBuffers()
        return

    # --- CRITICAL FIX: FORCE 3D PERSPECTIVE ---
    # Level 2 relies on Main setting the matrix, Level 1 sets it itself.
    # We set it here globally to prevent black screens.
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 2500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_DEPTH_TEST)
    # ------------------------------------------

    # --- ROUTING TABLE ---
    if current_level == 1: 
        level1.showScreen()   
    elif current_level == 2: 
        level2.draw_scene()   # <--- FIXED: Level 2 uses 'draw_scene'
    elif current_level == 3: 
        level3.showScreen()

def idle():
    global game_won
    
    if current_level == 1:
        level1.idle()
        if level1.level_complete:
            transition_to_level_2()
            
    elif current_level == 2:
        level2.update_logic() # <--- FIXED: Level 2 uses 'update_logic'
        if level2.level_complete:
            transition_to_level_3()
            
    elif current_level == 3:
        level3.idle()
        if level3.level_complete:
            game_won = True
            print("\n>>> YOU WIN! <<<")

# --- INPUT ROUTING ---
def keyDown(key, x, y):
    if current_level == 1: level1.keyDown(key, x, y)
    elif current_level == 2: level2.keyboard(key, x, y) # <--- FIXED
    elif current_level == 3: level3.keyDown(key, x, y)

def keyUp(key, x, y):
    if current_level == 1: level1.keyUp(key, x, y)
    elif current_level == 2: level2.keyboard_up(key, x, y) # <--- FIXED
    elif current_level == 3: level3.keyboardUpListener(key, x, y)

def specialDown(key, x, y):
    if current_level == 1: level1.specialDown(key, x, y)
    elif current_level == 2: level2.special(key, x, y) # <--- FIXED
    elif current_level == 3: level3.specialKeyListener(key, x, y)

def specialUp(key, x, y):
    if current_level == 1: level1.specialUp(key, x, y)
    elif current_level == 2: level2.special_up(key, x, y) # <--- FIXED
    elif current_level == 3: level3.specialKeyUpListener(key, x, y)

def mouseListener(button, state, x, y):
    if current_level == 1: level1.mouseListener(button, state, x, y)
    elif current_level == 2: level2.mouse(button, state, x, y) # <--- FIXED
    elif current_level == 3: level3.mouseListener(button, state, x, y)

# ==========================================
# Main
# ==========================================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"The Cursed Labyrinth: Complete Saga")
    
    glEnable(GL_DEPTH_TEST)
    init_game()
    
    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    
    # Register inputs
    glutKeyboardFunc(keyDown)
    glutKeyboardUpFunc(keyUp)
    glutSpecialFunc(specialDown)
    glutSpecialUpFunc(specialUp)
    glutMouseFunc(mouseListener)
    
    glutMainLoop()

if __name__ == "__main__":
    main()









##level1
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_TIMES_ROMAN_24
import math
import random


# ==========================================
# Global Configuration
# ==========================================
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

# Scale Factors
MAP_DIM = 140       
CELL_SIZE = 30      
WALL_HEIGHT = 80    
FOV_Y = 90

# Cell Types
C_EMPTY = 0
C_WALL = 1
C_ACID = 2
C_BOSS = 3
C_START = 4
C_GATE = 5
C_EXIT = 6

# Map Data
map_data = [] 
solution_path = []  
display_list = None 

# --- ENTITY LISTS ---
enemies = []    
animals = []
gas_clouds = [] 
daggers = []
loot = []
rain_drops = []
poison_ghosts = [] 

# --- GAME STATE ---
ghosts_captured = 0
boss_active = False
boss_defeated = False
boss_obj = {
    'x': 0, 
    'z': 0, 
    'hp': 500, 
    'max_hp': 500, 
    'timer': 0, 
    'teleport_cd': 0
}
rain_active = False
rain_duration = 0

# --- PLAYER STATE ---
player_pos = [0, 0, 0]
player_angle = 1.57 
base_speed = 5 
player_speed = base_speed
boss_speed = 3.5 # Faster boss (increased from 2.0)
enemy_speed = base_speed / 9.0 
animal_speed = base_speed / 3.0 
dagger_speed = 15.0 

key_states = {}

# Stats
player_hp = 5000.0
max_player_hp = 8000.0
player_ammo = 25000
inventory = ['Capture Bottle', 'Capture Bottle', 'Capture Bottle','Capture Bottle', 'Capture Bottle', 'Capture Bottle', 'Capture Bottle', 'Capture Bottle', 'Capture Bottle'] 
immunity_timer = 0 
has_green_gem = False

# Stamina
player_stamina = 100.0
max_stamina = 100.0
is_exhausted = False
infinite_stamina_timer = 0 
is_sprinting = False 

# Animation & Cheats
global_time = 0.0
acid_level = 0.0
game_over = False
level_complete = False 
map_visible = False 


def solve_maze():
    global solution_path
    
    # 1. Define Start (Player Spawn) & End (Boss) Grid Coordinates
    start_node = (10, 10) 
    target_gx = int(boss_obj['x'] // CELL_SIZE)
    target_gz = int(boss_obj['z'] // CELL_SIZE)
    target_node = (target_gx, target_gz)
    
    # 2. BFS Algorithm
    queue = [start_node]
    visited = {start_node}
    came_from = {start_node: None}
    
    found_dest = None
    
    while queue:
        current = queue.pop(0)
        
        # If we reached the boss center or inside boss arena
        if current == target_node or map_data[current[0]][current[1]] == C_BOSS:
            found_dest = current
            break
            
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = current[0] + dx, current[1] + dy
            
            # Bounds check
            if 0 <= nx < MAP_DIM and 0 <= ny < MAP_DIM:
                if (nx, ny) not in visited:
                    # Valid path? (Not a wall)
                    if map_data[nx][ny] != C_WALL:
                        visited.add((nx, ny))
                        came_from[(nx, ny)] = current
                        queue.append((nx, ny))
    
    # 3. Reconstruct Path
    path = []
    if found_dest:
        curr = found_dest
        while curr:
            path.append(curr)
            curr = came_from[curr]
        # Reverse to get Start -> End
        path.reverse()
        
    solution_path = path

# ==========================================
# 1. Map Generation
# ==========================================
def generate_level_1():
    global map_data, player_pos, display_list, gas_clouds, enemies, animals, loot, particles, boss_obj, boss_active, boss_defeated, rain_drops, has_green_gem, poison_ghosts, ghosts_captured
    
    # 1. Fill world with Solid Walls
    map_data = [[C_WALL for _ in range(MAP_DIM)] for _ in range(MAP_DIM)]
    
    # Reset Entities
    gas_clouds = []
    enemies = []
    animals = []
    loot = []
    particles = []
    rain_drops = []
    poison_ghosts = []
    ghosts_captured = 0
    boss_active = False
    boss_defeated = False
    has_green_gem = False
    
    # --- HELPER FUNCTIONS ---
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
                if 0 < z+w < MAP_DIM-1:
                    map_data[x][z+w] = C_EMPTY

    def v_tunnel(z1, z2, x):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            for w in range(3): 
                if 0 < x+w < MAP_DIM-1:
                    map_data[x+w][z] = C_EMPTY

    # --- A. DEFINE CRITICAL ROOMS ---
    rooms = [] 
    
    # 1. Start Room (Bottom Left)
    start_room = {'x': 5, 'y': 5, 'w': 10, 'h': 10}
    create_rect(5, 5, 10, 10, C_START)
    start_room['center'] = (10, 10)
    rooms.append(start_room)
    
    # 2. Boss Arena (Top Right)
    boss_room = {'x': MAP_DIM - 35, 'y': MAP_DIM - 35, 'w': 30, 'h': 30}
    create_rect(boss_room['x'], boss_room['y'], 30, 30, C_BOSS)
    boss_room['center'] = (boss_room['x'] + 15, boss_room['y'] + 15)
    
    # --- B. GENERATE RANDOM ROOMS ---
    attempts = 0
    while len(rooms) < 20 and attempts < 1000:
        attempts += 1
        
        shape_type = random.choice([0, 0, 1, 2]) 
        x = random.randint(10, MAP_DIM - 30)
        y = random.randint(10, MAP_DIM - 30)
        
        if shape_type == 0: # Box
            w = random.randint(6, 12)
            h = random.randint(6, 12)
            if not check_overlap(x, y, w, h, rooms):
                create_rect(x, y, w, h)
                rooms.append({'x':x, 'y':y, 'w':w, 'h':h, 'center':(x+w//2, y+h//2)})
                
        elif shape_type == 1: # L-Shape
            w1 = random.randint(6, 10)
            h1 = random.randint(6, 10) 
            w2 = random.randint(6, 10)
            h2 = random.randint(6, 10) 
            
            if random.random() < 0.5: 
                x2, y2 = x + w1 - 2, y 
            else:
                x2, y2 = x, y + h1 - 2 
                
            if not check_overlap(x, y, w1+w2, h1+h2, rooms):
                create_rect(x, y, w1, h1)
                create_rect(x2, y2, w2, h2)
                rooms.append({'x':x, 'y':y, 'w':w1+w2, 'h':h1+h2, 'center':(x+w1//2, y+h1//2)})
                
        elif shape_type == 2: # Cross Shape
            if not check_overlap(x, y, 16, 16, rooms):
                create_rect(x + 4, y, 6, 16)
                create_rect(x, y + 5, 16, 6)
                rooms.append({'x':x, 'y':y, 'w':16, 'h':16, 'center':(x+8, y+8)})

    rooms.append(boss_room)

  
    boss_room['center'] = (MAP_DIM - 37, MAP_DIM - 20)
    
    for i in range(len(rooms) - 1):
        r1 = rooms[i]
        r2 = rooms[i+1]
        
        x1, y1 = r1['center']
        x2, y2 = r2['center']
        
        if random.random() < 0.5:
            h_tunnel(x1, x2, y1)
            v_tunnel(y1, y2, x2)
        else:
            v_tunnel(y1, y2, x1)
            h_tunnel(x1, x2, y2)

    # --- C. FINALIZE BOSS ARENA (Enclosed + Swampy) ---
    b_x = MAP_DIM - 35
    b_y = MAP_DIM - 35
    b_w = 30
    b_h = 30
    
    # 2. Build the Arena Floor and Walls
    for i in range(-1, b_w + 1):
        for j in range(-1, b_h + 1):
            # Coordinates
            cx = b_x + i
            cy = b_y + j
            
            if 0 <= cx < MAP_DIM and 0 <= cy < MAP_DIM:
                # If it's on the border, make it a WALL
                if i == -1 or i == b_w or j == -1 or j == b_h:
                    map_data[cx][cy] = C_WALL
                else:
                    # Inside is the Arena
                    # [Requirement] Extra acid pools/swamps inside the arena (30% chance)
                    if random.random() < 0.3:
                        map_data[cx][cy] = C_ACID
                    else:
                        map_data[cx][cy] = C_BOSS

    # --- D. PLACE GATE ---
    # Entrance on the Left Wall
    gate_x = b_x - 1
    mid_y = b_y + (b_h // 2)
    
    # 7-block wide gate
    for k in range(-3, 4): 
        if 0 <= gate_x < MAP_DIM and 0 <= mid_y + k < MAP_DIM:
            map_data[gate_x][mid_y + k] = C_GATE
            # Ensure immediate entry path is clear
            if gate_x - 1 >= 0:
                map_data[gate_x - 1][mid_y + k] = C_EMPTY

    # --- E. POPULATE ENTITIES ---
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EMPTY:
                wx = x * CELL_SIZE
                wz = z * CELL_SIZE
                
                # Acid Pools
                if random.random() < 0.1:
                    map_data[x][z] = C_ACID
                else:
                    r = random.random()
                    if r < 0.02:
                        enemies.append({'x': wx, 'z': wz, 'home_x': wx, 'home_z': wz})
                    elif r < 0.03:
                        animals.append({'x': wx, 'z': wz, 'home_x': wx, 'home_z': wz, 'angle': 0, 'active': True})
                   
    # Spawn Poison Ghosts
    ghost_attempts = 0
    while len(poison_ghosts) < 3 and ghost_attempts < 1000:
        ghost_attempts += 1
        rx = random.randint(10, MAP_DIM-10)
        rz = random.randint(10, MAP_DIM-10)
        if map_data[rx][rz] == C_EMPTY:
            dist_start = math.sqrt((rx*CELL_SIZE - start_room['center'][0]*CELL_SIZE)**2 + (rz*CELL_SIZE - start_room['center'][1]*CELL_SIZE)**2)
            if dist_start > 800:
                poison_ghosts.append({
                    'x': rx*CELL_SIZE, 
                    'z': rz*CELL_SIZE, 
                    'stun_timer': 0,
                    'state': 'ROAM',  # Start roaming
                    'seen_timer': 0   # How long player has been looking at it
                })

    boss_obj['x'] = (boss_room['x'] + 15) * CELL_SIZE
    boss_obj['z'] = (boss_room['y'] + 15) * CELL_SIZE
    boss_obj['hp'] = 500
    player_pos = [start_room['center'][0] * CELL_SIZE, 20, start_room['center'][1] * CELL_SIZE]
    
    solve_maze()

    if display_list:
        glDeleteLists(display_list, 1)
        display_list = None

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
            wx = x * CELL_SIZE
            wz = z * CELL_SIZE
            
            if cell == C_WALL:
                glPushMatrix()
                glTranslatef(wx, WALL_HEIGHT/2, wz)
                glScalef(1, WALL_HEIGHT/CELL_SIZE, 1) 
                
                # [VISUAL FIX] Organic "Poisoned Earth" Look
                # 1. Calculate Contamination Noise (Organic patches)
                # Low freq (x*0.2) creates large patches, High freq (random) creates grit
                contamination = math.sin(x * 0.2) * math.cos(z * 0.25)
                grit = random.uniform(-0.05, 0.05)
                
                if contamination > 0.1:
                    # POISONED WALL (Sickly Green/Mud mix)
                    # The higher the contamination, the greener it gets
                    r = 0.25 + grit
                    g = 0.35 + (contamination * 0.3) + grit
                    b = 0.15 + grit
                else:
                    # NORMAL EARTH/ROCK (Dark Muddy Brown)
                    r = 0.35 + grit
                    g = 0.25 + grit
                    b = 0.20 + grit
                
                glColor3f(r, g, b) 
                glutSolidCube(CELL_SIZE)
                
                glPopMatrix()
                
            elif cell == C_EMPTY or cell == C_START:
                # Darker Forest Floor to match new walls
                if (x+z)%2 == 0: 
                    glColor3f(0.08, 0.3, 0.08) 
                else: 
                    glColor3f(0.12, 0.35, 0.12) 
                
                glBegin(GL_QUADS)
                glVertex3f(wx-CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glVertex3f(wx-CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glEnd()
                
            elif cell == C_BOSS:
                # Dark Stone for Boss Arena
                glColor3f(0.1, 0.1, 0.1)
                glBegin(GL_QUADS)
                glVertex3f(wx-CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glVertex3f(wx-CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glEnd()
                
            elif cell == C_GATE:
                glPushMatrix()
                glTranslatef(wx, WALL_HEIGHT/2, wz)
                glScalef(0.5, WALL_HEIGHT/CELL_SIZE, 1)
                glColor3f(0.0, 1.0, 0.5) 
                glutSolidCube(CELL_SIZE)
                glPopMatrix()
    glEndList()

def draw_entities():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # 1. Acid (Swamp)
    # CHANGED: Bright Neon Green
    glColor4f(0.4, 1.0, 0.0, 0.8) 
    
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_ACID:
                wx = x * CELL_SIZE
                wz = z * CELL_SIZE
                glPushMatrix()
                # Downward Pulse Animation
                pulse = math.sin(global_time * 2) * 2 - 5
                
                # Move to the specific cell location
                glTranslatef(wx, pulse, wz) 
                
                # [FIX] Draw relative to the translated center (Local Coordinates)
                glBegin(GL_QUADS)
                glVertex3f(-CELL_SIZE/2, 0, -CELL_SIZE/2)
                glVertex3f( CELL_SIZE/2, 0, -CELL_SIZE/2)
                glVertex3f( CELL_SIZE/2, 0,  CELL_SIZE/2)
                glVertex3f(-CELL_SIZE/2, 0,  CELL_SIZE/2)
                glEnd()
                glPopMatrix()
    
    # 2. Gas
    glColor4f(0.6, 0.8, 0.6, 0.4) 
    for g in gas_clouds:
        glPushMatrix()
        glTranslatef(g['x'], g['y_base'] + math.sin(global_time)*3, g['z'])
        glutSolidSphere(12, 10, 10)
        glPopMatrix()
        
    # 3. Poison Ghosts (Updated Shape)
    glColor4f(0.0, 1.0, 0.8, 0.5) 

    # 3. Poison Ghosts (Visuals: Normal, Stunned, or Tired)
    for g in poison_ghosts:
        glPushMatrix()
        
        # Priority 1: Stunned (White & Shaking)
        if g.get('stun_timer', 0) > 0:
            glColor4f(1.0, 1.0, 1.0, 0.9) 
            shake = random.uniform(-2, 2)
            glTranslatef(g['x'] + shake, 60, g['z'] + shake)
            
        # Priority 2: Fatigued (Purple & Low to ground)
        elif g.get('fatigue', 0) > 0:
            glColor4f(0.8, 0.4, 0.8, 0.6) 
            glTranslatef(g['x'], 40, g['z'])
            
        # Priority 3: Normal (Cyan & Floating High)
        else:
            glColor4f(0.0, 1.0, 0.8, 0.5) 
            float_y = 60 + math.sin(global_time * 3) * 5
            glTranslatef(g['x'], float_y, g['z'])
        
        # Draw Ghost Model
        glutSolidSphere(10, 12, 12)
        glPushMatrix(); glTranslatef(0, -5, 0); glRotatef(90, 1, 0, 0); glutSolidCone(6, 20, 8, 8); glPopMatrix()
        
        # Arms
        glColor4f(1, 1, 1, 0.5) 
        glPushMatrix(); glTranslatef(-8, 0, 0); glRotatef(45, 0, 0, 1); glScalef(0.5, 3, 0.5); glutSolidCube(4); glPopMatrix()
        glPushMatrix(); glTranslatef(8, 0, 0); glRotatef(-45, 0, 0, 1); glScalef(0.5, 3, 0.5); glutSolidCube(4); glPopMatrix()
        
        glPopMatrix()

    glDisable(GL_BLEND)

    # 4. Enemies
    glColor3f(0.6, 0.0, 0.8) 
    for e in enemies:
        glPushMatrix()
        s = 1.0 + 0.1 * math.sin(global_time * 2)
        glTranslatef(e['x'], 5, e['z']) 
        glScalef(s * 1.2, s * 0.4, s * 1.2) 
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

    # 5. Animals
    for a in animals:
        if a['active']:
            glPushMatrix()
            glTranslatef(a['x'], 3, a['z'])
            glRotatef(math.degrees(a.get('angle', 0)), 0, 1, 0)
            glColor3f(0.6, 0.55, 0.5) 
            glPushMatrix()
            glScalef(1, 0.7, 1.5)
            glutSolidCube(6)
            glPopMatrix() 
            glPushMatrix()
            glTranslatef(0, 3, 3)
            glutSolidCube(4)
            glPushMatrix()
            glTranslatef(-1, 2, 0)
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(0.5, 3, 4, 4)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(1, 2, 0)
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(0.5, 3, 4, 4)
            glPopMatrix()
            glPopMatrix() 
            glPushMatrix()
            glTranslatef(0, 0, -4)
            glutSolidCone(1, 2, 4, 4)
            glPopMatrix() 
            for lx in [-2, 2]:
                for lz in [-2, 2]:
                    glPushMatrix()
                    glTranslatef(lx, -2, lz)
                    glRotatef(90, 1, 0, 0)
                    glutSolidCone(0.5, 2, 4, 4)
                    glPopMatrix() 
            glPopMatrix()

    # 6. Daggers
    glColor3f(0.75, 0.75, 0.8) 
    for d in daggers:
        glPushMatrix()
        glTranslatef(d['x'], d['y'], d['z'])
        glRotatef(math.degrees(-d['angle']), 0, 1, 0) 
        glRotatef(20, 1, 0, 0) 
        glutSolidCone(1, 6, 8, 8)
        glPopMatrix()
        

    # 8. Loot
    for l in loot:
        glPushMatrix()
        glTranslatef(l['x'], 10, l['z'])
        glRotatef(global_time * 50, 0, 1, 0) 
        if l['type'] == 'HP':
            glColor3f(1, 0, 0)
            glutSolidSphere(5, 8, 8)
        elif l['type'] == 'AMMO':
            glColor3f(0.3, 0.3, 0.3)
            glScalef(0.5, 2, 0.5)
            glutSolidCube(5)
        elif l['type'] == 'IMMUNITY':
            glColor3f(0.8, 0, 1)
            glutSolidTorus(2, 5, 8, 8)
        elif l['type'] == 'STAMINA':
            glColor3f(0.0, 1.0, 0.8)
            glScalef(0.5, 2, 0.5)
            glutSolidCube(5)
        elif l['type'] == 'BOTTLE':
            glColor3f(0.0, 0.5, 1.0)
            glScalef(0.6, 1.5, 0.6)
            glutSolidCube(6)
        elif l['type'] == 'POISON_GEM':
            glColor3f(0.5, 0.0, 1.0) # Purple Gem
            glScalef(1.5, 1.5, 1.5)
            glScalef(1, 2, 1)
            glutSolidOctahedron()
        glPopMatrix()
        
    # 9. Boss
    if boss_active or (not boss_defeated and in_boss_arena(player_pos, 1000)):
        glPushMatrix()
        glTranslatef(boss_obj['x'], 20 + math.sin(global_time)*2, boss_obj['z'])
        glScalef(2, 2, 2)
        glColor3f(0.4, 0.0, 0.4)
        glutSolidSphere(15, 16, 16)
        glColor3f(0.0, 1.0, 0.0)
        for ang in range(0, 360, 90):
             rad = math.radians(ang + global_time*50)
             ox = math.cos(rad) * 12
             oz = math.sin(rad) * 12
             glPushMatrix()
             glTranslatef(ox, 0, oz)
             glutSolidSphere(6, 10, 10)
             glPopMatrix()
        glPopMatrix()
        
    # 10. Rain
    if rain_active:
        glLineWidth(1)
        glBegin(GL_LINES)
        glColor3f(0.2, 1.0, 0.2)
        for r in rain_drops:
            glVertex3f(r['x'], r['y'], r['z'])
            glVertex3f(r['x'], r['y']-15, r['z'])
        glEnd()

def in_boss_arena(pos, padding=0):
    # Boss Room is at MAP_DIM - 35, Size 30x30
    # World Coordinates conversion
    start_x = (MAP_DIM - 35) * CELL_SIZE
    start_z = (MAP_DIM - 35) * CELL_SIZE
    end_x = (MAP_DIM - 5) * CELL_SIZE # Leave 5 tiles padding from edge
    end_z = (MAP_DIM - 5) * CELL_SIZE
    
    # Check if position is inside this box (with optional padding)
    return (start_x - padding < pos[0] < end_x + padding) and \
           (start_z - padding < pos[2] < end_z + padding)


def draw_minimap():
    glDisable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Minimap Background
    map_size = 150
    margin = 20
    world_max = MAP_DIM * CELL_SIZE
    
    # Draw Box
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(margin, margin)
    glVertex2f(margin+map_size, margin)
    glVertex2f(margin+map_size, margin+map_size)
    glVertex2f(margin, margin+map_size)
    glEnd()

    # Draw Border
    glColor3f(1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(margin, margin)
    glVertex2f(margin+map_size, margin)
    glVertex2f(margin+map_size, margin+map_size)
    glVertex2f(margin, margin+map_size)
    glEnd()

    # --- CHEAT MODE: DRAW STATIC SOLUTION PATH ---
    if map_visible and solution_path:
        glColor3f(1, 1, 0) # Yellow Line
        glLineWidth(2)
        glBegin(GL_LINE_STRIP)
        for node in solution_path:
            # Convert Grid Coordinates to Minimap Pixels
            mx = margin + (node[0] * CELL_SIZE / world_max) * map_size
            my = margin + (node[1] * CELL_SIZE / world_max) * map_size
            glVertex2f(mx, my)
        glEnd()
        glLineWidth(1)
        
        # Show Ghosts in Cheat Mode
        glColor3f(0, 1, 1) 
        for g in poison_ghosts:
            gx = (g['x'] / world_max) * map_size
            gz = (g['z'] / world_max) * map_size
            glPushMatrix()
            glTranslatef(margin + gx, margin + gz, 0)
            glBegin(GL_QUADS)
            glVertex2f(-2, -2); glVertex2f(2, -2); glVertex2f(2, 2); glVertex2f(-2, 2)
            glEnd()
            glPopMatrix()

    # Draw Player Dot
    px = (player_pos[0] / world_max) * map_size
    py = (player_pos[2] / world_max) * map_size
    
    # Player
    glColor3f(0, 1, 0)
    glPushMatrix()
    glTranslatef(margin + px, margin + py, 0)
    glBegin(GL_TRIANGLE_FAN)
    for i in range(0, 360, 40):
        rad = math.radians(i)
        glVertex2f(math.cos(rad)*3, math.sin(rad)*3)
    glEnd()
    glPopMatrix()
    
    # Draw Boss Icon
    if not boss_defeated:
        bx = (boss_obj['x'] / world_max) * map_size
        bz = (boss_obj['z'] / world_max) * map_size
        glColor3f(1, 0, 0)
        glPushMatrix()
        glTranslatef(margin + bx, margin + bz, 0)
        glBegin(GL_QUADS)
        glVertex2f(-3, -3); glVertex2f(3, -3); glVertex2f(3, 3); glVertex2f(-3, 3)
        glEnd()
        glPopMatrix()

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    glColor3f(1, 0, 0)
    glRasterPos2f(20, WINDOW_HEIGHT - 30)
    for ch in f"HP: {int(player_hp)}": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    
    # Stamina Bar
    bar_x = 100
    bar_y = WINDOW_HEIGHT - 30
    bar_w = 100
    bar_h = 10
    
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_w, bar_y)
    glVertex2f(bar_x + bar_w, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()
    
    if infinite_stamina_timer > 0: glColor3f(0, 1, 1) 
    elif is_exhausted: glColor3f(1, 0, 0) 
    else: glColor3f(1, 1, 0) 
        
    fill_w = (player_stamina / max_stamina) * bar_w
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + fill_w, bar_y)
    glVertex2f(bar_x + fill_w, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(bar_x + 110, bar_y)
    status_msg = "INF STM" if infinite_stamina_timer > 0 else "TIRED" if is_exhausted else "STM"
    for ch in status_msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glColor3f(1, 1, 1)
    glRasterPos2f(20, WINDOW_HEIGHT - 60)
    for ch in f"Daggers: {player_ammo}": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    bag_content = ", ".join([str(item) for item in inventory])
    glRasterPos2f(20, WINDOW_HEIGHT - 90)
    for ch in f"Bag: {bag_content}": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Ghost Count
    glColor3f(0, 1, 1)
    glRasterPos2f(20, WINDOW_HEIGHT - 150)
    for ch in f"Ghosts Captured: {ghosts_captured}/3": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    if immunity_timer > 0:
        glColor3f(0, 1, 0)
        glRasterPos2f(20, WINDOW_HEIGHT - 120)
        msg = f"IMMUNITY: {int(immunity_timer/60)}s"
        for ch in msg: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
    if has_green_gem:
        glColor3f(0, 1, 0)
        glRasterPos2f(20, WINDOW_HEIGHT - 180)
        for ch in "GEM ACQUIRED! GATE OPEN!": glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    if game_over:
        glColor3f(1, 0, 0)
        glRasterPos2f(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2)
        for ch in "GAME OVER": glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))
        
    if level_complete:
        glColor3f(0, 1, 0)
        glRasterPos2f(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2)
        for ch in "LEVEL COMPLETE!": glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(ch))

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# ==========================================
# 3. Logic & Physics
# ==========================================
def in_boss_arena(pos, padding=0):
    bx = (MAP_DIM - 20) * CELL_SIZE
    bz = (MAP_DIM - 20) * CELL_SIZE
    half_size = 15 * CELL_SIZE + padding
    return (bx - half_size < pos[0] < bx + half_size) and (bz - half_size < pos[2] < bz + half_size)

def close_boss_gate():
    global display_list
    # Match the gate position from generate_level_1
    b_x = MAP_DIM - 35
    b_y = MAP_DIM - 35
    gate_x = b_x - 1
    mid_y = b_y + 15
    
    # Seal the gate
    for k in range(-4, 5):
        if 0 <= gate_x < MAP_DIM and 0 <= mid_y + k < MAP_DIM:
             map_data[gate_x][mid_y + k] = C_WALL
                    
    if display_list:
        glDeleteLists(display_list, 1)
        display_list = None
        create_display_list()

def check_sprint():
    global is_sprinting
    if glutGetModifiers() & GLUT_ACTIVE_SHIFT:
        is_sprinting = True
    else:
        is_sprinting = False

def update_physics():
    global player_pos, player_angle, global_time, acid_level, player_hp, max_player_hp, game_over, level_complete
    global enemies, animals, gas_clouds, daggers, loot, immunity_timer, player_ammo, inventory, particles
    global player_stamina, is_exhausted, infinite_stamina_timer, is_sprinting, player_speed
    global boss_active, boss_defeated, boss_obj, rain_active, rain_duration, rain_drops, has_green_gem, boss_speed, poison_ghosts
    
    if game_over or level_complete: return

    global_time += 0.05
    acid_level = math.sin(global_time) * 3 
    if immunity_timer > 0: immunity_timer -= 1
    if infinite_stamina_timer > 0: infinite_stamina_timer -= 1

    # Boss Trigger
    if not boss_active and not boss_defeated:
        if in_boss_arena(player_pos):
            boss_active = True
            close_boss_gate()

    # --- BOSS LOGIC ---
    if boss_active:
        boss_obj['timer'] += 1
        
        # [Requirement] Boss strictly inside arena
        # Define Arena Bounds (World Coords)
        arena_min_x = (MAP_DIM - 35) * CELL_SIZE + CELL_SIZE
        arena_max_x = (MAP_DIM - 5) * CELL_SIZE - CELL_SIZE
        arena_min_z = (MAP_DIM - 35) * CELL_SIZE + CELL_SIZE
        arena_max_z = (MAP_DIM - 5) * CELL_SIZE - CELL_SIZE

        dx = boss_obj['x'] - player_pos[0]
        dz = boss_obj['z'] - player_pos[2]
        dist = math.sqrt(dx*dx + dz*dz)
        
        # [Requirement] Boss Teleport Logic
        # Condition: Player too close OR random cornered check
        if dist < 300 and boss_obj['teleport_cd'] <= 0:
             # Find a spot FAR from player, INSIDE ARENA
             best_tx, best_tz = boss_obj['x'], boss_obj['z']
             max_d = -1
             
             # Try 10 random spots in arena, pick furthest from player
             for _ in range(10):
                 rx = random.uniform(arena_min_x, arena_max_x)
                 rz = random.uniform(arena_min_z, arena_max_z)
                 
                 d_p = math.sqrt((rx - player_pos[0])**2 + (rz - player_pos[2])**2)
                 if d_p > max_d:
                     max_d = d_p
                     best_tx, best_tz = rx, rz
             
             boss_obj['x'] = best_tx
             boss_obj['z'] = best_tz
             boss_obj['teleport_cd'] = 200 # 3-4 seconds cooldown
                  
        if boss_obj['teleport_cd'] > 0: boss_obj['teleport_cd'] -= 1

        if boss_obj['timer'] % 800 == 0: 
            rain_active = True
            rain_duration = 300
            boss_obj['rain_center_x'] = player_pos[0]
            boss_obj['rain_center_z'] = player_pos[2]
            
        current_slimes = 0
        for e in enemies:
             if in_boss_arena([e['x'], 0, e['z']], 0): current_slimes += 1
        
        current_gas = 0
        for g in gas_clouds:
             if in_boss_arena([g['x'], 0, g['z']], 0): current_gas += 1
             
        # 2. INSTANTLY Replenish
        while current_slimes < 20:
             # Spawn Slime at Boss
             enemies.append({'x': boss_obj['x'], 'z': boss_obj['z'], 'home_x': boss_obj['x'], 'home_z': boss_obj['z']})
             current_slimes += 1

        if current_slimes > 20:
            kept = []
            kept_slimes_in_arena = 0
            for e in enemies:
                if in_boss_arena([e['x'], 0, e['z']], 0):
                    if kept_slimes_in_arena < 20:
                        kept.append(e)
                        kept_slimes_in_arena += 1
                else:
                    kept.append(e)
            enemies = kept
             
        while current_gas < 20:
             # Spawn Gas at Boss, Random Direction
             angle = random.uniform(0, 6.28)
             g_speed = 0.5
             gas_clouds.append({
                 'x': boss_obj['x'], 'z': boss_obj['z'], 
                 'y_base': 40, 'life': 1200, 
                 'dx': math.sin(angle)*g_speed, 'dz': math.cos(angle)*g_speed, 
                 'type': 'BOSS',
                 'home_x': boss_obj['x'], 'home_z': boss_obj['z'] 
             })
             current_gas += 1

    if rain_active:
        rain_duration -= 1
        if rain_duration <= 0: rain_active = False
        
        # [Requirement] Acid Rain (Increased area)
        # Using 600 units radius (20 tiles)
        if immunity_timer <= 0:
            dist_to_rain = math.sqrt((player_pos[0] - boss_obj.get('rain_center_x', 0))**2 + (player_pos[2] - boss_obj.get('rain_center_z', 0))**2)
            if dist_to_rain < 700:
                 player_hp -= 0.5
                 
        for _ in range(8):
             # Visuals concentrated in the area
             rcx = boss_obj.get('rain_center_x', player_pos[0])
             rcz = boss_obj.get('rain_center_z', player_pos[2])
             rain_drops.append({'x': rcx+random.randint(-600,600), 'y': 200, 'z': rcz+random.randint(-600,600)})
        new_rain = []
        for r in rain_drops:
            r['y'] -= 5
            if r['y'] > 0: new_rain.append(r)
        rain_drops = new_rain
        
    # [Requirement] Exit Gate appears after boss defeat
    if boss_defeated:
         ex_x = (MAP_DIM - 25) * CELL_SIZE
         ex_z = (MAP_DIM - 35) * CELL_SIZE
         dist_exit = math.sqrt((player_pos[0] - ex_x)**2 + (player_pos[2] - ex_z)**2)
         
         if dist_exit < 50:
             if "Poison Gem Stone" in inventory:
                 level_complete = True
                 print("LEVEL COMPLETE! ENTERING NEXT LEVEL...")

    # Movement
    move_speed = 0; strafe = 0
    is_moving = key_states.get(b'w') or key_states.get(b's') or key_states.get(b'a') or key_states.get(b'd')
    
    if infinite_stamina_timer > 0:
        player_speed = base_speed * 2.0 if is_sprinting else base_speed
        player_stamina = 100; is_exhausted = False
    else:
        if is_sprinting and is_moving and not is_exhausted:
            player_speed = base_speed * 2.0
            player_stamina -= 0.16 
            if player_stamina <= 0: player_stamina = 0; is_exhausted = True
        elif is_exhausted:
            player_speed = base_speed * 0.5
            player_stamina += 0.05
            if player_stamina >= 30: is_exhausted = False
        else:
            player_speed = base_speed
            if not is_sprinting: player_stamina = min(100, player_stamina + 0.1)

    if key_states.get(b'w'): move_speed = player_speed
    if key_states.get(b's'): move_speed = -player_speed
    if key_states.get(b'a'): strafe = -player_speed
    if key_states.get(b'd'): strafe = player_speed
    
    if key_states.get(GLUT_KEY_LEFT): player_angle -= 0.04
    if key_states.get(GLUT_KEY_RIGHT): player_angle += 0.04
    
    dx = math.sin(player_angle) * move_speed
    dz = -math.cos(player_angle) * move_speed
    sdx = math.sin(player_angle + 1.57) * strafe
    sdz = -math.cos(player_angle + 1.57) * strafe
    
    final_dx = dx + sdx
    final_dz = dz + sdz
    
    # Inside update_physics -> check_col function:
    
    def check_col(tx, tz):
        radius = 5
        for cx in [tx-radius, tx+radius]:
            for cz in [tz-radius, tz+radius]:
                 gx = int(cx // CELL_SIZE)
                 gz = int(cz // CELL_SIZE)
                 if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM:
                     cell = map_data[gx][gz]
                     if cell == C_WALL: return True
                     
                     # GATE LOGIC:
                     # If ghosts < 3: Solid Wall.
                     # If ghosts >= 3: Walkable (Pass through)
                     if cell == C_GATE and ghosts_captured < 3: return True
                     
        return False

    if not check_col(player_pos[0] + final_dx, player_pos[2]):
        player_pos[0] += final_dx
    
    if not check_col(player_pos[0], player_pos[2] + final_dz):
        player_pos[2] += final_dz
        
    gx_curr = int(player_pos[0] // CELL_SIZE)
    gz_curr = int(player_pos[2] // CELL_SIZE)
    if map_data[gx_curr][gz_curr] == C_ACID and immunity_timer <= 0:
            player_hp -= 0.05

    # --- Poison Ghosts AI (Smart Slide + Corner Escape) ---
    p_dx = math.sin(player_angle)
    p_dz = -math.cos(player_angle)

    for g in poison_ghosts:
        # 1. Handle Stun
        if g.get('stun_timer', 0) > 0:
            g['stun_timer'] -= 1
            continue

        # 2. State Logic
        dx = g['x'] - player_pos[0]
        dz = g['z'] - player_pos[2]
        dist = math.sqrt(dx*dx + dz*dz)
        
        dot = (p_dx * (dx/dist if dist>0 else 0)) + (p_dz * (dz/dist if dist>0 else 0))
        
        # Check Vision & Distance
        if dist < 400 and dot < -0.5: # In front of player
             g['state'] = 'FLEE'
        elif dist > 1000:
             g['state'] = 'ROAM'
        
        # Default State if undefined
        if 'state' not in g: g['state'] = 'ROAM'

        move_x = 0; move_y = 0
        speed = base_speed * 1.3 # Slightly faster than base to be threatening

        if g['state'] == 'FLEE':
            if dist > 0:
                # Vector AWAY from player
                move_x = (dx / dist) * speed
                move_y = (dz / dist) * speed
        else:
            # Roam
            if random.random() < 0.05: 
                g['rx'] = random.uniform(-1, 1)
                g['ry'] = random.uniform(-1, 1)
            move_x = g.get('rx', 0) * (speed * 0.4)
            move_y = g.get('ry', 0) * (speed * 0.4)

        # --- PHYSICS & SLIDING ---
        # Proposed new positions
        next_x = g['x'] + move_x
        next_z = g['z'] + move_y
        
        # Grid Coordinates
        curr_gx = int(g['x'] // CELL_SIZE)
        curr_gz = int(g['z'] // CELL_SIZE)
        next_gx = int(next_x // CELL_SIZE)
        next_gz = int(next_z // CELL_SIZE)
        
        can_move_x = True
        can_move_z = True

        # Check X-Axis Wall
        if 0 <= next_gx < MAP_DIM and 0 <= curr_gz < MAP_DIM:
            if map_data[next_gx][curr_gz] == C_WALL or in_boss_arena([next_x, 0, g['z']], padding=20):
                can_move_x = False

        # Check Z-Axis Wall
        if 0 <= curr_gx < MAP_DIM and 0 <= next_gz < MAP_DIM:
            if map_data[curr_gx][next_gz] == C_WALL or in_boss_arena([g['x'], 0, next_z], padding=20):
                can_move_z = False

        # Apply Movement
        if can_move_x: 
            g['x'] = next_x
        
        if can_move_z: 
            g['z'] = next_z

        # --- CORNER ESCAPE MECHANIC ---
        # If stuck on BOTH axes (Cornered) and trying to move
        if not can_move_x and not can_move_z and (abs(move_x) > 0.1 or abs(move_y) > 0.1):
            # Force move towards the center of the current cell to unstuck
            # Then pick a random perpendicular direction to slide out
            center_x = (curr_gx * CELL_SIZE) + (CELL_SIZE / 2)
            center_z = (curr_gz * CELL_SIZE) + (CELL_SIZE / 2)
            
            # Nudge towards center
            g['x'] += (center_x - g['x']) * 0.2
            g['z'] += (center_z - g['z']) * 0.2
            
            # Jitter slightly to find a new sliding angle next frame
            g['x'] += random.uniform(-1, 1)
            g['z'] += random.uniform(-1, 1)
            
        # Hard Map Bounds
        g['x'] = max(CELL_SIZE, min(g['x'], (MAP_DIM-1)*CELL_SIZE))
        g['z'] = max(CELL_SIZE, min(g['z'], (MAP_DIM-1)*CELL_SIZE))

    # Gas
    active_gas = []
    for g in gas_clouds:
        g['x'] += g['dx']; g['z'] += g['dz']
        if g.get('type') == 'BOSS':
             g['life'] -= 1
             # Bounce off Arena Walls
             arena_min_x = (MAP_DIM - 35) * CELL_SIZE + CELL_SIZE
             arena_max_x = (MAP_DIM - 5) * CELL_SIZE - CELL_SIZE
             arena_min_z = (MAP_DIM - 35) * CELL_SIZE + CELL_SIZE
             arena_max_z = (MAP_DIM - 5) * CELL_SIZE - CELL_SIZE
             
             if g['x'] < arena_min_x or g['x'] > arena_max_x: g['dx'] *= -1
             if g['z'] < arena_min_z or g['z'] > arena_max_z: g['dz'] *= -1
             
             if g['life'] <= 0: continue
        else:
             if math.sqrt((g['x']-g['home_x'])**2 + (g['z']-g['home_z'])**2) > 50: g['dx']*=-1; g['dz']*=-1
        
        if math.sqrt((player_pos[0]-g['x'])**2 + (player_pos[2]-g['z'])**2) < 20 and immunity_timer <= 0: player_hp -= 0.3
        else: active_gas.append(g)
    gas_clouds = active_gas

    # Enemies
    new_enemies = []
    for e in enemies:
        dist = math.sqrt((player_pos[0]-e['x'])**2 + (player_pos[2]-e['z'])**2)
        if dist < 15: player_hp -= 0.5; continue
        
        in_arena = in_boss_arena([e['x'], 0, e['z']], 0)
        
        should_chase = False
        if in_arena:
            should_chase = True
        elif dist < 200:
            should_chase = True
            
        if should_chase:
             chase_allowed = True
             if not in_arena:
                 if math.sqrt((e['x']-e['home_x'])**2 + (e['z']-e['home_z'])**2) >= 300: chase_allowed = False
             
             if chase_allowed and dist > 0:
                 ex = (player_pos[0]-e['x'])/dist; ez = (player_pos[2]-e['z'])/dist
                 e['x'] += ex * enemy_speed; e['z'] += ez * enemy_speed
        new_enemies.append(e)
    enemies = new_enemies

    # Animals
    for a in animals:
        if a['active']:
            dist = math.sqrt((player_pos[0]-a['x'])**2 + (player_pos[2]-a['z'])**2)
            if dist < 120:
                ex = (a['x'] - player_pos[0]) / dist
                ez = (a['z'] - player_pos[2]) / dist
                a['angle'] = math.atan2(ex, ez)
                nx = a['x'] + ex * animal_speed; nz = a['z'] + ez * animal_speed
                gx = int(round(nx / CELL_SIZE)); gz = int(round(nz / CELL_SIZE))
                if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM and map_data[gx][gz] not in [C_WALL, C_GATE]:
                    a['x'] = nx; a['z'] = nz
                else:
                    a['x'] += random.choice([-1, 1]); a['z'] += random.choice([-1, 1])
        else:
            if math.sqrt((player_pos[0]-a['home_x'])**2 + (player_pos[2]-a['home_z'])**2) > 250:
                a['active'] = True; a['x'] = a['home_x']; a['z'] = a['home_z']

    # Daggers
    kept_daggers = []
    for d in daggers:
        d['x'] += math.sin(d['angle']) * dagger_speed
        d['z'] -= math.cos(d['angle']) * dagger_speed
        d['y'] -= 0.1; d['life'] -= 1
        hit = False
        gx = int(round(d['x'] / CELL_SIZE)); gz = int(round(d['z'] / CELL_SIZE))
        if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM and map_data[gx][gz] in [C_WALL, C_GATE]: hit = True
        
        if not hit:
            # 1. Check Boss Collision
            if boss_active:
                if math.sqrt((d['x']-boss_obj['x'])**2 + (d['z']-boss_obj['z'])**2) < 25:
                    hit = True
                    boss_obj['hp'] -= 50
                    boss_obj['teleport_cd'] = max(0, boss_obj['teleport_cd'] - 50)
                    
                    # Move Away / Evade Logic...
                    vx = boss_obj['x'] - player_pos[0]; vz = boss_obj['z'] - player_pos[2]
                    v_len = math.sqrt(vx*vx + vz*vz)
                    if v_len > 0: vx /= v_len; vz /= v_len
                    move_dist = 40
                    side = 1 if random.random() < 0.5 else -1
                    sx = -vz * side * 30; sz = vx * side * 30
                    target_x = boss_obj['x'] + (vx * move_dist) + sx
                    target_z = boss_obj['z'] + (vz * move_dist) + sz
                    
                    arena_min_x = (MAP_DIM - 35) * CELL_SIZE + 20; arena_max_x = (MAP_DIM - 5) * CELL_SIZE - 20
                    arena_min_z = (MAP_DIM - 35) * CELL_SIZE + 20; arena_max_z = (MAP_DIM - 5) * CELL_SIZE - 20
                    boss_obj['x'] = max(arena_min_x, min(target_x, arena_max_x))
                    boss_obj['z'] = max(arena_min_z, min(target_z, arena_max_z))
                    
                    if boss_obj['hp'] <= 0:
                        boss_active = False; boss_defeated = True; rain_active = False
                        loot.append({'x': boss_obj['x'], 'z': boss_obj['z'], 'type': 'POISON_GEM'})
                        max_stamina = 120; player_stamina = 120; max_player_hp = 120; player_hp = 120

            # 2. Check Enemy Collision (ONLY if Boss wasn't hit)
            if not hit:
                remaining = []
                for e in enemies:
                    if math.sqrt((d['x']-e['x'])**2 + (d['z']-e['z'])**2) < 20:
                        hit = True
                        if not in_boss_arena([e['x'], 0, e['z']], 0):
                            r = random.random()
                            if r < 0.05: loot.append({'x': e['x'], 'z': e['z'], 'type': 'IMMUNITY'})
                            elif r < 0.15: loot.append({'x': e['x'], 'z': e['z'], 'type': 'STAMINA'})
                            elif r < 0.20: loot.append({'x': e['x'], 'z': e['z'], 'type': 'BOTTLE'})
                            elif r < 0.70: loot.append({'x': e['x'], 'z': e['z'], 'type': 'AMMO'})
                            elif r < 0.90: loot.append({'x': e['x'], 'z': e['z'], 'type': 'HP'})

                        if boss_active and in_boss_arena([e['x'], 0, e['z']], 0):
                            for _ in range(random.randint(2, 3)):
                                remaining.append({
                                    'x': boss_obj['x'], 
                                    'z': boss_obj['z'], 
                                    'home_x': boss_obj['x'], 
                                    'home_z': boss_obj['z']
                                })

                    else: remaining.append(e)
                enemies = remaining

        # ... (Ghost and Animal logic follows, make sure they are also guarded by `if not hit:`) ...
        
        # Check Ghost Hit (Stun Effect)
        if not hit:
            for g in poison_ghosts:
                 dist = math.sqrt((d['x']-g['x'])**2 + (d['z']-g['z'])**2)
                 if dist < 25:
                     hit = True
                     g['stun_timer'] = 180 # 3 Seconds Stun
                     print("GHOST STUNNED! CATCH IT NOW!")
                     break

        if not hit:
            for a in animals:
                if a['active'] and math.sqrt((d['x']-a['x'])**2 + (d['z']-a['z'])**2) < 15:
                    hit = True; a['active'] = False
                    r = random.random()
                    if r < 0.4: loot.append({'x': a['x'], 'z': a['z'], 'type': 'BOTTLE'})
                    elif r < 0.7: loot.append({'x': a['x'], 'z': a['z'], 'type': 'HP'})

        if not hit and d['life'] > 0 and d['y'] > 0: kept_daggers.append(d)
    daggers = kept_daggers


    # Loot
    kept_loot = []
    for l in loot:
        if math.sqrt((player_pos[0]-l['x'])**2 + (player_pos[2]-l['z'])**2) < 20:
            if l['type'] == 'HP': 
                if player_hp >= max_player_hp: inventory.append("HP Pill")
                else: player_hp = min(max_player_hp, player_hp + 30)
            elif l['type'] == 'AMMO': player_ammo += 40
            elif l['type'] == 'IMMUNITY': inventory.append("Immunity")
            elif l['type'] == 'STAMINA': inventory.append("Stamina Pill")
            elif l['type'] == 'BOTTLE': inventory.append("Capture Bottle")
            elif l['type'] == 'GEM': has_green_gem = True; inventory.append("Green Gem")
            elif l['type'] == 'POISON_GEM': inventory.append("Poison Gem Stone")
        else: kept_loot.append(l)
    loot = kept_loot

    if player_hp <= 0: game_over = True

def setup_camera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60, WINDOW_WIDTH/WINDOW_HEIGHT, 1, 2000)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    lx = player_pos[0] + math.sin(player_angle) * 100
    lz = player_pos[2] - math.cos(player_angle) * 100
    gluLookAt(player_pos[0], 25, player_pos[2], lx, 25, lz, 0, 1, 0)

# ==========================================
# Standard Callbacks
# ==========================================
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setup_camera()
    if display_list is None: create_display_list()
    glCallList(display_list)
    draw_entities()
    if map_visible: draw_minimap() 
    draw_hud()
    
    # [Requirement] Draw Exit Gate when Boss Defeated
    if boss_defeated:
        ex_x = (MAP_DIM - 25) * CELL_SIZE
        ex_z = (MAP_DIM - 35) * CELL_SIZE
        glPushMatrix()
        glTranslatef(ex_x, 0, ex_z)
        glColor3f(0, 0, 1) # Blue Gate
        glScalef(1, 3, 1)
        glutSolidCube(30)
        glPopMatrix()
        
    glutSwapBuffers()

def idle(): update_physics(); glutPostRedisplay()

def keyDown(key, x, y):
    global player_ammo, immunity_timer, player_hp, infinite_stamina_timer, ghosts_captured, poison_ghosts, inventory, map_visible
    check_sprint()
    key_states[key] = True; key_states[key.lower()] = True
    if key == b'r': generate_level_1()
    
    # Phase 1.4: Capture Ghost (Proximity Only)
    if key == b'4':
         if "Capture Bottle" in inventory and ghosts_captured < 3:
             captured = False

             for g in poison_ghosts:
                 dist = math.sqrt((g['x']-player_pos[0])**2 + (g['z']-player_pos[2])**2)
                 
                 # Logic: Must be Stunned AND Close
                 if g.get('stun_timer', 0) > 0 and dist < 80:
                     inventory.remove("Capture Bottle")
                     poison_ghosts.remove(g)
                     ghosts_captured += 1
                     captured = True
                     print(f"Ghost Captured! Total: {ghosts_captured}/3")
                     break
             
             if not captured:
                 print("Missed! Stun first or get closer.")
         else:
             print("No Bottles or Already Full!")
        
    if key == b'c': map_visible = not map_visible
    if key == b'1' and "Immunity" in inventory: inventory.remove("Immunity"); immunity_timer = 3600
    if key == b'2' and "HP Pill" in inventory and player_hp < 100: inventory.remove("HP Pill"); player_hp = min(100, player_hp+20)
    if key == b'3' and "Stamina Pill" in inventory: inventory.remove("Stamina Pill"); infinite_stamina_timer = 1800

def keyUp(key, x, y): check_sprint(); key_states[key] = False; key_states[key.lower()] = False
def specialDown(key, x, y): check_sprint(); key_states[key] = True
def specialUp(key, x, y): check_sprint(); key_states[key] = False

def mouseListener(button, state, x, y):
    global player_ammo
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        if player_ammo > 0:
            player_ammo -= 1
            daggers.append({'x': player_pos[0], 'y': 20, 'z': player_pos[2], 'angle': player_angle, 'life': 35})

def init_fog():
    glEnable(GL_FOG); glFogfv(GL_FOG_COLOR, (0.05, 0.15, 0.05, 1.0))
    glFogi(GL_FOG_MODE, GL_LINEAR); glFogf(GL_FOG_START, 100.0); glFogf(GL_FOG_END, 1200.0)
    glClearColor(0.05, 0.15, 0.05, 1.0)

def main():
    glutInit(); glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"level 1: The Cursed Labyrinth")
    glEnable(GL_DEPTH_TEST); init_fog(); generate_level_1()
    glutDisplayFunc(showScreen); glutIdleFunc(idle)
    glutKeyboardFunc(keyDown); glutKeyboardUpFunc(keyUp)
    glutSpecialFunc(specialDown); glutSpecialUpFunc(specialUp)
    glutMouseFunc(mouseListener); glutMainLoop()

if __name__ == "__main__": main()   










##level2
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random


WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

MAP_DIM = 100
CELL_SIZE = 20
WALL_HEIGHT = 50

C_EMPTY = 0
C_WALL = 1
C_SPIKE_HIDDEN = 2
C_BOSS_ARENA = 4
C_EXIT = 5

map_data = []


birds = []
moving_enemies = []
projectiles = []
player_bullets = []
drops = []
respawning_spikes = []


player_pos = [0, 20, 0]
player_angle = 1.57
player_pitch = 0.0

base_speed = 5       
rotation_speed = 0.03   

key_states = {}
shift_held = False 

player_hp = 3000000000.0
player_stamina = 100.0
player_ammo = 50
player_bombs = 2
diamonds_collected = 0
diamonds_needed = 10

game_over = False
level_complete = False
boss_stage = 0
boss_arena_unlocked = False
boss_gate_closed = False
global_time = 0.0

boss = {
    'x': 0, 'z': 0,
    'hp': 10,
    'active': False,
    'dead': False,
    'stage': 1,
    'shoot_timer': 0
}

fovY = 60


def draw_text_2d(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def check_collision(x1, z1, r1, x2, z2, r2):
    return (x1-x2)**2 + (z1-z2)**2 < (r1+r2)**2

def is_walkable(x, z):
    mx = int(x / CELL_SIZE)
    mz = int(z / CELL_SIZE)
    if 0 <= mx < MAP_DIM and 0 <= mz < MAP_DIM:
        cell = map_data[mx][mz]
        if cell == C_WALL: return False
        if cell == C_BOSS_ARENA and not boss_arena_unlocked: return False
        return True
    return False


def generate_level():
    global map_data, player_pos, birds, moving_enemies, boss, drops, respawning_spikes
    global player_hp, player_stamina, player_ammo, player_bombs, diamonds_collected, game_over
    global boss_stage, boss_arena_unlocked, boss_gate_closed, level_complete, projectiles, player_bullets
    global player_angle, global_time

    map_data = [[C_WALL for _ in range(MAP_DIM)] for _ in range(MAP_DIM)]
    birds = []
    moving_enemies = []
    projectiles = []
    player_bullets = []
    drops = []
    respawning_spikes = []
    
    player_hp = 300000.0
    player_stamina = 100.0
    player_ammo = 50000
    player_bombs = 2
    diamonds_collected = 0
    player_angle = 1.57
    global_time = 0.0
    
    game_over = False
    level_complete = False
    boss_stage = 0
    boss_arena_unlocked = False
    boss_gate_closed = False

    start_x, start_y = 5, 5
    boss_x, boss_y = MAP_DIM - 10, MAP_DIM - 10


    for i in range(start_x-2, start_x+3):
        for j in range(start_y-2, start_y+3):
            if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM: map_data[i][j] = C_EMPTY

    cx, cy = start_x, start_y
    while (abs(cx - boss_x) > 1 or abs(cy - boss_y) > 1):
        for ox in [-1, 0, 1]:
            for oy in [-1, 0, 1]:
                if 0 <= cx+ox < MAP_DIM and 0 <= cy+oy < MAP_DIM:
                    map_data[cx+ox][cy+oy] = C_EMPTY
        if random.random() < 0.5:
            if cx < boss_x: cx += 1
            elif cx > boss_x: cx -= 1
        else:
            if cy < boss_y: cy += 1
            elif cy > boss_y: cy -= 1

   
    for _ in range(40):
        rx, ry = random.randint(5, MAP_DIM-5), random.randint(5, MAP_DIM-5)
        life = 100
        while life > 0:
            if 0 < rx < MAP_DIM-1 and 0 < ry < MAP_DIM-1: map_data[rx][ry] = C_EMPTY
            move = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            rx += move[0]; ry += move[1]
            rx = max(2, min(MAP_DIM-3, rx)); ry = max(2, min(MAP_DIM-3, ry))
            life -= 1

   
    for i in range(boss_x-8, boss_x+9):
        for j in range(boss_y-8, boss_y+9):
            if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM: map_data[i][j] = C_BOSS_ARENA
    map_data[boss_x][boss_y+8] = C_EXIT

    
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EMPTY:
                dist = math.sqrt((x-start_x)**2 + (z-start_y)**2)
                if dist < 20: continue
                
                wx, wz = x * CELL_SIZE, z * CELL_SIZE
                r = random.random()
                is_black_tile = (x + z) % 2 != 0

                if is_black_tile and r < 0.20:
                    map_data[x][z] = C_SPIKE_HIDDEN
                elif r < 0.05: 
                    moving_enemies.append({'x': wx, 'z': wz, 'hp': 3, 'shoot_timer': 0})
                elif r < 0.12:
                    birds.append({
                        'x': wx, 'y': 35, 'z': wz, 
                        'cx': wx, 'cz': wz,
                        'angle': random.random()*6.28, 
                        'radius': random.randint(20, 60),
                        'speed': random.choice([0.02, -0.02]),
                        'drop_timer': random.randint(500, 1000)
                    })

    boss['x'] = boss_x * CELL_SIZE
    boss['z'] = boss_y * CELL_SIZE
    boss['hp'] = 15
    boss['active'] = False
    boss['dead'] = False
    boss['stage'] = 1
    
    player_pos = [start_x * CELL_SIZE, 20, start_y * CELL_SIZE]


def update_logic():
    global player_hp, player_stamina, player_pos, player_ammo, player_bombs, diamonds_collected, global_time
    global game_over, level_complete, boss_arena_unlocked, boss_gate_closed, boss_stage
    global player_angle, player_pitch
    global projectiles, player_bullets, moving_enemies, drops, respawning_spikes
    
    glutPostRedisplay()
    if game_over or level_complete: return
    global_time += 0.02

    is_trying_to_sprint = shift_held
    
    dx, dz = 0, 0
    if key_states.get(b'w'): 
        dx += math.cos(player_angle); dz += math.sin(player_angle)
    if key_states.get(b's'): 
        dx -= math.cos(player_angle); dz -= math.sin(player_angle)
    if key_states.get(b'a'): 
        dx += math.sin(player_angle); dz -= math.cos(player_angle)
    if key_states.get(b'd'): 
        dx -= math.sin(player_angle); dz += math.cos(player_angle)

    is_moving = (dx != 0 or dz != 0)
    speed = base_speed

    if is_moving and is_trying_to_sprint and player_stamina > 0:
        speed *= 2.5
        player_stamina = max(0.0, player_stamina - 1.5)
    else:
        player_stamina = min(100.0, player_stamina + 0.5)

    dx *= speed
    dz *= speed

    if key_states.get(GLUT_KEY_LEFT): player_angle -= rotation_speed
    if key_states.get(GLUT_KEY_RIGHT): player_angle += rotation_speed
    
    
    
    new_x = player_pos[0] + dx
    if is_walkable(new_x, player_pos[2]): player_pos[0] = new_x
        
    new_z = player_pos[2] + dz
    if is_walkable(player_pos[0], new_z): player_pos[2] = new_z

    curr_cell_x = int(player_pos[0] / CELL_SIZE)
    curr_cell_z = int(player_pos[2] / CELL_SIZE)
    if 0 <= curr_cell_x < MAP_DIM and 0 <= curr_cell_z < MAP_DIM:
        if map_data[curr_cell_x][curr_cell_z] == C_BOSS_ARENA:
             if boss_arena_unlocked and not boss_gate_closed:
                 boss_gate_closed = True; boss['active'] = True
        
        if map_data[curr_cell_x][curr_cell_z] == C_SPIKE_HIDDEN:
             h = -15 + (math.sin(global_time * 2) + 1) * 15 
             if h > 2: player_hp -= 1.0

    if diamonds_collected >= diamonds_needed: boss_arena_unlocked = True

    active_respawns = []
    for s in respawning_spikes:
        s['timer'] -= 1
        if s['timer'] <= 0:
            if map_data[s['x']][s['z']] == C_EMPTY:
                map_data[s['x']][s['z']] = C_SPIKE_HIDDEN
        else:
            active_respawns.append(s)
    respawning_spikes = active_respawns

    for e in moving_enemies:
        dist = math.sqrt((e['x']-player_pos[0])**2 + (e['z']-player_pos[2])**2)
        if dist < 150:
            ang = math.atan2(player_pos[2]-e['z'], player_pos[0]-e['x'])
            vx = math.cos(ang) * 0.8
            vz = math.sin(ang) * 0.8
            
            nx = e['x'] - vx
            if is_walkable(nx + 5, e['z']) and is_walkable(nx - 5, e['z']):
                 e['x'] = nx
            
            nz = e['z'] - vz
            if is_walkable(e['x'], nz + 5) and is_walkable(e['x'], nz - 5):
                 e['z'] = nz
        
        e['shoot_timer'] += 1
        if e['shoot_timer'] > 80 and dist < 400:
            e['shoot_timer'] = 0
            ang = math.atan2(player_pos[2]-e['z'], player_pos[0]-e['x'])
            projectiles.append({'x': e['x'], 'z': e['z'], 'vx': math.cos(ang)*3, 'vz': math.sin(ang)*3, 'type': 'enemy', 'life': 100})

    for b in birds:
        b['angle'] += b['speed']
        b['x'] = b['cx'] + math.cos(b['angle']) * b['radius']
        b['z'] = b['cz'] + math.sin(b['angle']) * b['radius']
        
        b['drop_timer'] -= 1
        if b['drop_timer'] <= 0:
            b['drop_timer'] = random.randint(500, 1000) 
            
            if random.random() < 0.5:
                if random.random() < 0.4:
                    drops.append({'x': b['x'], 'z': b['z'], 'y': 35, 'type': 'AMMO'})
                else:
                    drops.append({'x': b['x'], 'z': b['z'], 'y': 35, 'type': 'EGG'})

    active_bullets = []
    for p in player_bullets:
        p['x'] += p['vx']; p['z'] += p['vz']; p['life'] -= 1
        if p['life'] <= 0: continue
        
        hit = False
        for e in moving_enemies[:]:
            if check_collision(p['x'], p['z'], 12, e['x'], e['z'], 10):
                e['hp'] -= 1; hit = True
                if e['hp'] <= 0:
                    moving_enemies.remove(e)
                    loot = 'BOMB' if random.random() < 0.5 else 'SMALL_HP'
                    drops.append({'x': e['x'], 'z': e['z'], 'y': 5, 'type': loot})
                break
        
        if hit: continue


        mx, mz = int(p['x']/CELL_SIZE), int(p['z']/CELL_SIZE)
        
        
        offsets = [(0,0), (1,0), (-1,0), (0,1), (0,-1)]
        
        spike_hit = False
        for ox, oz in offsets:
            tx, tz = mx + ox, mz + oz
            if 0 <= tx < MAP_DIM and 0 <= tz < MAP_DIM:
                 if map_data[tx][tz] == C_SPIKE_HIDDEN:
                     
                     cx, cz = tx * CELL_SIZE, tz * CELL_SIZE
                     if check_collision(p['x'], p['z'], 10, cx, cz, 15): 
                         map_data[tx][tz] = C_EMPTY
                         respawning_spikes.append({'x': tx, 'z': tz, 'timer': 600})
                         hit = True
                         spike_hit = True
                         
                         
                         r = random.random()
                         if r < 0.30: 
                             drops.append({'x': tx*CELL_SIZE, 'z': tz*CELL_SIZE, 'y': 5, 'type': 'DIAMOND'})
                         elif r < 0.60: 
                             drops.append({'x': tx*CELL_SIZE, 'z': tz*CELL_SIZE, 'y': 5, 'type': 'AMMO'})
                         
                         break
                 
                 elif map_data[tx][tz] == C_WALL:
                    
                     cx, cz = tx * CELL_SIZE, tz * CELL_SIZE
                     if check_collision(p['x'], p['z'], 2, cx, cz, 10):
                        hit = True
                        break
        
        if hit: continue

        if boss['active'] and not boss['dead']:
            if check_collision(p['x'], p['z'], 5, boss['x'], boss['z'], 20):
                 boss['hp'] -= 1; hit = True
                 if boss['hp'] <= 0:
                     if boss['stage'] == 1: boss['stage'] = 2; boss['hp'] = 10
                     elif boss['stage'] == 2:
                         boss['active'] = False; boss['dead'] = True
                         map_data[int(boss['x']/CELL_SIZE)][int(boss['z']/CELL_SIZE)] = C_EXIT
        
        if not hit: active_bullets.append(p)
    player_bullets = active_bullets

    active_projectiles = []
    for p in projectiles:
        p['x'] += p['vx']; p['z'] += p['vz']; p['life'] -= 1
        if p['life'] <= 0: continue
        
        mx, mz = int(p['x']/CELL_SIZE), int(p['z']/CELL_SIZE)
        if 0 <= mx < MAP_DIM and 0 <= mz < MAP_DIM:
            if map_data[mx][mz] == C_WALL:
                continue 

        if check_collision(p['x'], p['z'], 5, player_pos[0], player_pos[2], 10):
            player_hp -= 5; continue
        
        active_projectiles.append(p)
    projectiles = active_projectiles

    for d in drops[:]:
        if d['y'] > 5: d['y'] -= 1
        if check_collision(player_pos[0], player_pos[2], 10, d['x'], d['z'], 15):
            if d['type'] == 'DIAMOND': diamonds_collected += 1
            elif d['type'] == 'AMMO': player_ammo += 10
            elif d['type'] == 'BOMB': player_bombs += 1
            elif d['type'] == 'SMALL_HP': player_hp = min(300, player_hp + 10)
            elif d['type'] == 'EGG':
                if random.random() < 0.5:
                    player_hp = min(300, player_hp + 30)
                else:
                    player_hp -= 10
            drops.remove(d)

    if boss['active'] and not boss['dead']:
        boss['x'] += math.cos(global_time)*1.5; boss['z'] += math.sin(global_time)*1.5
        boss['shoot_timer'] += 1
        if boss['shoot_timer'] > 50:
            boss['shoot_timer'] = 0
            ang = math.atan2(player_pos[2]-boss['z'], player_pos[0]-boss['x'])
            projectiles.append({'x': boss['x'], 'z': boss['z'], 'vx': math.cos(ang)*4, 'vz': math.sin(ang)*4, 'type': 'boss', 'life': 150})

    if player_hp <= 0: game_over = True
    mx, mz = int(player_pos[0]/CELL_SIZE), int(player_pos[2]/CELL_SIZE)
    if 0 <= mx < MAP_DIM and 0 <= mz < MAP_DIM and map_data[mx][mz] == C_EXIT: level_complete = True

def detonate_bomb():
    global player_bombs, map_data, respawning_spikes
    if player_bombs > 0:
        player_bombs -= 1
        px, pz = player_pos[0], player_pos[2]
        cx, cz = int(px/CELL_SIZE), int(pz/CELL_SIZE)
        for i in range(cx-10, cx+10):
            for j in range(cz-10, cz+10):
                if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM:
                    if map_data[i][j] == C_SPIKE_HIDDEN: 
                        map_data[i][j] = C_EMPTY
                        respawning_spikes.append({'x': i, 'z': j, 'timer': 600})
        for e in moving_enemies[:]:
            if check_collision(px, pz, 200, e['x'], e['z'], 10): moving_enemies.remove(e)


def draw_enemy(e):
    glPushMatrix()
    glTranslatef(e['x'], 15 + math.sin(global_time*5)*5, e['z'])
    glPushMatrix()
    glScalef(1.5, 0.5, 1.5)
    glColor3f(0.6, 0.0, 0.8) 
    gluSphere(gluNewQuadric(), 8, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 3, 0)
    glColor3f(0.2, 1.0, 0.2)
    gluSphere(gluNewQuadric(), 4, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glRotatef(global_time * 100, 0, 1, 0)
    glColor3f(1.0, 1.0, 0.0)
    for i in range(4):
        glPushMatrix()
        glRotatef(90 * i, 0, 1, 0)
        glTranslatef(12, 0, 0)
        glutSolidCube(4)
        glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def draw_bird(b):
    glPushMatrix()
    glTranslatef(b['x'], b['y'], b['z'])
    heading = b['angle'] + (1.57 if b['speed'] > 0 else -1.57)
    glRotatef(-math.degrees(heading), 0, 1, 0)
    glColor3f(0.0, 1.0, 1.0)
    glPushMatrix()
    glScalef(1, 0.5, 2)
    gluSphere(gluNewQuadric(), 4, 8, 8)
    glPopMatrix()
    flap = math.sin(global_time * 20) * 30
    glColor3f(1.0, 1.0, 1.0) 
    glPushMatrix()
    glRotatef(flap, 0, 0, 1)
    glTranslatef(5, 0, 0)
    glScalef(4, 0.2, 2)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glRotatef(-flap, 0, 0, 1)
    glTranslatef(-5, 0, 0)
    glScalef(4, 0.2, 2)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()

def draw_boss_fancy(b):
    glPushMatrix()
    glTranslatef(b['x'], 30, b['z'])
    

    glTranslatef(0, math.sin(global_time * 3) * 5, 0)
    
    if b['stage'] == 1:
        # SPIKED CRUSHER ---
        glRotatef(global_time * 50, 0, 1, 0) 
        glRotatef(global_time * 30, 1, 0, 0) 
        
        # Red Core Cube
        glColor3f(0.9, 0.2, 0.2)
        glutSolidCube(20)
        
        # Yellow Spikes
        glColor3f(1.0, 0.8, 0.0)
        directions = [
            (0, 1,0,0), (90, 1,0,0), (-90, 1,0,0), 
            (90, 0,1,0), (-90, 0,1,0), (180, 1,0,0) 
        ]
        for angle, x, y, z in directions:
            glPushMatrix()
            if angle != 0: glRotatef(angle, x, y, z)
            glTranslatef(0, 0, 10)
            glutSolidCone(5, 15, 10, 2)
            glPopMatrix()
            
    else:
        #  DARK STAR ---
        glRotatef(math.sin(global_time)*10, 1, 0, 1)
        
        glColor3f(0.6, 0.0, 0.8)
        gluSphere(gluNewQuadric(), 15, 20, 20)
        
        glColor3f(0.0, 1.0, 1.0)
        glPushMatrix()
        glRotatef(global_time * 100, 0, 1, 0)
        glScalef(1, 0.1, 1)
        glutWireSphere(25, 15, 15)
        glPopMatrix()
        
        glColor3f(0.0, 1.0, 0.0)
        for i in range(4):
            glPushMatrix()
            glRotatef(global_time*80 + i*90, 0, 1, 0) 
            glRotatef(i*45, 0, 0, 1) 
            glTranslatef(25, 0, 0)
            glutSolidSphere(3, 10, 10)
            glPopMatrix()

    glPopMatrix()

def draw_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    lx = math.cos(player_angle); lz = math.sin(player_angle); ly = math.sin(player_pitch)
    gluLookAt(player_pos[0], 20, player_pos[2],
              player_pos[0] + lx*100, 20 + ly*100, player_pos[2] + lz*100, 0, 1, 0)

    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            wx, wz = x * CELL_SIZE, z * CELL_SIZE
            if abs(wx - player_pos[0]) > 600 or abs(wz - player_pos[2]) > 600: continue
            cell = map_data[x][z]
            
            if cell == C_WALL:
                glPushMatrix()
                glTranslatef(wx, WALL_HEIGHT/2, wz)
                glScalef(1, WALL_HEIGHT/CELL_SIZE, 1)
                
                # Solid Wall
                glColor3f(0.4, 0.2, 0.1) 
                glutSolidCube(CELL_SIZE)
                
                # Black Border
                glColor3f(0.0, 0.0, 0.0) 
                glLineWidth(2.0)
                glutWireCube(CELL_SIZE * 1.02)
                glLineWidth(1.0)
                
                glPopMatrix()
            
            elif cell in [C_EMPTY, C_SPIKE_HIDDEN, C_BOSS_ARENA, C_EXIT]:
                if (x+z)%2 == 0: glColor3f(0.5, 0.5, 0.55)
                else: glColor3f(0.45, 0.45, 0.5) 
                if cell == C_BOSS_ARENA: glColor3f(0.3, 0.0, 0.0)
                
                glBegin(GL_QUADS)
                glVertex3f(wx-10, 0, wz-10); glVertex3f(wx+10, 0, wz-10)
                glVertex3f(wx+10, 0, wz+10); glVertex3f(wx-10, 0, wz+10)
                glEnd()
                
                if cell == C_SPIKE_HIDDEN:
                    h = -15 + (math.sin(global_time * 2) + 1) * 15 
                    
                    glColor3f(0.5, 0.5, 0.5)
                    glPushMatrix()
                    glTranslatef(wx, h, wz); glRotatef(-90, 1, 0, 0)
                    gluCylinder(gluNewQuadric(), 4, 0, 15, 6, 2) 
                    glPopMatrix()

    for e in moving_enemies:
        draw_enemy(e)

    for b in birds:
        draw_bird(b)

    if boss['active'] and not boss['dead']:
        draw_boss_fancy(boss)

    for d in drops:
        glPushMatrix(); glTranslatef(d['x'], d['y'], d['z']); glRotatef(global_time*50, 0, 1, 0)
        if d['type'] == 'DIAMOND': 
            glColor3f(0,0,1); glRotatef(45, 1, 0, 1); glutSolidCube(10)
        elif d['type'] == 'BOMB': 
            glColor3f(0,0,0); gluSphere(gluNewQuadric(), 4, 8, 8)
        elif d['type'] == 'EGG':
            glColor3f(1.0, 0.8, 0.0); gluSphere(gluNewQuadric(), 5, 8, 8)
        elif d['type'] == 'SMALL_HP':
            glColor3f(0, 1, 0); glutSolidCube(6)
        elif d['type'] == 'AMMO':
            glColor3f(0, 0, 1); glutSolidCube(6)
        else: 
            glColor3f(1,1,0); glutSolidCube(4)
        glPopMatrix()

    glColor3f(1, 1, 0)
    for p in player_bullets:
        glPushMatrix(); glTranslatef(p['x'], 15, p['z']); gluSphere(gluNewQuadric(), 2, 5, 5); glPopMatrix()
    glColor3f(1, 0, 0)
    for p in projectiles:
        glPushMatrix(); glTranslatef(p['x'], 15, p['z']); gluSphere(gluNewQuadric(), 3, 5, 5); glPopMatrix()

    if level_complete or boss['dead']:
        glPushMatrix(); glTranslatef(boss['x'], 0, boss['z']); glRotatef(-90, 1, 0, 0); glColor3f(0,1,0); gluCylinder(gluNewQuadric(), 10, 10, 30, 10, 1); glPopMatrix()

    glDisable(GL_DEPTH_TEST)
    draw_minimap()
    draw_hud()
    glEnable(GL_DEPTH_TEST)
    
    glutSwapBuffers()

def draw_minimap():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    mx, my, ms = 20, 20, 150
    glColor3f(0, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(mx, my); glVertex2f(mx+ms, my); glVertex2f(mx+ms, my+ms); glVertex2f(mx, my+ms)
    glEnd()
    
    world_size = MAP_DIM * CELL_SIZE
    px = (player_pos[0] / world_size) * ms
    pz = (player_pos[2] / world_size) * ms
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(mx+px-3, my+pz-3); glVertex2f(mx+px+3, my+pz-3); glVertex2f(mx+px+3, my+pz+3); glVertex2f(mx+px-3, my+pz+3)
    glEnd()
    
    if not boss['dead']:
        bx = (boss['x'] / world_size) * ms
        bz = (boss['z'] / world_size) * ms
        glColor3f(1.0, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(mx+bx-4, my+bz-4); glVertex2f(mx+bx+4, my+bz-4); glVertex2f(mx+bx+4, my+bz+4); glVertex2f(mx+bx-4, my+bz+4)
        glEnd()
    
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_hud():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    glColor3f(1, 1, 1)
    draw_text_2d(20, WINDOW_HEIGHT-30, f"HP: {int(player_hp)} | AMMO: {player_ammo}")
    draw_text_2d(20, WINDOW_HEIGHT-60, f"DIAMONDS: {diamonds_collected}/{diamonds_needed} | BOMBS: {player_bombs}")
    draw_text_2d(20, WINDOW_HEIGHT-90, f"STAMINA: {int(player_stamina)}%")
    
    msg = "BOSS UNLOCKED!" if boss_arena_unlocked else "LOCKED"
    draw_text_2d(WINDOW_WIDTH//2-50, WINDOW_HEIGHT-40, msg)
    if game_over: draw_text_2d(WINDOW_WIDTH//2-60, WINDOW_HEIGHT//2, "GAME OVER (R)")
    if level_complete: draw_text_2d(WINDOW_WIDTH//2-80, WINDOW_HEIGHT//2, "LEVEL 2 COMPLETE (R)")

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def keyboard(key, x, y):
    global shift_held
    try: key = key.lower()
    except: pass
    
    shift_held = (glutGetModifiers() & GLUT_ACTIVE_SHIFT) != 0
    
    key_states[key] = True
    if key == b'r': generate_level()
    if key == b'f': detonate_bomb()

def keyboard_up(key, x, y):
    global shift_held
    try: key = key.lower()
    except: pass
    
    shift_held = (glutGetModifiers() & GLUT_ACTIVE_SHIFT) != 0
    
    key_states[key] = False

def special(key, x, y): 
    global shift_held
    shift_held = (glutGetModifiers() & GLUT_ACTIVE_SHIFT) != 0
    key_states[key] = True

def special_up(key, x, y): 
    global shift_held
    shift_held = (glutGetModifiers() & GLUT_ACTIVE_SHIFT) != 0
    key_states[key] = False

def mouse(button, state, x, y):
    global player_ammo
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and player_ammo > 0:
        player_ammo -= 1
        vx = math.cos(player_angle) * 6
        vz = math.sin(player_angle) * 6
        player_bullets.append({'x': player_pos[0], 'z': player_pos[2], 'vx': vx, 'vz': vz, 'life': 100})

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"level 1: iron defender")
    
    
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    
    generate_level()
    glutDisplayFunc(draw_scene)
    glutIdleFunc(update_logic)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special)
    glutSpecialUpFunc(special_up)
    glutMouseFunc(mouse)
    glutMainLoop()

if __name__ == "__main__":
    main()









##level3
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ==========================================
# Global Configuration
# ==========================================
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

MAP_DIM = 100        
CELL_SIZE = 30       
WALL_HEIGHT = 70    

C_EMPTY = 0
C_WALL = 1
C_MINE_ZONE = 2      
C_BOSS_ARENA = 3     # 
C_START = 4
C_EXIT = 5

map_data = []       
display_list = None 
hole_locations = [] # Track specific hole positions: (wx, wz, side)
solution_path = []  # Added to support l1.txt structure

# --- ENTITY LISTS ---
mines = []      
particles = [] 
thrown_rocks = []  # Projectiles in the air
animals = []       # Added Rabbits
boulders = []      # Added from 
boss_minions = []  # Added from 
ground_pills = []  # NEW: Pills dropped on the ground
rain_rocks = []    # NEW: Rock rain projectiles
rolling_rocks = [] # NEW: Big rolling obstacles

# --- STATE FOR ROCK RAIN ---
rain_active_timer = 0 # Ticks remaining for current rain
next_rain_trigger = 400 # Ticks until next rain starts

# --- BOSS STATE (Added from bal.txt) ---
boss_active = False
boss_defeated = False
boss_obj = {
    'x': 0, 'z': 0, 
    'hp': 700,          # REDUCED TO 700
    'max_hp': 700,      # REDUCED TO 700
    'timer': 0
}

# --- PLAYER STATE ---
player_pos = [0, 0, 0]
player_angle = 1.57 
base_speed = 5.5 # CHANGED PLAYER SPEED TO 5.5
player_speed = base_speed
animal_speed = base_speed / 3.0 # Added Animal Speed
key_states = {}
rock_count = 10    # Inventory for collected mines - CHANGED FROM 0 TO 10

# --- CHEAT MODE STATE ---
cheat_mode = False 
auto_gun_follow = False
cheat_timer = 0  
cheat_cooldown = 0 # NEW: Cooldown for Cheat Mode

# --- NEW SHIELD STATE ---
shield_pill_bag = 0
player_shield_timer = 0 # 200 ticks = 10 seconds (approx)

player_hp = 100.0
hp_warning_timer = 0 # NEW: Timer for showing HP requirement message
game_over = False
level_complete = False 
global_time = 0.0

# ==========================================
# BFS PATH SOLVER (From l1.txt structure)
# ==========================================
def solve_maze():
    global solution_path
    start_node = (5, 5) 
    target_gx = int(boss_obj['x'] // CELL_SIZE)
    target_gz = int(boss_obj['z'] // CELL_SIZE)
    target_node = (target_gx, target_gz)
    
    queue = [start_node]
    visited = {start_node}
    came_from = {start_node: None}
    found_dest = None
    
    while queue:
        current = queue.pop(0)
        if current == target_node or map_data[current[0]][current[1]] == C_BOSS_ARENA:
            found_dest = current
            break
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < MAP_DIM and 0 <= ny < MAP_DIM:
                if (nx, ny) not in visited and map_data[nx][ny] != C_WALL:
                    visited.add((nx, ny))
                    came_from[(nx, ny)] = current
                    queue.append((nx, ny))
    path = []
    if found_dest:
        curr = found_dest
        while curr:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
    solution_path = path

# ==========================================
# 1. Map Generation (COMPLICATED ZIG-ZAG VERSION)
# ==========================================
def generate_level_3():
    global map_data, player_pos, display_list, mines, particles, game_over, level_complete, player_hp, rock_count, thrown_rocks, animals, hole_locations
    global boss_active, boss_defeated, boss_obj, boulders, boss_minions, cheat_mode, shield_pill_bag, player_shield_timer, ground_pills
    global rain_rocks, rain_active_timer, next_rain_trigger, cheat_timer, auto_gun_follow, cheat_cooldown, rolling_rocks, hp_warning_timer
    
    # Fill with Walls
    map_data = [[C_WALL for _ in range(MAP_DIM)] for _ in range(MAP_DIM)]
    mines, particles, thrown_rocks, animals, hole_locations, boulders, boss_minions, ground_pills, rain_rocks, rolling_rocks = [], [], [], [], [], [], [], [], [], []
    game_over = False
    level_complete = False
    boss_active = False
    boss_defeated = False
    player_hp = 100000000.0
    hp_warning_timer = 0
    rock_count = 1000000 # CHANGED FROM 0 TO 10
    shield_pill_bag = 0
    player_shield_timer = 0
    boss_obj['hp'] = 700        # RESET TO 700
    boss_obj['max_hp'] = 700    # RESET TO 700
    cheat_mode = False
    cheat_timer = 0
    cheat_cooldown = 0
    auto_gun_follow = False
    
    # Reset Rain
    rain_active_timer = 0
    next_rain_trigger = random.randint(300, 600)

    def create_rect(r_x, r_y, r_w, r_h, type=C_EMPTY):
        for i in range(r_w):
            for j in range(r_h):
                if 0 <= r_x + i < MAP_DIM and 0 <= r_y + j < MAP_DIM:
                    map_data[r_x + i][r_y + j] = type

    def check_overlap(x, y, w, h, existing_rooms, buffer=4): # Increased buffer for more maze-y space
        for r in existing_rooms:
            if (x - buffer < r['x'] + r['w'] and x + w + buffer > r['x'] and
                y - buffer < r['y'] + r['h'] and y + h + buffer > r['y']):
                return True
        return False

    def h_tunnel(x1, x2, z):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < MAP_DIM and 0 <= z < MAP_DIM:
                map_data[x][z] = C_EMPTY
                if z+1 < MAP_DIM: map_data[x][z+1] = C_EMPTY

    def v_tunnel(z1, z2, x):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if 0 <= x < MAP_DIM and 0 <= z < MAP_DIM:
                map_data[x][z] = C_EMPTY
                if x+1 < MAP_DIM: map_data[x+1][z] = C_EMPTY

    # --- ROOM GENERATION ---
    rooms = []
    # Start Room
    start_room = {'x': 2, 'y': 2, 'w': 6, 'h': 6} # Smaller rooms
    create_rect(2, 2, 6, 6, C_START)
    start_room['center'] = (5, 5)
    rooms.append(start_room)

    # Complicated Labyrinth: 120 attempts for smaller rooms
    for _ in range(120):
        w, h = random.randint(4, 7), random.randint(4, 7) # Forced small rooms
        x, y = random.randint(2, MAP_DIM-12), random.randint(2, MAP_DIM-12)
        if not check_overlap(x, y, w, h, rooms, buffer=4):
            create_rect(x, y, w, h)
            rooms.append({'x': x, 'y': y, 'w': w, 'h': h, 'center': (x+w//2, y+h//2)})

    # Boss Room (Isolate at the very end)
    boss_room = {'x': MAP_DIM-22, 'y': MAP_DIM-22, 'w': 18, 'h': 18}
    create_rect(boss_room['x'], boss_room['y'], 18, 18, C_BOSS_ARENA)
    boss_room['center'] = (boss_room['x'] + 9, boss_room['y'] + 9)
    rooms.append(boss_room)

    # --- ZIG-ZAG TUNNELING ---
    for i in range(len(rooms) - 1):
        x1, y1 = rooms[i]['center']
        x2, y2 = rooms[i+1]['center']
        
        # Create a 3-segment Zig-Zag (S-curve) path
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        
        if random.random() < 0.5:
            h_tunnel(x1, mid_x, y1)
            v_tunnel(y1, y2, mid_x)
            h_tunnel(mid_x, x2, y2)
        else:
            v_tunnel(y1, mid_y, x1)
            h_tunnel(x1, x2, mid_y)
            v_tunnel(mid_y, y2, x2)

    # --- PILLAR INJECTION (STRICT 3 TILE GAP & COMPLICATED MAP) ---
    # Increased attempts to 2500 to fill more space while respecting the strict 3-tile gap
    for _ in range(2500):
        rx, rz = random.randint(5, MAP_DIM-10), random.randint(5, MAP_DIM-10)
        if map_data[rx][rz] == C_EMPTY:
            can_place = True
            # Check a radius of 3 tiles. Any wall within this range invalidates placement.
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if dx == 0 and dz == 0: continue
                    nx, nz = rx + dx, rz + dz
                    if 0 <= nx < MAP_DIM and 0 <= nz < MAP_DIM:
                        if map_data[nx][nz] == C_WALL:
                            can_place = False
                            break
                if not can_place: break
            
            if can_place:
                map_data[rx][rz] = C_WALL

    # Final entities
    boss_obj['x'], boss_obj['z'] = boss_room['center'][0] * CELL_SIZE, boss_room['center'][1] * CELL_SIZE
    map_data[boss_room['x'] + 9][boss_room['y'] + 14] = C_EXIT
    
    # Standard population
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EMPTY:
                r = random.random()
                # INCREASED LANDMINES
                if r < 0.06:
                    mines.append({'x': x*CELL_SIZE, 'y': 0, 'z': z*CELL_SIZE, 'state': 'IDLE', 'timer': 180})

    # RANDOM INCREASED RABBITS (Increased count)
    num_extra_rabbits = random.randint(80, 110)
    placed = 0
    while placed < num_extra_rabbits:
        rx, rz = random.randint(0, MAP_DIM-1), random.randint(0, MAP_DIM-1)
        if map_data[rx][rz] == C_EMPTY:
            animals.append({'x': rx*CELL_SIZE, 'z': rz*CELL_SIZE, 'home_x': rx*CELL_SIZE, 'home_z': rz*CELL_SIZE, 'angle': 0, 'active': True})
            placed += 1

    # Initial Big Rocks - REDUCED NUMBER
    num_big_rocks = random.randint(5, 8)
    placed_rocks = 0
    while placed_rocks < num_big_rocks:
        rx, rz = random.randint(2, MAP_DIM-2), random.randint(2, MAP_DIM-2)
        if map_data[rx][rz] == C_EMPTY:
            rolling_rocks.append({'x': rx*CELL_SIZE, 'y': 15, 'z': rz*CELL_SIZE})
            placed_rocks += 1

    for x in range(1, MAP_DIM-1):
        for z in range(1, MAP_DIM-1):
            if map_data[x][z] == C_WALL:
                for dx, dz, side in [(0,1,'F'), (0,-1,'B'), (-1,0,'L'), (1,0,'R')]:
                    if 0 <= x+dx < MAP_DIM and 0 <= z+dz < MAP_DIM:
                        if map_data[x+dx][z+dz] == C_EMPTY and random.random() < 0.1:
                            hole_locations.append({'gx':x, 'gz':z, 'side':side})
                            break

    player_pos = [start_room['center'][0] * CELL_SIZE, 20, start_room['center'][1] * CELL_SIZE]
    solve_maze()
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
            wx, wz = x * CELL_SIZE, z * CELL_SIZE
            if cell == C_WALL:
                glPushMatrix()
                glTranslatef(wx, WALL_HEIGHT/2, wz)
                glScalef(1, WALL_HEIGHT/CELL_SIZE, 1)
                col = 0.3 + random.uniform(-0.05, 0.05)
                glColor3f(col, col, col) 
                glutSolidCube(CELL_SIZE)
                glPopMatrix()

                # --- DRAW SPECIFIC HOLES ---
                for h in hole_locations:
                    if h['gx'] == x and h['gz'] == z:
                        glColor3f(0, 0, 0)
                        glBegin(GL_QUADS)
                        if h['side'] == 'F':
                            glVertex3f(wx-4, 0.1, wz+CELL_SIZE/2+0.1); glVertex3f(wx+4, 0.1, wz+CELL_SIZE/2+0.1)
                            glVertex3f(wx+4, 8, wz+CELL_SIZE/2+0.1); glVertex3f(wx-4, 8, wz+CELL_SIZE/2+0.1)
                        elif h['side'] == 'B':
                            glVertex3f(wx-4, 0.1, wz-CELL_SIZE/2-0.1); glVertex3f(wx+4, 0.1, wz-CELL_SIZE/2-0.1)
                            glVertex3f(wx+4, 8, wz-CELL_SIZE/2-0.1); glVertex3f(wx-4, 8, wz-CELL_SIZE/2-0.1)
                        elif h['side'] == 'L':
                            glVertex3f(wx-CELL_SIZE/2-0.1, 0.1, wz-4); glVertex3f(wx-CELL_SIZE/2-0.1, 0.1, wz+4)
                            glVertex3f(wx-CELL_SIZE/2-0.1, 8, wz+4); glVertex3f(wx-CELL_SIZE/2-0.1, 8, wz-4)
                        elif h['side'] == 'R':
                            glVertex3f(wx+CELL_SIZE/2+0.1, 0.1, wz-4); glVertex3f(wx+CELL_SIZE/2+0.1, 0.1, wz+4)
                            glVertex3f(wx+CELL_SIZE/2+0.1, 8, wz+4); glVertex3f(wx+CELL_SIZE/2+0.1, 8, wz-4)
                        glEnd()

            elif cell in [C_EMPTY, C_START, C_BOSS_ARENA]:
                if cell == C_BOSS_ARENA: glColor3f(0.1, 0.1, 0.1)
                elif (x+z)%2 == 0: glColor3f(0.35, 0.25, 0.15) 
                else: glColor3f(0.30, 0.20, 0.10) 
                glBegin(GL_QUADS)
                glVertex3f(wx-CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz-CELL_SIZE/2)
                glVertex3f(wx+CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glVertex3f(wx-CELL_SIZE/2, 0, wz+CELL_SIZE/2)
                glEnd()
            elif cell == C_EXIT:
                glPushMatrix()
                glTranslatef(wx, 10, wz)
                glColor3f(1, 1, 1)
                glutSolidSphere(10, 10, 10)
                glBegin(GL_LINES); glVertex3f(0,0,0); glVertex3f(0, 200, 0); glEnd()
                glPopMatrix()
    glEndList()

def create_explosion(x, y, z):
    for _ in range(30):
        particles.append({
            'x': x, 'y': y, 'z': z,
            'dx': random.uniform(-3,3), 'dy': random.uniform(1,5), 'dz': random.uniform(-3,3),
            'life': 40
        })

def draw_entities():
    # 1. LANDMINES
    for m in mines:
        if m['state'] == 'EXPLODED': continue
        glPushMatrix()
        glTranslatef(m['x'], 2, m['z'])
        if m['state'] == 'IDLE':
            glColor3f(0.2, 0.2, 0.2)
            glScalef(1, 0.2, 1); glutSolidSphere(8, 8, 8)
            glColor3f(1, 0, 0); glPushMatrix(); glTranslatef(0, 5, 0); glutSolidSphere(1, 4, 4); glPopMatrix()
        elif m['state'] == 'ACTIVE':
            if int(global_time * 10) % 2 == 0: glColor3f(1.0, 0.0, 0.0)
            else: glColor3f(0.0, 0.0, 0.0)
            glScalef(1.2, 0.4, 1.2); glutSolidSphere(10, 8, 8)
        glPopMatrix()

    # 2. THROWN ROCKS
    for r in thrown_rocks:
        glPushMatrix()
        glTranslatef(r['x'], r['y'], r['z'])
        glColor3f(0.4, 0.4, 0.4)
        glutSolidSphere(4, 8, 8)
        glPopMatrix()

    # 3. PARTICLES
    for p in particles:
        glPushMatrix()
        glTranslatef(p['x'], p['y'], p['z'])
        glScalef(p['life']/10.0, p['life']/10.0, p['life']/10.0)
        if random.random() < 0.5: glColor3f(1, 0, 0)
        else: glColor3f(1, 0.6, 0)
        glutSolidCube(3)
        glPopMatrix()

    # 4. ANIMALS
    for a in animals:
        if a['active']:
            glPushMatrix()
            glTranslatef(a['x'], 3, a['z'])
            glRotatef(math.degrees(a.get('angle', 0)), 0, 1, 0)
            glColor3f(0.6, 0.55, 0.5) 
            glPushMatrix()
            glScalef(1, 0.7, 1.5)
            glutSolidCube(6)
            glPopMatrix() 
            glPushMatrix()
            glTranslatef(0, 3, 3)
            glutSolidCube(4)
            glPushMatrix()
            glTranslatef(-1, 2, 0)
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(0.5, 3, 4, 4)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(1, 2, 0)
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(0.5, 3, 4, 4)
            glPopMatrix()
            glPopMatrix() 
            glPushMatrix()
            glTranslatef(0, 0, -4)
            glutSolidCone(1, 2, 4, 4)
            glPopMatrix() 
            for lx in [-2, 2]:
                for lz in [-2, 2]:
                    glPushMatrix()
                    glTranslatef(lx, -2, lz)
                    glRotatef(90, 1, 0, 0)
                    glutSolidCone(0.5, 2, 4, 4)
                    glPopMatrix() 
            glPopMatrix()

    # 4.5. GROUND SHIELD PILLS
    for pill in ground_pills:
        glPushMatrix()
        glTranslatef(pill['x'], 4, pill['z'])
        glRotatef(global_time * 100, 0, 1, 0) # Rotate for visibility
        glColor3f(0, 0.6, 1.0) # Light blue pill
        glutSolidCube(6)
        glPopMatrix()

    # 5. BOSS
    if boss_active and not boss_defeated:
        glPushMatrix()
        glTranslatef(boss_obj['x'], 30, boss_obj['z']) 
        glScalef(4, 4, 4) 
        glColor3f(0.3, 0.25, 0.2); glutSolidCube(10) 
        glTranslatef(0, 8, 0); glColor3f(0.4, 0.35, 0.3); glutSolidSphere(4, 10, 10) 
        glColor3f(1, 0, 0); glTranslatef(-2, 0, 3); glutSolidSphere(1, 5, 5)
        glTranslatef(4, 0, 0); glutSolidSphere(1, 5, 5)
        glPopMatrix()

    # 6. BOULDERS (BOSS)
    glColor3f(0.2, 0.2, 0.2) 
    for b in boulders:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        glutSolidSphere(15, 10, 10) 
        glPopMatrix()
    
    # 6.2 ROLLING BIG ROCKS (OBSTACLES)
    glColor3f(0.1, 0.1, 0.1)
    for rr in rolling_rocks:
        glPushMatrix()
        glTranslatef(rr['x'], rr['y'], rr['z'])
        glRotatef(global_time * 100, 1, 0, 1) # Rolling effect
        glutSolidSphere(20, 12, 12)
        glPopMatrix()

    # 6.5 RAIN ROCKS (Drawn similar to boulders but maybe different size/color)
    glColor3f(0.5, 0.2, 0.1)
    for rr in rain_rocks:
        glPushMatrix()
        glTranslatef(rr['x'], rr['y'], rr['z'])
        glutSolidSphere(8, 6, 6)
        glPopMatrix()

    # 7. MINIONS
    glColor3f(0.6, 0.0, 0.8) 
    for e in boss_minions:
        glPushMatrix()
        s = 1.0 + 0.1 * math.sin(global_time * 2)
        glTranslatef(e['x'], 5, e['z'])
        glScalef(s * 1.2, s * 0.4, s * 1.2)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

    # --- SHIELD VISUAL EFFECT ---
    if player_shield_timer > 0:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        glTranslatef(player_pos[0], player_pos[1], player_pos[2])
        glColor4f(0.2, 0.6, 1.0, 0.3)
        glutSolidSphere(15, 10, 10)
        glPopMatrix()
        glDisable(GL_BLEND)

def draw_minimap():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    map_size = 150; margin = 20
    # Background
    glColor4f(0.1, 0.1, 0.1, 0.7); glBegin(GL_QUADS)
    glVertex2f(margin, margin); glVertex2f(margin+map_size, margin)
    glVertex2f(margin+map_size, margin+map_size); glVertex2f(margin, margin+map_size); glEnd()

    world_max = MAP_DIM * CELL_SIZE

    # Player (Green)
    px = (player_pos[0] / world_max) * map_size
    pz = (player_pos[2] / world_max) * map_size
    glColor3f(0, 1, 0); glPointSize(5); glBegin(GL_POINTS)
    glVertex2f(margin + px, margin + pz); glEnd()

    # Boss (Red)
    bx = (boss_obj['x'] / world_max) * map_size
    bz = (boss_obj['z'] / world_max) * map_size
    glColor3f(1, 0, 0); glPointSize(8); glBegin(GL_POINTS)
    glVertex2f(margin + bx, margin + pz); glEnd() # Note: minimap axis flipped slightly relative to 3d

    # Exit (White)
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EXIT:
                ex = (x * CELL_SIZE / world_max) * map_size
                ez = (z * CELL_SIZE / world_max) * map_size
                glColor3f(1, 1, 1); glPointSize(4); glBegin(GL_POINTS)
                glVertex2f(margin + ez, margin + ex); glEnd()

    glPopMatrix() # Pop GL_MODELVIEW matrix
    glMatrixMode(GL_PROJECTION) # Switch back to GL_PROJECTION
    glPopMatrix() # Pop GL_PROJECTION matrix
    glMatrixMode(GL_MODELVIEW) # Restore GL_MODELVIEW as the active matrix mode
    glEnable(GL_DEPTH_TEST)

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, r=1, g=1, b=1):
    glColor3f(r, g, b)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    glDisable(GL_DEPTH_TEST)
    
    shield_status = f"SHIELD: {int(player_shield_timer/20)}s" if player_shield_timer > 0 else "OFF"
    # UPDATED HP DISPLAY TO /300
    msg = f"LEVEL 3 | HP: {int(player_hp)}/300 | ROCKS: {rock_count} | BAG: {shield_pill_bag} PILLS | {shield_status}"
    draw_text(20, WINDOW_HEIGHT - 30, msg)
    
    # NEW HP REQUIREMENT WARNING
    if hp_warning_timer > 0:
        draw_text(WINDOW_WIDTH/2 - 180, WINDOW_HEIGHT/2 + 100, "NEED 150 HP TO ENTER BOSS AREA!", r=1.0, g=0.2, b=0.2)

    if rain_active_timer > 0:
        r_msg = "!!! ROCK RAIN !!!"
        draw_text(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT - 30, r_msg, r=1, g=0.5, b=0)

    if boss_active and not boss_defeated:
        b_msg = f"GOLEM: {boss_obj['hp']}/{boss_obj['max_hp']}"
        draw_text(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT - 50, b_msg, r=1, g=0.2, b=0.2)

    if game_over:
        raws = "YOU DIED"
        draw_text(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2, raws, r=1, g=0, b=0)
    if level_complete:
        draw_text(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2 + 20, "YOU WIN", r=0, g=1, b=0)
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 20, "ALL LEVELS PASSED", r=0, g=1, b=0)
        
    glEnable(GL_DEPTH_TEST)


# ==========================================
# 3. Physics & Logic
# ==========================================
def update_physics():
    global player_pos, player_angle, global_time, player_hp, game_over, level_complete, mines, particles, rock_count, thrown_rocks, animals
    global boss_active, boss_obj, boss_defeated, boulders, boss_minions, cheat_mode, cheat_cooldown
    global shield_pill_bag, player_shield_timer, ground_pills, cheat_timer, auto_gun_follow
    global rain_rocks, rain_active_timer, next_rain_trigger, rolling_rocks, display_list, map_data, hp_warning_timer
    
    if game_over or level_complete: return
    global_time += 0.05
    
    # Decrement warning timer
    if hp_warning_timer > 0:
        hp_warning_timer -= 1

    # --- AUTOMATIC SHIELD MANAGEMENT FROM BAG ---
    if player_shield_timer > 0:
        player_shield_timer -= 1
    elif shield_pill_bag > 0:
        shield_pill_bag -= 1
        player_shield_timer = 200 # 10 seconds (0.05 * 200 = 10 units)

    # --- ROCK RAIN LOGIC ---
    if rain_active_timer > 0:
        rain_active_timer -= 1
        for _ in range(random.randint(3, 6)):
            rx = random.uniform(0, MAP_DIM * CELL_SIZE)
            rz = random.uniform(0, MAP_DIM * CELL_SIZE)
            rain_rocks.append({'x': rx, 'y': 300, 'z': rz, 'vy': 0})
    else:
        next_rain_trigger -= 1
        if next_rain_trigger <= 0:
            rain_active_timer = 160 # ~8 seconds
            next_rain_trigger = random.randint(300, 600) # Cooldown for next rain

    # Update Rain Rocks movement
    active_rain_rocks = []
    for rr in rain_rocks:
        rr['vy'] += 0.4
        rr['y'] -= rr['vy']
        if rr['y'] <= 0:
            # Impact check when the rock rain hits the ground level
            dist_rr = math.sqrt((player_pos[0]-rr['x'])**2 + (player_pos[2]-rr['z'])**2)
            if dist_rr < 15 and player_shield_timer <= 0:
                # Check current player grid location
                pgx, pgz = int(player_pos[0] // CELL_SIZE), int(player_pos[2] // CELL_SIZE)
                if 0 <= pgx < MAP_DIM and 0 <= pgz < MAP_DIM and map_data[pgx][pgz] == C_BOSS_ARENA:
                    player_hp -= 5 # Boss area rain damage
                elif random.random() < 0.5:
                    player_hp -= 10 # Normal rain damage (50% chance, 10 HP)
        else:
            active_rain_rocks.append(rr)
    rain_rocks = active_rain_rocks

    # --- ROLLING ROCKS LOGIC (RANDOM TIME & SPACE SPAWNING) ---
    # Spawn a new big rock at random intervals - REDUCED PROBABILITY
    if random.random() < 0.002: 
        rx, rz = random.randint(5, MAP_DIM-5), random.randint(5, MAP_DIM-5)
        if map_data[rx][rz] == C_EMPTY:
            rolling_rocks.append({'x': rx*CELL_SIZE, 'y': 15, 'z': rz*CELL_SIZE})

    for rr in rolling_rocks:
        dx, dz = player_pos[0] - rr['x'], player_pos[2] - rr['z']
        dist = math.sqrt(dx*dx + dz*dz)
        if dist > 0:
            rr['x'] += (dx/dist) * (base_speed * 0.12)
            rr['z'] += (dz/dist) * (base_speed * 0.12)

    # --- MOVEMENT ---
    move_speed, strafe = 0, 0
    if key_states.get(b'w'): move_speed = player_speed
    if key_states.get(b's'): move_speed = -player_speed
    if key_states.get(b'a'): strafe = -player_speed
    if key_states.get(b'd'): strafe = player_speed
    if key_states.get(GLUT_KEY_LEFT): player_angle -= 0.04
    if key_states.get(GLUT_KEY_RIGHT): player_angle += 0.04

    # --- UPDATED CHEAT MODE LOGIC (ORBITING AROUND BOSS) ---
    if cheat_mode:
        cheat_timer -= 1
        player_shield_timer = 2 # Forced Shield ON
        
        if boss_active:
            # Calculate distance from boss
            rel_x = player_pos[0] - boss_obj['x']
            rel_z = player_pos[2] - boss_obj['z']
            radius = math.sqrt(rel_x**2 + rel_z**2)
            
            # Ensure radius is consistent during rotation
            if radius < 50: radius = 200 
            
            # Update position to rotate around the boss center
            current_orbit_angle = math.atan2(rel_z, rel_x)
            new_orbit_angle = current_orbit_angle + 0.03 # Rotation speed
            
            new_x = boss_obj['x'] + math.cos(new_orbit_angle) * radius
            new_z = boss_obj['z'] + math.sin(new_orbit_angle) * radius
            
            player_pos[0], player_pos[2] = new_x, new_z
            
            # Camera Angle strictly locked on Boss
            vx = boss_obj['x'] - player_pos[0]
            vz = boss_obj['z'] - player_pos[2]
            player_angle = math.atan2(vx, -vz)
        
        if cheat_timer <= 0:
            cheat_mode = False
            cheat_cooldown = 240
            player_shield_timer = 0
    elif cheat_cooldown > 0:
        cheat_cooldown -= 1
    
    # Process movement only if not in orbital cheat mode
    if not cheat_mode:
        dx = math.sin(player_angle) * move_speed + math.sin(player_angle + 1.57) * strafe
        dz = -math.cos(player_angle) * move_speed - math.cos(player_angle + 1.57) * strafe
        
        nx, nz = player_pos[0] + dx, player_pos[2] + dz
        gx, gz = int(round(nx / CELL_SIZE)), int(round(nz / CELL_SIZE))
        
        is_blocked_by_rock = False
        for rr in rolling_rocks:
            dist_to_rock = math.sqrt((nx - rr['x'])**2 + (nz - rr['z'])**2)
            if dist_to_rock < 22:
                is_blocked_by_rock = True
                if player_shield_timer <= 0: player_hp -= 0.2
                break

        if not is_blocked_by_rock and 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM and map_data[gx][gz] != C_WALL:
            # BOSS AREA ENTRY CHECK: Need at least 150 HP
            if map_data[gx][gz] == C_BOSS_ARENA and player_hp < 150 and not boss_active and not boss_defeated:
                hp_warning_timer = 60 # Show message for a while
                pass # Block movement into boss area
            else:
                player_pos[0], player_pos[2] = nx, nz
                if map_data[gx][gz] == C_BOSS_ARENA and not boss_active and not boss_defeated: 
                    boss_active = True
                if map_data[gx][gz] == C_EXIT: 
                    if boss_defeated: level_complete = True

    # --- PILL COLLECTION LOGIC ---
    remaining_pills = []
    for pill in ground_pills:
        dist_pill = math.sqrt((player_pos[0]-pill['x'])**2 + (player_pos[2]-pill['z'])**2)
        if dist_pill < 20:
            if player_shield_timer <= 0: player_shield_timer = 200
            else: shield_pill_bag += 1
        else: remaining_pills.append(pill)
    ground_pills = remaining_pills

    # --- LANDMINE COLLECTION/DETONATION LOGIC ---
    remaining_mines = []
    for m in mines:
        if m['state'] == 'EXPLODED': continue
        dist = math.sqrt((player_pos[0]-m['x'])**2 + (player_pos[2]-m['z'])**2)
        if m['state'] == 'IDLE' and dist < 15:
            m['state'] = 'ACTIVE'
        elif m['state'] == 'ACTIVE':
            if dist > 25: 
                rock_count += 1
                m['state'] = 'EXPLODED' 
                continue
            m['timer'] -= 1
            if m['timer'] <= 0:
                m['state'] = 'EXPLODED'
                create_explosion(m['x'], 5, m['z'])
                if dist < 40 and player_shield_timer <= 0: 
                    player_hp -= 60 
        if m['state'] != 'EXPLODED':
            remaining_mines.append(m)
    mines = remaining_mines
    
    # --- BOSS AI ---
    if boss_active:
        # Trigger rain in the boss area constantly
        if rain_active_timer <= 0: rain_active_timer = 160

        boss_obj['timer'] += 1
        bx, bz = boss_obj['x'], boss_obj['z']
        v_to_p_x, v_to_p_z = player_pos[0] - bx, player_pos[2] - bz
        d_to_p = math.sqrt(v_to_p_x**2 + v_to_p_z**2)
        if d_to_p < 30:
            if player_shield_timer <= 0: player_hp -= 1.0 
            player_pos[0] += (v_to_p_x / d_to_p) * 10
            player_pos[2] += (v_to_p_z / d_to_p) * 10
        if d_to_p > 25: 
            boss_obj['x'] += (v_to_p_x / d_to_p) * (base_speed * 0.15)
            boss_obj['z'] += (v_to_p_z / d_to_p) * (base_speed * 0.15)
        if boss_obj['timer'] % 200 == 0: 
            boulders.append({'x': player_pos[0], 'y': 200, 'z': player_pos[2], 'vy': 0})
        if boss_obj['timer'] % 400 == 0: 
            boss_minions.append({'x': boss_obj['x'] + random.randint(-50,50), 'z': boss_obj['z'] + random.randint(-50,50)})
        if boss_obj['timer'] % 300 == 0 and boss_obj['hp'] < boss_obj['max_hp']: 
            boss_obj['hp'] += 20

    # --- BOULDERS (BOSS) ---
    active_boulders = []
    for b in boulders:
        b['vy'] += 0.5; b['y'] -= b['vy']
        if b['y'] <= 0:
            create_explosion(b['x'], 2, b['z'])
            if math.sqrt((player_pos[0]-b['x'])**2 + (player_pos[2]-b['z'])**2) < 30: 
                if player_shield_timer <= 0:
                    player_hp = 0; game_over = True
        else: active_boulders.append(b)
    boulders = active_boulders

    # --- MINIONS ---
    enemy_speed = base_speed / 8.0 
    for m in boss_minions:
        dx, dz = player_pos[0] - m['x'], player_pos[2] - m['z']
        dst = math.sqrt(dx*dx + dz*dz)
        if dst < 15: 
            if player_shield_timer <= 0: player_hp -= 0.5
        elif dst < 400: m['x'] += (dx/dst) * enemy_speed; m['z'] += (dz/dst) * enemy_speed

    # --- ANIMALS PHYSICS (RABBITS) ---
    for a in animals:
        if a['active']:
            dist_p = math.sqrt((player_pos[0]-a['x'])**2 + (player_pos[2]-a['z'])**2)
            if dist_p < 120:
                best_target_x, best_target_z = -1, -1
                min_h_dist = 9999
                for h in hole_locations:
                    hx, hz = h['gx'] * CELL_SIZE, h['gz'] * CELL_SIZE
                    if h['side'] == 'F': hz += (CELL_SIZE/2 + 0.5)
                    elif h['side'] == 'B': hz -= (CELL_SIZE/2 + 0.5)
                    elif h['side'] == 'L': hx -= (CELL_SIZE/2 + 0.5)
                    elif h['side'] == 'R': hx += (CELL_SIZE/2 + 0.5)
                    dist_hole_to_player = math.sqrt((player_pos[0]-hx)**2 + (player_pos[2]-hz)**2)
                    if dist_hole_to_player > dist_p:
                        hd = math.sqrt((a['x']-hx)**2 + (a['z']-hz)**2)
                        if hd < min_h_dist:
                            min_h_dist = hd; best_target_x, best_target_z = hx, hz
                if best_target_x != -1:
                    vx, vz = best_target_x - a['x'], best_target_z - a['z']
                    v_mag = math.sqrt(vx*vx + vz*vz)
                    if v_mag > 1.5: 
                        a['x'] += (vx / v_mag) * animal_speed
                        a['z'] += (vz / v_mag) * animal_speed
                        a['angle'] = math.atan2(vx, vz)
                    else: a['active'] = False
        else:
            if math.sqrt((player_pos[0]-a['home_x'])**2 + (player_pos[2]-a['home_z'])**2) > 250:
                a['active'] = True; a['x'] = a['home_x']; a['z'] = a['home_z']

    # --- THROWN ROCKS PHYSICS ---
    active_rocks = []
    for r in thrown_rocks:
        if 'target' in r and r['target']['active']:
            tr = r['target']
            vec_x, vec_y, vec_z = tr['x'] - r['x'], 3 - r['y'], tr['z'] - r['z']
            dist_t = math.sqrt(vec_x**2 + vec_y**2 + vec_z**2)
            if dist_t > 0:
                speed_t = 12.0
                r['vx'], r['vy'], r['vz'] = (vec_x/dist_t)*speed_t, (vec_y/dist_t)*speed_t, (vec_z/dist_t)*speed_t
        else: r['vy'] -= 0.1 

        r['x'] += r['vx']; r['y'] += r['vy']; r['z'] += r['vz']
        gx, gz = int(round(r['x']/CELL_SIZE)), int(round(r['z']/CELL_SIZE))
        hit_impact = False
        
        if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM:
            if map_data[gx][gz] == C_WALL: hit_impact = True
        
        # --- NEW LOGIC: COLLISION WITH ROLLING BIG ROCKS ---
        for rr in rolling_rocks[:]:
            dist_p_rock = math.sqrt((r['x'] - rr['x'])**2 + (r['z'] - rr['z'])**2)
            if dist_p_rock < 25: # Hitbox for destruction
                create_explosion(rr['x'], 15, rr['z'])
                rolling_rocks.remove(rr)
                hit_impact = True
                break 

        if boss_active:
            if math.sqrt((r['x']-boss_obj['x'])**2 + (r['z']-boss_obj['z'])**2) < 50:
                boss_obj['hp'] -= 15; hit_impact = True
                if boss_obj['hp'] <= 0: 
                    boss_active = False; boss_defeated = True
                    # OPEN GATE
                    bx, bz = MAP_DIM-22, MAP_DIM-22
                    for i in range(bx, bx+18):
                        for j in range(bz+13, bz+16):
                            if map_data[i][j] == C_WALL: map_data[i][j] = C_EMPTY
                    display_list = None

        for a in animals:
            if a['active']:
                adist = math.sqrt((r['x']-a['x'])**2 + (r['z']-a['z'])**2)
                if adist < 15 and 0 < r['y'] < 30: 
                    a['active'] = False
                    if random.random() < 0.5:
                        player_hp = min(300.0, player_hp + random.randint(21, 40)) # INCREASED CAP TO 300
                    else: ground_pills.append({'x': a['x'], 'z': a['z']})
                    hit_impact = True; break

        if r['y'] <= 0 or hit_impact: create_explosion(r['x'], max(2, r['y']), r['z'])
        else: active_rocks.append(r)
    thrown_rocks = active_rocks

    active_particles = []
    for p in particles:
        p['x'] += p['dx']; p['y'] += p['dy']; p['z'] += p['dz']
        p['dy'] -= 0.1; p['life'] -= 1
        if p['life'] > 0 and p['y'] > 0: active_particles.append(p)
    particles = active_particles

    if player_hp <= 0: game_over = True

def setupCamera():
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    gluPerspective(60, WINDOW_WIDTH/WINDOW_HEIGHT, 1, 1000)
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix
    lx = player_pos[0] + math.sin(player_angle) * 100
    lz = player_pos[2] - math.cos(player_angle) * 100
    gluLookAt(player_pos[0], 25, player_pos[2], lx, 25, lz, 0, 1, 0)

# ==========================================
# Input Callbacks
# ==========================================
def mouseListener(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        target_rabbit = None
        f_x, f_z = math.sin(player_angle), -math.cos(player_angle)
        for a in animals:
            if a['active']:
                dx, dz = a['x'] - player_pos[0], a['z'] - player_pos[2]
                dist = math.sqrt(dx*dx + dz*dz)
                if dist < 300:
                    nx, nz = dx/dist, dz/dist
                    dot = f_x * nx + f_z * nz
                    if dot > 0.99:
                        target_rabbit = a
                        break
        new_rock = {'x': player_pos[0], 'y': 25, 'z': player_pos[2], 'vx': f_x * 8, 'vy': 2, 'vz': f_z * 8}
        if target_rabbit: new_rock['target'] = target_rabbit
        thrown_rocks.append(new_rock)

def keyboardListener(key, x, y):
    global player_angle, cheat_mode, cheat_timer, cheat_cooldown, auto_gun_follow, player_shield_timer, shield_pill_bag, rock_count, boss_active, boss_obj, boss_defeated, map_data, display_list, rolling_rocks
    key_states[key] = True

    if key == b'c' and cheat_cooldown == 0:
        cheat_mode = True # Use explicit activation
        cheat_timer = 200 # 10 seconds (20 ticks per second)
        cheat_cooldown = 600 # 30 seconds cooldown
        
        # Reposition and re-orient camera if in boss area
        if boss_active:
            # Calculate direction vector from boss to player
            dx = player_pos[0] - boss_obj['x']
            dz = player_pos[2] - boss_obj['z']
            dist = math.sqrt(dx*dx + dz*dz)
            if dist == 0: dx, dz, dist = 1, 0, 1
            
            # Distance player from boss (certain amount: 250 units)
            safe_dist = 250
            player_pos[0] = boss_obj['x'] + (dx/dist) * safe_dist
            player_pos[2] = boss_obj['z'] + (dz/dist) * safe_dist
            
            # Adjust initial angle to look directly at the boss
            vx = boss_obj['x'] - player_pos[0]
            vz = boss_obj['z'] - player_pos[2]
            player_angle = math.atan2(vx, -vz)

        print(f"Cheat Mode: {cheat_mode}")
    elif key == b'g':
        auto_gun_follow = not auto_gun_follow
        print(f"Auto Gun Follow: {auto_gun_follow}")
    elif key == b's' and shield_pill_bag > 0 and player_shield_timer == 0:
        shield_pill_bag -= 1
        player_shield_timer = 200 # 10 seconds shield
        print("Shield Activated!")
    elif key == b'r':
        generate_level_3()
    elif key == b'l':
        if cheat_mode: return 
        
        if boss_active:
            boss_obj['hp'] -= 50
            if boss_obj['hp'] <= 0:
                boss_obj['hp'] = 0
                boss_active = False
                boss_defeated = True
                bx, bz = MAP_DIM-22, MAP_DIM-22
                for i in range(bx, bx+18):
                    for j in range(bz+13, bz+16):
                        if map_data[i][j] == C_WALL: map_data[i][j] = C_EMPTY
                display_list = None
        if rock_count > 0:
            rock_count -= 1
            # Shoot a rock
            thrown_rocks.append({'x': player_pos[0], 'y': 25, 'z': player_pos[2], 'vx': math.sin(player_angle) * 8, 'vy': 2, 'vz': -math.cos(player_angle) * 8})

def keyboardUpListener(key, x, y): 
    key_states[key] = False

def specialKeyListener(key, x, y): key_states[key] = True
def specialKeyUpListener(key, x, p): key_states[key] = False

def showScreen():
    glPushMatrix() # Push the current matrix onto the stack
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)  # Set viewport size

    setupCamera()

    # Draw the maze
    if display_list is None:
        create_display_list()
    glCallList(display_list)

    draw_entities()
    draw_hud()
    draw_minimap()

    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()
    glPopMatrix() # Pop the matrix pushed at the beginning of showScreen()

def idle():
    update_physics()
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)  # Window size
    glutCreateWindow(b"Level 3: Final Challenge")  # Create the window
    glEnable(GL_DEPTH_TEST) # Enable depth testing for 3D rendering
    generate_level_3() # Initialize game level
    glutDisplayFunc(showScreen)  # Register display function
    glutIdleFunc(idle)  # Register the idle function
    glutKeyboardFunc(keyboardListener); glutKeyboardUpFunc(keyboardUpListener)  # Register keyboard listeners
    glutSpecialFunc(specialKeyListener); glutSpecialUpFunc(specialKeyUpListener)  # Register special keyboard listeners
    glutMouseFunc(mouseListener)  # Register mouse listener
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()