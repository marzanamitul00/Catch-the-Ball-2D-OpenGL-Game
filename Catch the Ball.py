from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ─────────────────────────────────────────────
#  Global State
# ─────────────────────────────────────────────
WIN_W       = 600
WIN_H       = 600

# Paddle
paddle_x    = 0.0          # centre x  (-1 to 1)
paddle_y    = -0.85        # fixed bottom
PADDLE_W    = 0.30
PADDLE_H    = 0.05

# Ball
ball_x      = 0.0
ball_y      = 0.6
ball_dx     = 0.012
ball_dy     = -0.018
BALL_R      = 0.045

# Score / lives
score       = 0
lives       = 3
game_over   = False
paused      = False

# Features
fog_on      = False
blend_on    = True

# ─────────────────────────────────────────────
#  Drawing Helpers
# ─────────────────────────────────────────────

def draw_circle(cx, cy, r, slices=48):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(slices + 1):
        t = 2.0 * math.pi * i / slices
        glVertex2f(cx + r * math.cos(t), cy + r * math.sin(t))
    glEnd()


def draw_glow(cx, cy, r, color, layers=5):
    """Blending — soft glow ring around ball."""
    for i in range(layers, 0, -1):
        alpha  = 0.07 * i / layers
        radius = r + (layers - i + 1) * 0.022
        glColor4f(color[0], color[1], color[2], alpha)
        draw_circle(cx, cy, radius)


def draw_rect(x, y, w, h):
    """Filled rectangle centred at (x,y)."""
    glBegin(GL_QUADS)
    glVertex2f(x - w, y - h)
    glVertex2f(x + w, y - h)
    glVertex2f(x + w, y + h)
    glVertex2f(x - w, y + h)
    glEnd()


def draw_text(x, y, text, font=GLUT_BITMAP_9_BY_15):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))


# ─────────────────────────────────────────────
#  Draw Paddle  (shading: bright top → dark bottom)
# ─────────────────────────────────────────────

def draw_paddle():
    x, y = paddle_x, paddle_y
    w, h = PADDLE_W, PADDLE_H

    # Glow under paddle
    if blend_on:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        draw_glow(x, y, w * 0.5, (0.3, 0.8, 1.0), layers=4)

    # Paddle body — Gouraud shading via vertex colours
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.9, 1.0)        # bright top-left
    glVertex2f(x - w, y + h)
    glColor3f(0.2, 0.9, 1.0)        # bright top-right
    glVertex2f(x + w, y + h)
    glColor3f(0.0, 0.4, 0.6)        # dark bottom-right  ← shading
    glVertex2f(x + w, y - h)
    glColor3f(0.0, 0.4, 0.6)        # dark bottom-left
    glVertex2f(x - w, y - h)
    glEnd()

    if blend_on:
        glDisable(GL_BLEND)


# ─────────────────────────────────────────────
#  Draw Ball  (shading + glow)
# ─────────────────────────────────────────────

def draw_ball():
    if blend_on:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        draw_glow(ball_x, ball_y, BALL_R, (1.0, 0.4, 0.1))

    # Ball body — bright centre → dark rim (shading)
    glBegin(GL_TRIANGLE_FAN)
    glColor3f(1.0, 0.95, 0.5)       # bright centre
    glVertex2f(ball_x, ball_y)
    slices = 48
    for i in range(slices + 1):
        t = 2.0 * math.pi * i / slices
        glColor3f(0.9, 0.25, 0.0)   # dark orange rim
        glVertex2f(ball_x + BALL_R * math.cos(t),
                   ball_y + BALL_R * math.sin(t))
    glEnd()

    if blend_on:
        glDisable(GL_BLEND)


# ─────────────────────────────────────────────
#  Draw Background grid
# ─────────────────────────────────────────────

def draw_background():
    glColor3f(0.08, 0.08, 0.15)
    draw_rect(0.0, 0.0, 1.0, 1.0)

    if blend_on:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glColor4f(0.2, 0.2, 0.4, 0.25)
    glLineWidth(0.5)
    glBegin(GL_LINES)
    for i in range(-10, 11):
        x = i * 0.1
        glVertex2f(x, -1.0); glVertex2f(x, 1.0)
        glVertex2f(-1.0, x); glVertex2f(1.0, x)
    glEnd()

    if blend_on:
        glDisable(GL_BLEND)


# ─────────────────────────────────────────────
#  HUD — score, lives, controls
# ─────────────────────────────────────────────

