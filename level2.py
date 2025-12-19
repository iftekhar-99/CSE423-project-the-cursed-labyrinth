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

# Game Scale
MAP_DIM = 100
CELL_SIZE = 20
WALL_HEIGHT = 50

# Cell Types
C_EMPTY = 0
C_WALL = 1
C_SPIKE = 2
C_PISTON = 3    
C_BOSS_ARENA = 4
C_EXIT = 5

map_data = []

# --- ENTITY LISTS ---
birds = []
projectiles = [] 
player_daggers = []
loot = []
pistons = []    

# --- BOSS STATE ---
boss_obj = {
    'x': 0, 'z': 0, 
    'hp': 5000,          
    'active': False, 
    'dead': False, 
    'shoot_timer': 0     
}

# --- PLAYER STATE ---
player_pos = [0, 20, 0] # x, y, z
player_angle = 1.57     # Yaw (Left/Right)
player_pitch = 0.0      # Pitch (Up/Down)
base_speed = 2.0

# Input State
key_states = {}
modifiers = 0  # To store Shift/Ctrl state

# Stats
player_hp = 100.0
player_ammo = 30
player_stamina = 100.0  
emp_cooldown = 0        
immunity_timer = 0
infinite_stamina_timer = 0

inventory = {
    'immunity': 1,
    'hp_pill': 1,
    'stamina_pill': 1
}

global_time = 0.0
spike_cooldown = 0
game_over = False
level_complete = False
fovY = 60

# ==========================================
# Helper Functions (Strict Intro Style)
# ==========================================

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    # Draws text using standard fixed-pipeline OpenGL
    glColor3f(1, 1, 1)
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

def draw_rect_manual(x, y, w, h, r, g, b):
    # Replaces glRectf with manual quads
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(x, y); glVertex2f(x+w, y); glVertex2f(x+w, y+h); glVertex2f(x, y+h)
    glEnd()

# ==========================================
# 1. Map & Entity Generation
# ==========================================
def generate_level_3():
    global map_data, player_pos, birds, boss_obj, pistons
    global projectiles, player_daggers, loot, player_hp, player_ammo
    global player_stamina, emp_cooldown, immunity_timer, infinite_stamina_timer, inventory, game_over, level_complete

    # Reset Game State
    map_data = [[C_WALL for _ in range(MAP_DIM)] for _ in range(MAP_DIM)]
    birds = []
    projectiles = []
    player_daggers = []
    loot = []
    pistons = []
    
    player_hp = 100
    player_ammo = 30
    player_stamina = 100
    emp_cooldown = 0
    immunity_timer = 0
    infinite_stamina_timer = 0
    inventory = {'immunity': 1, 'hp_pill': 1, 'stamina_pill': 1}
    game_over = False
    level_complete = False

    start_x, start_y = 5, 5
    boss_x, boss_y = MAP_DIM - 10, MAP_DIM - 10

    # Clear Start Area
    for i in range(start_x-2, start_x+3):
        for j in range(start_y-2, start_y+3):
             if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM: map_data[i][j] = C_EMPTY

    # Create "Highway" Path to Boss
    cx, cy = start_x, start_y
    while (abs(cx - boss_x) > 1 or abs(cy - boss_y) > 1):
        # Wide path
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

    # Random Room Mining
    for _ in range(30): 
        rx, ry = random.randint(5, MAP_DIM-5), random.randint(5, MAP_DIM-5)
        life = 150
        while life > 0:
            if 0 < rx < MAP_DIM-1 and 0 < ry < MAP_DIM-1: map_data[rx][ry] = C_EMPTY
            move = random.choice([(0,1), (0,-1), (1,0), (-1,0)]) 
            rx += move[0]; ry += move[1]
            rx = max(2, min(MAP_DIM-3, rx)); ry = max(2, min(MAP_DIM-3, ry))
            life -= 1

    # Place Hazards & Enemies
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_EMPTY:
                dist = math.sqrt((x-start_x)**2 + (z-start_y)**2)
                if dist < 20: continue 

                wx = x * CELL_SIZE
                wz = z * CELL_SIZE
                r = random.random()

                if r < 0.02: loot.append({'x': wx, 'z': wz, 'type': 'AMMO'})
                elif r < 0.04: 
                    map_data[x][z] = C_PISTON
                    pistons.append({'x': wx, 'z': wz, 'offset': random.uniform(0, 6.28)})
                elif r < 0.10: map_data[x][z] = C_SPIKE
                elif r < 0.14: 
                    birds.append({'x': wx, 'y': 35, 'z': wz, 'angle': 0, 'speed': 1.5, 'shoot_timer': random.randint(0,100)})

    # Boss Arena & Exit
    boss_obj['x'] = boss_x * CELL_SIZE
    boss_obj['z'] = boss_y * CELL_SIZE
    boss_obj['hp'] = 5000
    boss_obj['dead'] = False
    
    for i in range(boss_x-8, boss_x+9):
        for j in range(boss_y-8, boss_y+9):
            if 0 <= i < MAP_DIM and 0 <= j < MAP_DIM:
                map_data[i][j] = C_BOSS_ARENA

    map_data[boss_x][boss_y+8] = C_EXIT
    player_pos = [start_x * CELL_SIZE, 20, start_y * CELL_SIZE]

