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