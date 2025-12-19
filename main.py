from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys

# Import the level modules
# (Assumes files are named level1.py, level2.py, level3.py)
import level1
import level2
import level3

# ==========================================
# Global Configuration
# ==========================================
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

# State Management
current_level = 1

def init_game():
    """ Initial setup and starting Level 1 """
    # Set basic OpenGL states shared by all levels
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Start Level 1
    print("Starting Level 1: The Maze...")
    level1.generate_level_1()

# ==========================================
# Transition Logic
# ==========================================
def transition_to_level_2():
    global current_level
    print("\n>>> LEVEL 1 COMPLETE! ENTERING LEVEL 2: THE IRON GAUNTLET <<<")
    
    # 1. Capture Data from Level 1
    # We carry over HP to maintain continuity difficulty
    saved_hp = level1.player_hp
    
    # 2. Initialize Level 2
    level2.generate_level_2()
    
    # 3. Inject Persistence Data
    level2.player_hp = saved_hp
    
    # 4. Switch State
    current_level = 2

def transition_to_level_3():
    global current_level
    print("\n>>> LEVEL 2 COMPLETE! ENTERING LEVEL 3: THE FINAL STAND <<<")
    
    # 1. Capture Data from Level 2
    saved_hp = level2.player_hp
    
    # 2. Initialize Level 3
    level3.generate_level_3()
    
    # 3. Inject Persistence Data
    level3.player_hp = saved_hp
    
    # 4. Switch State
    current_level = 3

# ==========================================
# Master Callbacks
# ==========================================
def showScreen():
    """ 
    Master Renderer: Delegates drawing to the active level.
    """
    if current_level == 1:
        level1.showScreen()
    elif current_level == 2:
        level2.showScreen()
    elif current_level == 3:
        level3.showScreen()

def idle():
    """
    Master Logic Loop: Handles updates and checks for level completion.
    """
    global current_level
    
    if current_level == 1:
        level1.idle()
        # Check Transition Condition
        if level1.level_complete:
            transition_to_level_2()
            
    elif current_level == 2:
        level2.idle()
        # Check Transition Condition
        if level2.level_complete:
            transition_to_level_3()
            
    elif current_level == 3:
        level3.idle()
        # Win Condition Logic
        if level3.level_complete:
            # Just let Level 3 show its "Tank Defeated" text, 
            # or we could add a global win screen here.
            pass

# ==========================================
# Input Routing
# ==========================================
def keyDown(key, x, y):
    if current_level == 1: level1.keyDown(key, x, y)
    elif current_level == 2: level2.keyDown(key, x, y)
    elif current_level == 3: level3.keyDown(key, x, y)

def keyUp(key, x, y):
    if current_level == 1: level1.keyUp(key, x, y)
    elif current_level == 2: level2.keyUp(key, x, y)
    elif current_level == 3: level3.keyUp(key, x, y)

def specialDown(key, x, y):
    if current_level == 1: level1.specialDown(key, x, y)
    elif current_level == 2: level2.specialDown(key, x, y)
    elif current_level == 3: level3.specialDown(key, x, y)

def specialUp(key, x, y):
    if current_level == 1: level1.specialUp(key, x, y)
    elif current_level == 2: level2.specialUp(key, x, y)
    elif current_level == 3: level3.specialUp(key, x, y)

def mouseListener(button, state, x, y):
    if current_level == 1: level1.mouseListener(button, state, x, y)
    elif current_level == 2: level2.mouseListener(button, state, x, y)
    elif current_level == 3: level3.mouseListener(button, state, x, y)

# ==========================================
# Main Execution
# ==========================================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"The Survivor: Complete Saga")
    
    init_game()
    
    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    
    # Register Input Callbacks
    glutKeyboardFunc(keyDown)
    glutKeyboardUpFunc(keyUp)
    glutSpecialFunc(specialDown)
    glutSpecialUpFunc(specialUp)
    glutMouseFunc(mouseListener)
    
    glutMainLoop()

if __name__ == "__main__":
    main()