# ==========================================
# 2. Logic & Physics (Game Loop)
# ==========================================

def update_physics():
    global global_time, player_hp, player_ammo, player_stamina, player_angle, player_pitch
    global projectiles, birds, player_daggers, loot, pistons, boss_obj, modifiers
    global spike_cooldown, game_over, level_complete, emp_cooldown, immunity_timer, infinite_stamina_timer
    
    if game_over or level_complete: return

    # --- INPUT MOVEMENT LOGIC ---
    current_speed = base_speed
    
    # Check Shift for Sprint
    # We update 'modifiers' in the key listener, but we also check here
    is_sprinting = (modifiers & GLUT_ACTIVE_SHIFT)

    if is_sprinting and (player_stamina > 0 or infinite_stamina_timer > 0):
        current_speed = base_speed * 2.5 # Swift sprint
        if infinite_stamina_timer <= 0: player_stamina -= 1.0
    else:
        if player_stamina < 100: player_stamina += 0.5

    move_speed = 0
    strafe = 0
    
    # Continuous Movement Checks
    if key_states.get(b'w'): move_speed = current_speed
    if key_states.get(b's'): move_speed = -current_speed
    if key_states.get(b'a'): strafe = -current_speed
    if key_states.get(b'd'): strafe = current_speed

    # Arrow Keys for Camera
    if key_states.get(GLUT_KEY_LEFT): player_angle -= 0.05
    if key_states.get(GLUT_KEY_RIGHT): player_angle += 0.05
    if key_states.get(GLUT_KEY_UP): player_pitch = min(1.0, player_pitch + 0.03)
    if key_states.get(GLUT_KEY_DOWN): player_pitch = max(-1.0, player_pitch - 0.03)

    # Apply Movement
    if move_speed != 0 or strafe != 0:
        dx = math.sin(player_angle) * move_speed
        dz = -math.cos(player_angle) * move_speed
        sdx = math.sin(player_angle + 1.57) * strafe
        sdz = -math.cos(player_angle + 1.57) * strafe
        
        nx = player_pos[0] + dx + sdx
        nz = player_pos[2] + dz + sdz
        
        # Collision
        gx = int(round(nx / CELL_SIZE))
        gz = int(round(nz / CELL_SIZE))
        
        if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM:
            cell = map_data[gx][gz]
            if cell != C_WALL:
                if cell == C_EXIT:
                    if boss_obj['dead']: level_complete = True
                else:
                    player_pos[0] = nx; player_pos[2] = nz

    # --- ENVIRONMENT LOGIC ---
    global_time += 0.05
    if immunity_timer > 0: immunity_timer -= 1
    if emp_cooldown > 0: emp_cooldown -= 1
    if infinite_stamina_timer > 0: infinite_stamina_timer -= 1

    # Hazards
    gx = int(round(player_pos[0] / CELL_SIZE))
    gz = int(round(player_pos[2] / CELL_SIZE))

    # Pistons
    for p in pistons:
        cycle = (global_time * 2 + p['offset'])
        # If piston is down (sin < -0.6) and player is close
        if math.sin(cycle) < -0.6: 
            if math.sqrt((p['x']-player_pos[0])**2 + (p['z']-player_pos[2])**2) < 15 and immunity_timer <= 0:
                player_hp -= 5.0
    
    # Spikes Floor Damage
    if 0 <= gx < MAP_DIM and 0 <= gz < MAP_DIM:
        if map_data[gx][gz] == C_SPIKE and immunity_timer <= 0: player_hp -= 0.5
    
    # Spike Shooting Logic
    spike_cooldown += 1
    if spike_cooldown > 50: 
        spike_cooldown = 0
        for x in range(MAP_DIM):
            for z in range(MAP_DIM):
                if map_data[x][z] == C_SPIKE:
                    wx, wz = x*CELL_SIZE, z*CELL_SIZE
                    # If player is near spike
                    if math.sqrt((wx-player_pos[0])**2 + (wz-player_pos[2])**2) < 150:
                        rad = math.atan2(player_pos[0]-wx, player_pos[2]-wz)
                        projectiles.append({'x': wx, 'z': wz, 'dx': math.sin(rad)*1.5, 'dz': math.cos(rad)*1.5, 'life': 80})

    # Bird AI
    for b in birds:
        b['x'] += math.sin(b['angle']) * b['speed']
        b['z'] += math.cos(b['angle']) * b['speed']
        # Random change direction
        if random.random() < 0.05: b['angle'] += random.uniform(-0.5, 0.5)
        
        b['shoot_timer'] += 1
        # Shoot at player
        if b['shoot_timer'] > 100 and math.sqrt((b['x']-player_pos[0])**2 + (b['z']-player_pos[2])**2) < 300:
            b['shoot_timer'] = 0
            aim = math.atan2(player_pos[0] - b['x'], player_pos[2] - b['z'])
            projectiles.append({'x': b['x'], 'z': b['z'], 'dx': math.sin(aim)*2.5, 'dz': math.cos(aim)*2.5, 'life': 100})

    # Boss AI
    if not boss_obj['dead'] and math.sqrt((boss_obj['x']-player_pos[0])**2 + (boss_obj['z']-player_pos[2])**2) < 600:
        boss_obj['shoot_timer'] += 1
        if boss_obj['shoot_timer'] > 60:
            boss_obj['shoot_timer'] = 0
            # 8-way shot
            for i in range(8):
                angle = (i * 45) * (math.pi / 180)
                projectiles.append({'x': boss_obj['x'], 'z': boss_obj['z'], 'dx': math.sin(angle)*3.0, 'dz': math.cos(angle)*3.0, 'life': 150})

    # Update Enemy Projectiles
    active_projs = []
    for p in projectiles:
        p['x'] += p['dx']; p['z'] += p['dz']; p['life'] -= 1
        # Player Hit
        if math.sqrt((p['x']-player_pos[0])**2 + (p['z']-player_pos[2])**2) < 10 and immunity_timer <= 0:
            player_hp -= 5; p['life'] = 0
        # Wall Hit
        pgx, pgz = int(p['x']/CELL_SIZE), int(p['z']/CELL_SIZE)
        if 0 <= pgx < MAP_DIM and 0 <= pgz < MAP_DIM and map_data[pgx][pgz] == C_WALL: p['life'] = 0
        
        if p['life'] > 0: active_projs.append(p)
    projectiles = active_projs

    # Update Player Daggers
    active_daggers = []
    for d in player_daggers:
        d['x'] += math.sin(d['angle'])*8; d['z'] -= math.cos(d['angle'])*8; d['life'] -= 1
        hit = False
        
        # Hit Bird
        for b in birds:
            if not hit and math.sqrt((d['x']-b['x'])**2 + (d['z']-b['z'])**2) < 15:
                birds.remove(b); hit = True; loot.append({'x':b['x'], 'z':b['z'], 'type': 'AMMO'})
        
        # Hit Boss
        if not hit and not boss_obj['dead']:
            if math.sqrt((d['x']-boss_obj['x'])**2 + (d['z']-boss_obj['z'])**2) < 30:
                boss_obj['hp'] -= 50; hit = True
                if boss_obj['hp'] <= 0: boss_obj['dead'] = True
        
        # Hit Walls/Spikes (destroy spikes)
        dgx, dgz = int(round(d['x']/CELL_SIZE)), int(round(d['z']/CELL_SIZE))
        if 0 <= dgx < MAP_DIM and 0 <= dgz < MAP_DIM:
            if map_data[dgx][dgz] == C_SPIKE:
                map_data[dgx][dgz] = C_EMPTY; hit = True
                # Drop random loot
                r = random.random()
                if r < 0.4: loot.append({'x':d['x'], 'z':d['z'], 'type': 'HP_PILL'})
                elif r < 0.6: loot.append({'x':d['x'], 'z':d['z'], 'type': 'IMMUNITY'})
                elif r < 0.8: loot.append({'x':d['x'], 'z':d['z'], 'type': 'STAMINA_PILL'})
                else: loot.append({'x':d['x'], 'z':d['z'], 'type': 'AMMO'})

        if not hit and d['life'] > 0: active_daggers.append(d)
    player_daggers = active_daggers

    # Update Loot Collection
    active_loot = []
    for l in loot:
        if math.sqrt((player_pos[0]-l['x'])**2 + (player_pos[2]-l['z'])**2) < 20: 
            if l['type'] == 'AMMO': player_ammo += 10 
            elif l['type'] == 'HP_PILL': inventory['hp_pill'] += 1
            elif l['type'] == 'IMMUNITY': inventory['immunity'] += 1
            elif l['type'] == 'STAMINA_PILL': inventory['stamina_pill'] += 1
        else: active_loot.append(l)
    loot = active_loot
    
    if player_hp <= 0: game_over = True

