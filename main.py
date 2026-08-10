from ursina import *
from direct.actor.Actor import Actor
import random
from pypresence import Presence
import time
import math
from collections import Counter
import json

client_id = '1535037932828889178' #for discord rpc

RPC = Presence(client_id)
RPC.connect()

start_time = time.time()
last_rpc_update = 0
update_interval = 15

with open("data.json", "r") as file:
        data = json.load(file)
        string_list = data.get("messages", [])

app = Ursina()
player = Entity(model='assets/farmer.obj', texture='lambert1_albedo', scale=(0.5), position=(0, 1, 0), collider='box') #his name is timmy, and he likes redbull
sky = Sky(texture='sky_sunset')
ground = Entity(model='plane', texture='grass_tintable', color=Color(1, 1, 0.3, 1), scale=(50, 50, 50), texture_scale=(1, 1))
bg_music = None

hedgeL = Entity(model='cube', texture='grass', scale=(1, 3, 50), position=(-5, 0, 0))
hedgeR = Entity(model='cube', texture='grass', scale=(1, 3, 50), position=(5, 0, 0))

obstacle1 = Entity(model='assets/pol.obj', texture="2015_Ranger_Pol_d", position=(3, 1, 50), scale=(1.5), rotation=(0, 180, 0), collider='box') #u can jump over
obstacle2 = Entity(model='assets/fence.obj', position=(-3, 1, 10), scale=(0.15), rotation=(0, 180, 0), color=color.dark_gray, collider='box') #u can crouch under
obstacle3 = Entity(model='assets/school bus.obj', texture='busdiffuse.png', position=(0, 1, 20), scale=(3), rotation=(0, 180, 0), collider='box') #u need to go around
speedcamera = Entity(model='assets/SpeedCam.obj', texture='SpeedCam.png', position=(6, 0, 30), rotation=(0, -90, 0)) #will affect ur ranking later

points_counter = Text(text='Points: 0', position=(-0.87, 0.475), scale=1.5)
multi_counter = Text(text='X1', position=(-0.87, 0.44), scale=1)

ranking = Entity(model='quad', texture='D.png', scale=(2.5, 1.25), position=(-5.7, 7.5, -1))
ranking_bg = Entity(model='quad', scale=(2.5, 3.4), position=(-6, 6.3, 0), color=(0, 0, 0, 0.4))
ranking_bar = Entity(model='quad', scale=(2.3, 0.20), position=(-5.7, 6.95, -1))

font_path = 'assets/textures/ranking/vcr.ttf'

pause_title = Text(text='TIMMY REDBULL RUNNER', position=(-0.8, 0.1), scale=2, font=font_path, color=color.red)
pause_guide = Text(text='Press space to start', position=(-0.8, -0.1), scale=1.75, font=font_path, color=color.white)
pause_splash = Text(text=random.choice(string_list), position=(-0.45, 0.03), scale=1, font=font_path, color=color.yellow, rotation=(0, 0, -15))
pause_bg = Entity(model='quad', scale=(100,100), position=(4, 1, 0), rotation=(0, 90, 0), color=(0, 0, 0, 0.9))

class ReactiveList(list):
    def __init__(self, on_change_callback, *args):
        super().__init__(*args)
        self.on_change_callback = on_change_callback

    def append(self, item):
        super().append(item)
        self.on_change_callback()

    def remove(self, item):
        super().remove(item)
        self.on_change_callback()

    def pop(self, index=-1):
        item = super().pop(index)
        self.on_change_callback()
        return item

text_rows = []
letters_data = ReactiveList(lambda: update())
ranking_points = 200
ranking_letter = "D"
ranking_bar.scale_x = ranking_points / 130
ranking_decay = 15 #per second

for i in range(8):
    x_pos = -0.870 + (i * 0.0027)
    y_pos = 0.235 - (i * 0.030)
    
    row = Text(text='', position=(x_pos, y_pos), font=font_path)
    text_rows.append(row)

speedcamera_taken = False

current_lane = 0
lanes = [-3, 0, 3]

points = 0
multiplier = 1