def draw_hud():
    glColor3f(0.9, 0.9, 0.9)
    draw_text(-0.98,  0.90, f"Score: {score}")
    draw_text( 0.55,  0.90, f"Lives: {'O ' * lives}")

    glColor3f(0.5, 0.5, 0.6)
    draw_text(-0.98, -0.97, "A/D or Mouse: move   F:fog   B:blend   P:pause   R:restart")

    if paused:
        glColor3f(1.0, 0.8, 0.0)
        draw_text(-0.12, 0.05, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)

    if game_over:
        glColor3f(1.0, 0.2, 0.2)
        draw_text(-0.28, 0.10, "GAME  OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        glColor3f(0.9, 0.9, 0.9)
        draw_text(-0.22, -0.05, f"Final Score: {score}")
        draw_text(-0.18, -0.15, "Press R to restart")


# ─────────────────────────────────────────────
#  Fog
# ─────────────────────────────────────────────

def apply_fog():
    if fog_on:
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE,  GL_LINEAR)
        glFogf(GL_FOG_START, 0.2)
        glFogf(GL_FOG_END,   1.5)
        glFogfv(GL_FOG_COLOR, [0.08, 0.08, 0.15, 1.0])
        glHint(GL_FOG_HINT,  GL_NICEST)
    else:
        glDisable(GL_FOG)


# ─────────────────────────────────────────────
#  Game Logic
# ─────────────────────────────────────────────

def reset_game():
    global ball_x, ball_y, ball_dx, ball_dy
    global score, lives, game_over, paused
    ball_x   = random.uniform(-0.5, 0.5)
    ball_y   = 0.6
    ball_dx  = random.choice([-1, 1]) * 0.010
    ball_dy  = -0.013
    score    = 0
    lives    = 3
    game_over = False
    paused   = False


def update_ball():
    global ball_x, ball_y, ball_dx, ball_dy
    global score, lives, game_over

    if paused or game_over:
        return

    ball_x += ball_dx
    ball_y += ball_dy

    # Wall bounce (left / right)
    if ball_x - BALL_R < -1.0 or ball_x + BALL_R > 1.0:
        ball_dx = -ball_dx

    # Ceiling bounce
    if ball_y + BALL_R > 1.0:
        ball_dy = -ball_dy

    # Paddle collision
    if (ball_y - BALL_R < paddle_y + PADDLE_H and
        ball_y + BALL_R > paddle_y - PADDLE_H and
        ball_x > paddle_x - PADDLE_W and
        ball_x < paddle_x + PADDLE_W and
        ball_dy < 0):
        ball_dy = -ball_dy
        score  += 1
        # Speed up slightly every 5 catches
        if score % 5 == 0:
            ball_dx *= 1.08
            ball_dy *= 1.08

    # Ball fell below screen
    if ball_y - BALL_R < -1.0:
        lives -= 1
        if lives <= 0:
            game_over = True
        else:
            ball_x  = random.uniform(-0.5, 0.5)
            ball_y  = 0.6
            ball_dx = random.choice([-1, 1]) * 0.010
            ball_dy = -0.013


# ─────────────────────────────────────────────
#  GLUT Callbacks
# ─────────────────────────────────────────────

def show_screen():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    apply_fog()

    draw_background()
    draw_paddle()
    draw_ball()
    draw_hud()

    glFlush()


def timer(value):
    update_ball()
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)      # ~60 fps


def keyboard(key, x, y):
    global paddle_x, fog_on, blend_on, paused
    step = 0.07

    if key == b'a' or key == b'A':
        paddle_x = max(paddle_x - step, -1.0 + PADDLE_W)
    elif key == b'd' or key == b'D':
        paddle_x = min(paddle_x + step,  1.0 - PADDLE_W)
    elif key == b'f':
        fog_on   = not fog_on
    elif key == b'b':
        blend_on = not blend_on
    elif key == b'p' or key == b' ':
        if not game_over:
            paused = not paused
    elif key == b'r' or key == b'R':
        reset_game()
    elif key == b'\x1b':             # ESC
        import sys; sys.exit(0)

    glutPostRedisplay()


def special_key(key, x, y):
    """Arrow keys also move paddle."""
    global paddle_x
    step = 0.07
    if key == GLUT_KEY_LEFT:
        paddle_x = max(paddle_x - step, -1.0 + PADDLE_W)
    elif key == GLUT_KEY_RIGHT:
        paddle_x = min(paddle_x + step,  1.0 - PADDLE_W)
    glutPostRedisplay()


def mouse(button, state, x, y):
    """Click to snap paddle."""
    global paddle_x
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        paddle_x = (x / (WIN_W / 2.0)) - 1.0
        paddle_x = max(-1.0 + PADDLE_W, min(1.0 - PADDLE_W, paddle_x))
    glutPostRedisplay()


def mouse2(x, y):
    """Drag paddle with mouse."""
    global paddle_x
    paddle_x = (x / (WIN_W / 2.0)) - 1.0
    paddle_x = max(-1.0 + PADDLE_W, min(1.0 - PADDLE_W, paddle_x))
    glutPostRedisplay()


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

reset_game()

glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_SINGLE)
glutInitWindowSize(WIN_W, WIN_H)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Catch the Ball  |  OpenGL 2D Game")

glEnable(GL_LINE_SMOOTH)
glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

glutDisplayFunc(show_screen)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_key)
glutMouseFunc(mouse)
glutMotionFunc(mouse2)
glutTimerFunc(16, timer, 0)

glutMainLoop()