# ==========================================
# 3. Drawing Functions
# ==========================================

def draw_shapes():
    # --- Draw Map Elements ---
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            cell = map_data[x][z]
            wx = x * CELL_SIZE
            wz = z * CELL_SIZE

            # Distance Culling (Don't draw far away things)
            if abs(wx - player_pos[0]) > 600 or abs(wz - player_pos[2]) > 600: continue

            if cell == C_WALL:
                glPushMatrix()
                glTranslatef(wx, WALL_HEIGHT/2, wz)
                glScalef(1, WALL_HEIGHT/CELL_SIZE, 1)
                glColor3f(0.4, 0.2, 0.1); glutSolidCube(CELL_SIZE) 
                glColor3f(0.2, 0.2, 0.2); glutWireCube(CELL_SIZE)
                glPopMatrix()
            
            elif cell in [C_EMPTY, C_SPIKE, C_PISTON, C_BOSS_ARENA]:
                # Floor Pattern
                if (x+z)%2 == 0: glColor3f(0.5, 0.5, 0.55)
                else: glColor3f(0.45, 0.45, 0.5)
                glBegin(GL_QUADS)
                glVertex3f(wx-10, 0, wz-10); glVertex3f(wx+10, 0, wz-10)
                glVertex3f(wx+10, 0, wz+10); glVertex3f(wx-10, 0, wz+10)
                glEnd()

            elif cell == C_EXIT:
                glPushMatrix()
                glTranslatef(wx, 15, wz)
                glColor3f(1.0, 0.8, 0.0) 
                glutSolidTorus(4, 10, 10, 10) # Gold Exit Ring
                glPopMatrix()

    # --- Draw Pistons ---
    for p in pistons:
        cycle = (global_time * 2 + p['offset'])
        height_val = math.sin(cycle) 
        draw_y = 35 + (height_val * 25)
        glPushMatrix(); glTranslatef(p['x'], draw_y, p['z'])
        glColor3f(0.3, 0.3, 0.3); glScalef(1, 2, 1); glutSolidCube(18)
        glPopMatrix()

    # --- Draw Spikes ---
    spike_h = abs(math.sin(global_time * 3)) * 15
    glColor3f(0.5, 0.5, 0.5)
    for x in range(MAP_DIM):
        for z in range(MAP_DIM):
            if map_data[x][z] == C_SPIKE:
                wx = x * CELL_SIZE; wz = z * CELL_SIZE
                if abs(wx - player_pos[0]) > 600 or abs(wz - player_pos[2]) > 600: continue
                glPushMatrix(); glTranslatef(wx, spike_h, wz); glRotatef(-90, 1, 0, 0)
                glutSolidCone(4, 15, 6, 2)
                glPopMatrix()

    # --- Draw Birds ---
    for b in birds:
        glPushMatrix(); glTranslatef(b['x'], b['y'], b['z']); glRotatef(math.degrees(-b['angle']), 0, 1, 0)
        glColor3f(0.9, 0.2, 0.2) 
        glPushMatrix(); glScalef(1, 0.5, 2); glutSolidCube(4); glPopMatrix()
        glPopMatrix()

    # --- Draw Projectiles ---
    for p in projectiles:
        glPushMatrix(); glTranslatef(p['x'], 15, p['z']); 
        glColor3f(1.0, 0.5, 0.0); glutSolidSphere(2, 5, 5); glPopMatrix()

    # --- Draw Daggers ---
    glColor3f(0, 1, 1)
    for d in player_daggers:
        glPushMatrix(); glTranslatef(d['x'], d['y'], d['z']); glRotatef(math.degrees(-d['angle']), 0, 1, 0)
        glutSolidCone(1, 5, 5, 5)
        glPopMatrix()

    # --- Draw Loot ---
    for l in loot:
        glPushMatrix(); glTranslatef(l['x'], 10, l['z']); glRotatef(global_time * 50, 0, 1, 0)
        if l['type'] == 'AMMO': glColor3f(0.7, 0.7, 0.7); glutSolidCone(3, 8, 6, 6)
        elif l['type'] == 'HP_PILL': glColor3f(1, 0, 0); glutSolidSphere(4, 8, 8)
        elif l['type'] == 'IMMUNITY': glColor3f(0.8, 0, 1); glutSolidCube(6)
        elif l['type'] == 'STAMINA_PILL': glColor3f(0, 1, 0); glutSolidCube(5)
        glPopMatrix()

    # --- Draw Boss ---
    if not boss_obj['dead']:
        glPushMatrix()
        glTranslatef(boss_obj['x'], 30, boss_obj['z'])
        glPushMatrix(); glColor3f(0.8, 0, 0); glScalef(2, 2, 2); glutSolidCube(15); glPopMatrix()
        glPushMatrix(); glColor3f(0.2, 0, 0); glutSolidSphere(12, 10, 10); glPopMatrix()
        # Rotating Shields
        glPushMatrix(); glRotatef(global_time * 60, 0, 1, 0)
        for i in range(4):
            glPushMatrix(); glRotatef(i * 90, 0, 1, 0); glTranslatef(35, 0, 0); glColor3f(0.4, 0.4, 0.4); glutSolidCube(8); glPopMatrix()
        glPopMatrix(); glPopMatrix()

    # --- EMP Visual ---
    if emp_cooldown > 480:
        scale = (500 - emp_cooldown) * 2
        glColor3f(0.0, 1.0, 1.0)
        glPushMatrix(); glTranslatef(player_pos[0], 20, player_pos[2]); glRotatef(90, 1, 0, 0)
        glutWireTorus(2, scale, 10, 20)
        glPopMatrix()