dead = False
godmode = False
started = False
is_paused = False
started_animation = False

camera.y = 2 #10
camera.z = 0 #-20
camera.x = -7 #0
camera.rotation_x = -5 #15
camera.rotation_y = 90 #0

move_speed = 0.5

is_jumping = False
is_crouching = False
resetcrouch = None
falldown = None

def input(key):
    global current_lane, started
    global is_jumping, is_crouching, resetcrouch, is_paused, falldown, started_animation
    global ranking
    if key == "space" and not started and not started_animation:
        started_animation = True
        camera.animate_y(10, duration=1.0, curve=curve.out_sine)
        camera.animate_x(0, duration=1.0, curve=curve.out_sine)
        camera.animate_z(-20, duration=1.0, curve=curve.out_sine)
        camera.animate('rotation_x', 15, duration=1.0, curve=curve.out_sine)
        camera.animate('rotation_y', 0, duration=1.0, curve=curve.out_sine)
        pause_bg.fade_out(duration=0.2)
        pause_title.fade_out(duration=0.2)
        pause_splash.fade_out(duration=0.2)
        pause_guide.fade_out(duration=0.2)
        invoke(start_game, delay=3) #gives the player some time to observe their surroundings
    elif key == 'escape':
        is_paused = not is_paused

    #debugging stuff under here
    elif key == 'r':
        pause_splash.text=random.choice(string_list)

    elif is_paused or not started:
        return

    #normal stuff under here
    elif key == 'd' or key == 'right arrow':
        if current_lane < 1:
            current_lane += 1
    elif key == 'a' or key == 'left arrow':
        if current_lane > -1:
            current_lane -= 1
    elif key == 'space' or key == 'w' or key == 'up arrow':
        if not is_jumping and player.y == 1 or player.y == 0.5: #patches flight. with good enough skills, u could skip most of the game using these glitches
            #one op glitch i found is that if u jump during the crouching animation. u fly up. but reset_crouch still plays. so the game doesnt know that ur jumping. so u could jump again
            if is_crouching:
                reset_crouch()
                resetcrouch.kill()
            is_jumping = True
            player.animate_y(player.y + 2, duration=0.3 / move_speed, curve=curve.out_sine)
            player.animate('rotation_x', 0, duration=0.3 / move_speed, curve=curve.out_sine)
            falldown = invoke(fall_down, delay=0.3 / move_speed)
    elif key == "c" or key == "control" or key == 'down arrow':
        reset_jump()
        is_crouching = True
        player.animate_y(0.5, duration=0.1)
        player.animate('rotation_x', 90, duration=0.1)
        resetcrouch = invoke(reset_crouch, delay=1 / move_speed)

    target_x = lanes[current_lane + 1]
    player.animate_x(target_x, duration=0.1, curve=curve.out_quad)

def fall_down():
    global is_jumping
    if is_paused:
        return
    player.animate_y(1, duration=0.3 / move_speed, curve=curve.in_sine)
    invoke(reset_jump, delay=0.3 / move_speed)

def reset_jump():
    global is_jumping
    is_jumping = False

def reset_crouch():
    global is_crouching
    is_crouching = False
    if not is_jumping:
        player.animate_y(1, duration=0.1)
        player.animate('rotation_x', 0, duration=0.1)

def start_game():
    global started

    started = True


