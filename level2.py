from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random

# ==========================================
# Global Configuration
# ==========================================
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

# --- ENTITY LISTS ---
birds = []
moving_enemies = []
projectiles = []
player_bullets = []
drops = []
respawning_spikes = []

# --- GAME STATE ---
player_pos = [0, 20, 0]
player_angle = 1.57
player_pitch = 0.0

# Speed settings
base_speed = 0.8       
rotation_speed = 0.03   

key_states = {}
shift_held = False 

player_hp = 300.0
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

# ==========================================
# Helper Functions
# ==========================================
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

# ==========================================
# Map Generation
# ==========================================
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
    
    player_hp = 300.0
    player_stamina = 100.0
    player_ammo = 50
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

    # Clear Start
    for i in range(start_x-2, start_x+3):
        for j in range(start_y-2, start_y+3):
            if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM: map_data[i][j] = C_EMPTY

    # Path to Boss
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

    # Rooms
    for _ in range(40):
        rx, ry = random.randint(5, MAP_DIM-5), random.randint(5, MAP_DIM-5)
        life = 100
        while life > 0:
            if 0 < rx < MAP_DIM-1 and 0 < ry < MAP_DIM-1: map_data[rx][ry] = C_EMPTY
            move = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
            rx += move[0]; ry += move[1]
            rx = max(2, min(MAP_DIM-3, rx)); ry = max(2, min(MAP_DIM-3, ry))
            life -= 1

    # Boss Arena
    for i in range(boss_x-8, boss_x+9):
        for j in range(boss_y-8, boss_y+9):
            if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM: map_data[i][j] = C_BOSS_ARENA
    map_data[boss_x][boss_y+8] = C_EXIT

    # Entities
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
                elif r < 0.07:
                    birds.append({
                        'x': wx, 'y': 35, 'z': wz, 
                        'cx': wx, 'cz': wz,
                        'angle': random.random()*6.28, 
                        'radius': random.randint(20, 60),
                        'speed': random.choice([0.02, -0.02]),
                        'drop_timer': random.randint(100, 500)
                    })

    boss['x'] = boss_x * CELL_SIZE
    boss['z'] = boss_y * CELL_SIZE
    boss['hp'] = 10
    boss['active'] = False
    boss['dead'] = False
    boss['stage'] = 1
    
    player_pos = [start_x * CELL_SIZE, 20, start_y * CELL_SIZE]

# ==========================================
# Logic
# ==========================================
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
    if key_states.get(GLUT_KEY_UP): player_pitch = max(-1.0, min(1.0, player_pitch - 0.02))
    if key_states.get(GLUT_KEY_DOWN): player_pitch = max(-1.0, min(1.0, player_pitch + 0.02))
    
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
             if math.sin(global_time * 2) > 0: player_hp -= 1.0

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
            if is_walkable(e['x'] - vx, e['z']): e['x'] -= vx
            if is_walkable(e['x'], e['z'] - vz): e['z'] -= vz
        
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
            b['drop_timer'] = random.randint(300, 800)
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
        if 0 <= mx < MAP_DIM and 0 <= mz < MAP_DIM:
            if map_data[mx][mz] == C_SPIKE_HIDDEN:
                map_data[mx][mz] = C_EMPTY
                respawning_spikes.append({'x': mx, 'z': mz, 'timer': 600})
                hit = True
                r = random.random()
                if r < 0.4: drops.append({'x': mx*CELL_SIZE, 'z': mz*CELL_SIZE, 'y': 5, 'type': 'DIAMOND'})
                elif r < 0.6: drops.append({'x': mx*CELL_SIZE, 'z': mz*CELL_SIZE, 'y': 5, 'type': 'AMMO'})
            elif map_data[mx][mz] == C_WALL:
                hit = True
        
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

# ==========================================
# Drawing
# ==========================================
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

# [NEW] Fancy Boss Drawing
def draw_boss_fancy(b):
    glPushMatrix()
    glTranslatef(b['x'], 30, b['z'])
    
    # Global boss animation (bobbing + spinning)
    glTranslatef(0, math.sin(global_time * 3) * 5, 0)
    glRotatef(global_time * 30, 0, 1, 0)

    if b['stage'] == 1:
        # --- STAGE 1: IRON FORTRESS ---
        glColor3f(0.8, 0.1, 0.1) # Red Body
        glutSolidCube(30)
        
        # Metallic corners
        glColor3f(0.4, 0.4, 0.4)
        for dx in [-15, 15]:
            for dy in [-15, 15]:
                for dz in [-15, 15]:
                    glPushMatrix()
                    glTranslatef(dx, dy, dz)
                    gluSphere(gluNewQuadric(), 5, 8, 8)
                    glPopMatrix()
        
        # Gold Spikes
        glColor3f(1.0, 0.8, 0.0)
        for r in [0, 90, 180, 270]:
            glPushMatrix()
            glRotatef(r, 0, 1, 0)
            glTranslatef(0, 0, 15)
            gluCylinder(gluNewQuadric(), 8, 0, 20, 8, 2)
            glPopMatrix()

    else:
        # --- STAGE 2: ALIEN MOTHERSHIP ---
        # Dark Matter Core
        glColor3f(0.2, 0.0, 0.8)
        gluSphere(gluNewQuadric(), 18, 15, 15)
        
        # Spinning Energy Ring
        glColor3f(0.0, 1.0, 1.0)
        glPushMatrix()
        glRotatef(global_time * 100, 0, 1, 0)
        for i in range(8):
            glPushMatrix()
            glRotatef(i * 45, 0, 1, 0)
            glTranslatef(25, 0, 0)
            glutSolidCube(6)
            glPopMatrix()
        glPopMatrix()
        
        # Vertical Beam
        glColor3f(1.0, 0.0, 1.0)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glTranslatef(0, 0, -30)
        gluCylinder(gluNewQuadric(), 2, 2, 60, 6, 1)
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
                glColor3f(0.4, 0.2, 0.1); glutSolidCube(CELL_SIZE)
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
                    h = max(0, math.sin(global_time * 2) * 15)
                    glColor3f(0.5, 0.5, 0.5)
                    glPushMatrix()
                    glTranslatef(wx, h, wz); glRotatef(-90, 1, 0, 0)
                    gluCylinder(gluNewQuadric(), 4, 0, 15, 6, 2) 
                    glPopMatrix()

    for e in moving_enemies:
        draw_enemy(e)

    for b in birds:
        draw_bird(b)

    # [UPDATED] Call new fancy boss function
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
    if level_complete: draw_text_2d(WINDOW_WIDTH//2-60, WINDOW_HEIGHT//2, "VICTORY (R)")

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
    glutCreateWindow(b"Task 1 Final Funky Boss")
    
    glutIgnoreKeyRepeat(GL_TRUE)
    
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