def draw_hud():
    # --- HUD Info ---
    draw_text(20, WINDOW_HEIGHT - 30, f"HP: {int(player_hp)} | AMMO: {player_ammo}")
    draw_text(20, WINDOW_HEIGHT - 60, f"[1] IMMUNITY: {inventory['immunity']} | [2] HP: {inventory['hp_pill']} | [3] STAMINA: {inventory['stamina_pill']}")
    
    status_y = 90
    if immunity_timer > 0:
        draw_text(20, WINDOW_HEIGHT - status_y, "IMMUNITY ACTIVE!")
        status_y += 20
    if infinite_stamina_timer > 0:
        draw_text(20, WINDOW_HEIGHT - status_y, "INFINITE STAMINA!")

    if emp_cooldown <= 0:
        draw_text(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 30, "EMP READY [E]")
    else:
        draw_text(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 30, "EMP RECHARGING...")

    # --- Stamina Bar ---
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    
    draw_rect_manual(20, WINDOW_HEIGHT-120, 100, 10, 0.2, 0.2, 0.2)
    draw_rect_manual(20, WINDOW_HEIGHT-120, player_stamina, 10, 0, 1, 1)
    
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    
    draw_text(130, WINDOW_HEIGHT - 118, "STAMINA (Shift)")

    if game_over:
        draw_text(WINDOW_WIDTH//2 - 40, WINDOW_HEIGHT//2, "GAME OVER (Press R)")
    if level_complete:
        draw_text(WINDOW_WIDTH//2 - 60, WINDOW_HEIGHT//2, "LEVEL COMPLETE! (Press R)")

def draw_minimap():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    ms = 150; mx = 20; my = 20
    draw_rect_manual(mx, my, ms, ms, 0, 0, 0) # Background
    
    world_max = MAP_DIM * CELL_SIZE
    px = (player_pos[0]/world_max)*ms; pz = (player_pos[2]/world_max)*ms
    
    draw_rect_manual(mx+px-3, my+pz-3, 6, 6, 0, 0.6, 1) # Player
    
    if not boss_obj['dead']:
        bx = (boss_obj['x']/world_max)*ms; bz = (boss_obj['z']/world_max)*ms
        draw_rect_manual(mx+bx-4, my+bz-4, 8, 8, 1, 0, 0) # Boss

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

# ==========================================
# Input Listeners
# ==========================================

def keyboardListener(key, x, y):
    global player_hp, inventory, immunity_timer, infinite_stamina_timer, player_stamina, emp_cooldown, projectiles, game_over, modifiers
    
    # Store key for continuous movement
    try:
        key_states[key] = True
        key_states[key.lower()] = True
    except:
        pass
        
    # Detect modifiers (Shift for Sprint)
    modifiers = glutGetModifiers()

    # --- Single Press Actions ---
    if key == b'r':
        generate_level_3()
        return

    # Inventory
    if key == b'1' and inventory['immunity'] > 0 and immunity_timer <= 0:
        inventory['immunity'] -= 1; immunity_timer = 300
    if key == b'2' and inventory['hp_pill'] > 0 and player_hp < 100:
        inventory['hp_pill'] -= 1; player_hp = min(100, player_hp + 20)
    if key == b'3' and inventory['stamina_pill'] > 0:
        inventory['stamina_pill'] -= 1; infinite_stamina_timer = 300; player_stamina = 100
    # EMP
    if key == b'e' and emp_cooldown <= 0:
        emp_cooldown = 500; projectiles = []

def keyboardUpListener(key, x, y):
    try:
        key_states[key] = False
        key_states[key.lower()] = False
    except:
        pass
    
    # Update modifiers on release too
    global modifiers
    modifiers = glutGetModifiers()

def specialKeyListener(key, x, y):
    # Store Arrow Keys
    key_states[key] = True

def specialUpListener(key, x, y):
    key_states[key] = False

def mouseListener(button, state, x, y):
    global player_ammo
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over and player_ammo > 0:
        player_ammo -= 1
        player_daggers.append({'x': player_pos[0], 'y': 20, 'z': player_pos[2], 'angle': player_angle, 'life': 50})

# ==========================================
# Core Loop
# ==========================================

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Third person / First person hybrid
    look_distance = 100
    lx = player_pos[0] + math.sin(player_angle) * look_distance * math.cos(player_pitch)
    lz = player_pos[2] - math.cos(player_angle) * look_distance * math.cos(player_pitch)
    ly = 20 + (math.sin(player_pitch) * look_distance)
    
    gluLookAt(player_pos[0], 20, player_pos[2], lx, ly, lz, 0, 1, 0)

def idle():
    # Continual updates for smooth movement
    update_physics()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setupCamera()
    
    draw_shapes()
    
    glDisable(GL_DEPTH_TEST)
    draw_minimap()
    draw_hud()
    glEnable(GL_DEPTH_TEST)

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Level 3: Gauntlet (Final)")

    glEnable(GL_DEPTH_TEST)

    generate_level_3()

    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    
    # Register all listeners for smooth input
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutSpecialUpFunc(specialUpListener)
    glutMouseFunc(mouseListener)

    glutMainLoop()

if __name__ == "__main__":
    main()