def update():
    global move_speed, last_rpc_update, points, dead, is_jumping, is_crouching, bg_music, started, speedcamera_taken, ranking_points, ranking_letter, ranking_decay
    player.rotation_y += 50 * time.dt #dis is walking animation. dont touch
    if is_paused and is_crouching:
        resetcrouch.pause()
    elif not is_paused and is_crouching:
        resetcrouch.resume()

    if is_paused and is_jumping:
        falldown.pause()
    elif not is_paused and is_jumping:
        falldown.resume()

    if not dead and started and not is_paused:
        for row in text_rows:
            destroy(row)
        text_rows.clear()

        for i, letter in enumerate(letters_data[:8]):
            x_pos = -0.870 + (i * 0.0027)
            y_pos = 0.235 - (i * 0.030)
            row = Text(text=str(letter), position=(x_pos, y_pos), font=font_path)
            text_rows.append(row)

            if ranking_points < 300:
                ranking_letter = "D"
                ranking_bar.scale_x = ranking_points / 130
                ranking_decay = 15
            elif ranking_points < 400:
                ranking_letter = "C"
                ranking_bar.scale_x = (ranking_points - 300) / 100
                ranking_decay = 18.75
            elif ranking_points < 500:
                ranking_letter = "B"
                ranking_bar.scale_x = (ranking_points - 400) / 100
                ranking_decay = 22.5
            elif ranking_points < 700:
                ranking_letter = "A"
                ranking_bar.scale_x = (ranking_points - 500) / 200
                ranking_decay = 30
            elif ranking_points < 850:
                ranking_letter = "S"
                ranking_bar.scale_x = (ranking_points - 700) / 150
                ranking_decay = 45
            elif ranking_points < 1000:
                ranking_letter = "SS"
                ranking_bar.scale_x = (ranking_points - 850) / 150
                ranking_decay = 60
            elif ranking_points < 1500:
                ranking_letter = "SSS"
                ranking_bar.scale_x = (ranking_points - 1000) / 500
                ranking_decay = 90
            else:
                ranking_letter = "U"
                ranking_bar.scale_x = 2.3
                ranking_decay = 120

            ranking.texture = f"{ranking_letter}.png"

            ranking_points -= ranking_decay * time.dt
            ranking_points = max(0.0, ranking_points)

        ground.texture_offset += Vec2(0, move_speed * time.dt)
        hedgeL.texture_offset += Vec2(0, move_speed * time.dt)
        hedgeR.texture_offset += Vec2(0, move_speed * time.dt)

        obstacle1.z -= (move_speed * time.dt) * 30
        obstacle2.z -= (move_speed * time.dt) * 30
        obstacle3.z -= (move_speed * time.dt) * 30
        speedcamera.z -= (move_speed * time.dt) * 30

        if obstacle1.x == player.x and player.intersects(obstacle1) and not is_jumping and not godmode: 
            dead = True
        if obstacle2.x == player.x and player.intersects(obstacle2) and not is_crouching and not godmode: 
            dead = True
        if obstacle3.x == player.x and player.intersects(obstacle3) and not godmode: 
            dead = True

        if obstacle1.z < -10:
            obstacle1.z = 50
            obstacle1.x = random.choice(lanes)

        if obstacle2.z < -10:
            obstacle2.z = 50
            obstacle2.x = random.choice(lanes)

        if obstacle3.z < -10:
            obstacle3.z = 50
            obstacle3.x = random.choice(lanes)

        if speedcamera.z < 2 and not speedcamera_taken:
            speedcamera_taken = True
            for item in list(letters_data):
                if "SWOOSH" in item:
                    letters_data.remove(item)          
            new_swoosh_text = f"[+] SWOOSH ({round(move_speed * 10, 1)}MPH)"
            ranking_points += round(move_speed * 100, 0)
            letters_data.append(new_swoosh_text)
            def remove_swoosh():
                if new_swoosh_text in letters_data:
                    letters_data.remove(new_swoosh_text)
            
            invoke(remove_swoosh, delay=10)

        if speedcamera.z < -10:
            speedcamera.z = 200
            speedcamera_taken = False

        move_speed += 0.0001

        points += 0.1 * multiplier

        points_counter.text = f'Points: {round(points, 0)}'
        multi_counter.text = f'X{multiplier}'

    if time.time() - last_rpc_update > update_interval:
        RPC.update(
            state="Running from the cops",
            details=f"Points: {round(points, 0)}, Running at {round(move_speed * 10, 1)} mph",
            start=start_time,
            large_image="logo",
            large_text="Timmy Redbull Runner"
        )
        last_rpc_update = time.time()

    if started_animation and bg_music is None:
        bg_music = Audio('assets/timmyredbullrunner.wav', loop=True, autoplay=True) #dis a fire beat dont touch

app.run()