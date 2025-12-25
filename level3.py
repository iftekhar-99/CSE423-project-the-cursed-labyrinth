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
rock_count = 0     # Inventory for collected mines

# --- CHEAT MODE STATE ---
cheat_mode = False 
auto_gun_follow = False
cheat_timer = 0  
cheat_cooldown = 0 # NEW: Cooldown for Cheat Mode

# --- NEW SHIELD STATE ---
shield_pill_bag = 0
player_shield_timer = 0 # 200 ticks = 10 seconds (approx)

player_hp = 100.0
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
    global rain_rocks, rain_active_timer, next_rain_trigger, cheat_timer, auto_gun_follow, cheat_cooldown, rolling_rocks
    
    # Fill with Walls
    map_data = [[C_WALL for _ in range(MAP_DIM)] for _ in range(MAP_DIM)]
    mines, particles, thrown_rocks, animals, hole_locations, boulders, boss_minions, ground_pills, rain_rocks, rolling_rocks = [], [], [], [], [], [], [], [], [], []
    game_over = False
    level_complete = False
    boss_active = False
    boss_defeated = False
    player_hp = 100.0
    rock_count = 0
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

    # Initial Big Rocks
    num_big_rocks = random.randint(15, 20)
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
    glVertex2f(margin + bx, margin + bz); glEnd()

    # Exit (White)
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EXIT:
                ex = (x * CELL_SIZE / world_max) * map_size
                ez = (z * CELL_SIZE / world_max) * map_size
                glColor3f(1, 1, 1); glPointSize(4); glBegin(GL_POINTS)
                glVertex2f(margin + ex, margin + ez); glEnd()

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
    msg = f"LEVEL 3 | HP: {int(player_hp)}/200 | ROCKS: {rock_count} | BAG: {shield_pill_bag} PILLS | {shield_status}"
    draw_text(20, WINDOW_HEIGHT - 30, msg)
    
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
        raws = "YOU WIN" 
        draw_text(WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2, raws, r=0, g=1, b=0)
        raws2 = "ALL LEVELS PASSED"
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 30, raws2, r=0, g=1, b=0)
        for ch in raws2: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
    glEnable(GL_DEPTH_TEST)


# ==========================================
# 3. Physics & Logic
# ==========================================
def update_physics():
    global player_pos, player_angle, global_time, player_hp, game_over, level_complete, mines, particles, rock_count, thrown_rocks, animals
    global boss_active, boss_obj, boss_defeated, boulders, boss_minions, cheat_mode, cheat_cooldown
    global shield_pill_bag, player_shield_timer, ground_pills, cheat_timer, auto_gun_follow
    global rain_rocks, rain_active_timer, next_rain_trigger, rolling_rocks, display_list, map_data
    
    if game_over or level_complete: return
    global_time += 0.05
    
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
            create_explosion(rr['x'], 2, rr['z'])
            dist_rr = math.sqrt((player_pos[0]-rr['x'])**2 + (player_pos[2]-rr['z'])**2)
            if dist_rr < 30 and player_shield_timer <= 0:
                player_hp -= 20
        else:
            active_rain_rocks.append(rr)
    rain_rocks = active_rain_rocks

    # --- ROLLING ROCKS LOGIC (RANDOM TIME & SPACE SPAWNING) ---
    # Spawn a new big rock at random intervals (approx every 3-5 seconds)
    if random.random() < 0.008: 
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

    # --- UPDATED CHEAT MODE LOGIC ---
    if cheat_mode:
        cheat_timer -= 1
        
        # ALWAYS LOCK ANGLE TO BOSS DURING CHEAT DURATION
        if boss_active:
            vx = boss_obj['x'] - player_pos[0]
            vz = boss_obj['z'] - player_pos[2]
            player_angle = math.atan2(vx, -vz)

        # Forced Constant Movement and Forced Shield
        move_speed = player_speed 
        player_shield_timer = 2 # Keep shield above zero to ensure activation
        
        if cheat_timer <= 0:
            cheat_mode = False
            cheat_cooldown = 240 # 12 second cooldown (240 ticks)
            player_shield_timer = 0 # Deactivate shield immediately
    elif cheat_cooldown > 0:
        cheat_cooldown -= 1
    
    dx = math.sin(player_angle) * move_speed + math.sin(player_angle + 1.57) * strafe
    dz = -math.cos(player_angle) * move_speed - math.cos(player_angle + 1.57) * strafe
    
    nx, nz = player_pos[0] + dx, player_pos[2] + dz
    gx, gz = int(round(nx / CELL_SIZE)), int(round(nz / CELL_SIZE))
    
    # CHECK OBSTACLE COLLISION FOR ROLLING ROCKS
    is_blocked_by_rock = False
    for rr in rolling_rocks:
        dist_to_rock = math.sqrt((nx - rr['x'])**2 + (nz - rr['z'])**2)
        if dist_to_rock < 22: # Obstacle collision radius
            is_blocked_by_rock = True
            if player_shield_timer <= 0: player_hp -= 0.2 # HP decrease on attack/contact
            break

    if not is_blocked_by_rock and 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM and map_data[gx][gz] != C_WALL:
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
        
        # Check hitting rolling rocks (DESTROY ROLLING ROCKS WITH 'L')
        for r_rock in rolling_rocks[:]:
            dist_rr = math.sqrt((r['x']-r_rock['x'])**2 + (r['z']-r_rock['z'])**2)
            if dist_rr < 25:
                create_explosion(r_rock['x'], 15, r_rock['z'])
                rolling_rocks.remove(r_rock)
                hit_impact = True
                break
        
        if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM:
            if map_data[gx][gz] == C_WALL: hit_impact = True
        
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
                        player_hp = min(200.0, player_hp + random.randint(21, 40))
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
    global player_angle, cheat_mode, cheat_timer, cheat_cooldown, auto_gun_follow, player_shield_timer, shield_pill_bag, rock_count, boss_active, boss_obj, boss_defeated, map_data, display_list
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
        if boss_active:
            boss_obj['hp'] -= 100
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
            thrown_rocks.append({'x': player_pos[0], 'y': 25, 'z': player_pos[2], 'vx': math.sin(player_angle) * 8, 'vy': 2, 'vz': -math.cos(player_angle) * 8})

def keyboardUpListener(key, x, y): 
    key_states[key] = False

def specialKeyListener(key, x, y): key_states[key] = True
def specialKeyUpListener(key, x, y): key_states[key] = False

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