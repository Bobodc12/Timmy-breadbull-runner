from ursina import *
from direct.actor.Actor import Actor #wait why did i import this again?
import random
from pypresence import Presence, exceptions
import time
import math
from collections import Counter
import json
import sys
import os
from panda3d.core import loadPrcFileData
from ursina.shaders import lit_with_shadows_shader

client_id = '1535037932828889178' #for discord rpc

RPC = None
rpc_connected = False

try:
    RPC = Presence(client_id)
    RPC.connect()
    rpc_connected = True
except Exception as e:
    print("launching game without discord RPC") #cuz i will prob play this game on my school laptop in the future


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

start_time = time.time()
last_rpc_update = 0
update_interval = 15 #to avoid rate limiting

config_file = {}

with open(resource_path("data.json"), "r") as file:
        data = json.load(file)
        string_list = data.get("messages", []) #i swear these are goated

with open(resource_path("config.json"), "r") as file:
    config_file = json.load(file)

antialiasing = config_file["antialiasing"]
shadows = config_file["shadows"]

loadPrcFileData("", "framebuffer-multisample 1")
loadPrcFileData("", "multisamples 4") #anti aliasing. will add an settings menu later with a toggle button
loadPrcFileData("", "shadow-map-size 2048")
loadPrcFileData("", "textures-power-2 none")

app = Ursina()
player = Entity(model='assets/farmer.obj', texture='lambert1_albedo', scale=(0.6), position=(0, 0, 1), shader=lit_with_shadows_shader) #his name is timmy, and he likes breadbull
idle_player = FrameAnimation3d('assets/farmer/idle/farmer', texture='lambert1_albedo', scale=(0.5), position=(0, 1, 0), fps=5, shader=lit_with_shadows_shader) #10 frame animation. peak
player_col_cube = Entity(model='cube', color=color.red, position=(player.x, player.y, player.z), collider='box', visible=False)
sky = Sky(texture='sky_sunset')
ground = Entity(model='plane', texture='grass_tintable', color=Color(0.5, 0.5, 0.15, 1), scale=(50, 50, 50), texture_scale=(1, 1), shader=lit_with_shadows_shader)
bg_music = None
mm_bg_music = None

hedgeL = Entity(model='cube', texture='grass', scale=(1, 3, 50), position=(-5, 0, 0), shader=lit_with_shadows_shader) #hedges? in the desert?
hedgeR = Entity(model='cube', texture='grass', scale=(1, 3, 50), position=(5, 0, 0), shader=lit_with_shadows_shader)

obstacle1 = Entity(model='assets/pol.obj', texture="2015_Ranger_Pol_d", position=(3, 1.5, 50), scale=(1.75), rotation=(0, 180, 0), collider='box', shader=lit_with_shadows_shader) #u can jump over
obstacle2 = Entity(model='assets/fence.obj', position=(-3, 0.3, 10), scale=(0.15), rotation=(0, 180, 0), color=color.dark_gray, collider='box', shader=lit_with_shadows_shader) #u can crouch under
obstacle3 = Entity(model='assets/school bus.obj', texture='busdiffuse.png', position=(0, 0, 20), scale=(3.5), rotation=(0, 180, 0), collider='box', shader=lit_with_shadows_shader) #whole ass school bus
speedcamera = Entity(model='assets/SpeedCam.obj', texture='SpeedCam.png', position=(6, 0, 30), rotation=(0, -90, 0), shader=lit_with_shadows_shader) #will affect ur ranking later (done)
#where is freddy fazbear

thesun = DirectionalLight(position=(10, 2, 3), shadows=shadows, rotation=(-90, 0, 0), color=Vec4(1, 1, 1, 1))

points_counter = Text(text='Points: 0', position=(-0.87, 0.475), scale=1.5)
multi_counter = Text(text='X1', position=(-0.87, 0.44), scale=1)

ranking = Entity(model='quad', texture='D.png', scale=(2.5, 1.25), position=(-5.7, 7.5, -1))
ranking_bg = Entity(model='quad', scale=(2.5, 3.4), position=(-6, 6.3, 0), color=(0, 0, 0, 0.4))
ranking_bar = Entity(model='quad', scale=(2.3, 0.20), position=(-5.7, 6.95, -1))

font_path = 'assets/textures/ranking/vcr.ttf' #bros trynna be retro. retroslop (i googled ultrakill font and clicked the top result. VCR OSD Mono)
Text.default_font=font_path

pause_title = Text(text='TIMMY BREADBULL RUNNER', position=(-0.8, 0.1), scale=2, font=font_path, color=color.red)
pause_guide = Text(text='Press space to start', position=(-0.8, -0.1), scale=1.75, font=font_path, color=color.white)
pause_sett = Text(text='Press enter to change settings', position=(-0.8, -0.2), scale=1.75, font=font_path, color=color.white)
pause_splash = Text(text=random.choice(string_list), position=(-0.45, 0.03, -0.1), scale=1, font=font_path, color=color.yellow, rotation=(0, 0, -15)) #as i said, these are goated
pause_bg = Entity(model='quad', scale=(100,100), position=(4, 1, 0), rotation=(0, 90, 0), color=(0, 0, 0, 0.9))

def toggle_aa():
    global antialiasing
    antialiasing = not antialiasing
    settings_aa.text=f'anti aliasing (4x)\ncurrently set to:\n{antialiasing}'
def toggle_shadows():
    global shadows
    shadows = not shadows
    thesun.shadows = shadows
    settings_shadow.text=f'shadows\ncurrently set to:\n{shadows}'

settings_aa = Button(text=f'anti aliasing (4x)\ncurrently set to:\n{antialiasing}', scale=(0.3, 0.1), on_click=toggle_aa, position=(0.6, 0.3), alpha=0, collision=False)
settings_shadow = Button(text=f'shadows\ncurrently set to:\n{shadows}', scale=(0.3, 0.1), on_click=toggle_shadows, position=(0.6, 0.19), alpha=0, collision=False)
settings_aa.text_entity.alpha=0
settings_shadow.text_entity.alpha=0


player.visible = False
idle_player.visible = True

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
letters_data = ReactiveList(lambda: update_text_display())
ranking_points = 200
ranking_letter = "D"
ranking_bar.scale_x = ranking_points / 130
ranking_decay = 15 #per second. this is like very bugged the first 10 seconds, im lovin it

last_jump = 0
bhop_count = 0

message_duration = 5 #5 seconds is good dont touch

for i in range(8):
    x_pos = -0.45 + (i * 0.0027)
    y_pos = 0.1 - (i * 0.060)
    row = Text(text='', position=(x_pos, y_pos), rotation_x=15, font=font_path, parent=ranking_bg, scale=3)
    text_rows.append(row)

def update_text_display():
    for i in range(8):
        if i < len(letters_data):
            text_rows[i].text = str(letters_data[i])
        else:
            text_rows[i].text = ''

def add_ranking_points(points_to_add, message=None, stackable=True):
    global ranking_points
    ranking_points += points_to_add
    if message:
        base_msg = message.split(" [x")[0].split(" (")[0]
        
        found_index = -1
        current_count = 1
        
        for idx, item in enumerate(letters_data):
            item_base = item.split(" [x")[0].split(" (")[0]
            if item_base == base_msg:
                found_index = idx
                if " [x" in item:
                    try:
                        current_count = int(item.split(" [x")[1].replace("]", ""))
                    except ValueError:
                        current_count = 1
                break

        if stackable:
            if found_index != -1:
                letters_data.pop(found_index)
                current_count += 1
                message = f"{base_msg} [x{current_count}]"
            
            letters_data.append(message)
            def remove_msg():
                if message in letters_data:
                    letters_data.remove(message)
            invoke(remove_msg, delay=message_duration)
        else:
            if found_index != -1:
                letters_data.pop(found_index)
            letters_data.append(message)
            def remove_msg():
                if message in letters_data:
                    letters_data.remove(message)
            invoke(remove_msg, delay=message_duration)

speedcamera_taken = False
car_passed = False
fence_passed = False

current_lane = 0
lanes = [-3, 0, 3]

points = 0
multiplier = 1

window.fullscreen = False
window.borderless = False

dead = False
godmode = False #ooo you like cheating dont you?
started = False
settings_open = False
is_paused = False
started_animation = False

camera.y = 2 #10
camera.z = 0 #-20
camera.x = -7 #0
camera.rotation_x = -5 #15
camera.rotation_y = 90 #0
#what the hell do those comments mean

move_speed = 0.5

is_jumping = False
is_crouching = False
resetcrouch = None
falldown = None

def input(key):
    global current_lane, started
    global is_jumping, is_crouching, resetcrouch, is_paused, falldown, started_animation, bhop_count, bg_music
    global ranking
    if key == "space" and not started and not started_animation:
        started_animation = True
        camera.animate_y(10, duration=1.0, curve=curve.out_sine)
        camera.animate_x(0, duration=1.0, curve=curve.out_sine)
        camera.animate_z(-20, duration=1.0, curve=curve.out_sine)
        camera.animate('rotation_x', 15, duration=1.0, curve=curve.out_sine)
        camera.animate('rotation_y', 0, duration=1.0, curve=curve.out_sine)
        pause_bg.animate_y(10, duration=1.0, curve=curve.out_sine)
        pause_bg.animate_x(0, duration=1.0, curve=curve.out_sine)
        pause_bg.animate_z(-17, duration=1.0, curve=curve.out_sine)
        pause_bg.animate('rotation_x', 15, duration=1.0, curve=curve.out_sine)
        pause_bg.animate('rotation_y', 0, duration=1.0, curve=curve.out_sine)
        pause_bg.fade_out(duration=0.2)
        pause_title.fade_out(duration=0.2)
        pause_splash.fade_out(duration=0.2)
        pause_guide.fade_out(duration=0.2)
        pause_sett.fade_out(duration=0.2)

        player.visible = True
        idle_player.visible = False
        invoke(start_game, delay=3) #gives the player some time to observe their surroundings

    elif key == 'enter' and not started and not started_animation:
        settings()
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
        if -0.1 < player.y < 0.26 and not is_jumping: #patches flight. with good enough skills, u could skip most of the game using these glitches
            if last_jump <= 0.5 and not is_crouching:
                bhop_count += 1
                if bhop_count >= 3:
                    add_ranking_points(50, f"+ BHOP (X{bhop_count})", stackable=False)
            else:
                bhop_count = 0

            if is_crouching:
                reset_crouch()
                resetcrouch.kill()
            is_jumping = True
            player.animate_y(4, duration=0.3 / move_speed, curve=curve.out_sine)
            player.animate('rotation_x', 0, duration=0.3 / move_speed, curve=curve.out_sine)
            falldown = invoke(fall_down, delay=0.3 / move_speed)
    elif key == "c" or key == "control" or key == 'down arrow': #dont ask why i didnt add S. im too lazy. srry WASD players
        reset_jump()
        is_crouching = True
        player.animate_y(0.25, duration=0.1)
        player.animate('rotation_x', 90, duration=0.1)
        resetcrouch = invoke(reset_crouch, delay=1 / move_speed)

    target_x = lanes[current_lane + 1]
    player.animate_x(target_x, duration=0.1, curve=curve.out_quad)

def fall_down(): #if it works, dont touch it (it applies for fall_down and reset_crouch)
    global is_jumping
    if is_paused:
        return
    player.animate_y(0, duration=0.3 / move_speed, curve=curve.in_sine)
    invoke(reset_jump, delay=0.3 / move_speed)

def reset_jump():
    global is_jumping
    is_jumping = False

def reset_crouch():
    global is_crouching
    is_crouching = False
    if not is_jumping:
        player.animate_y(0, duration=0.1)
        player.animate('rotation_x', 0, duration=0.1)

def settings():
    global settings_open
    if settings_open == True:
        settings_open = False
        settings_to_save = {"antialiasing": antialiasing, "shadows": shadows}
        with open(resource_path("config.json"), "w") as file:
            json.dump(settings_to_save, file, indent=4)
        camera.animate_z(0, duration=1, curve=curve.out_sine)
        pause_title.fade_in(duration=1, curve=curve.out_sine)
        pause_splash.fade_in(duration=1, curve=curve.out_sine)
        pause_guide.fade_in(duration=1, curve=curve.out_sine)
        settings_aa.fade_out(duration=1, curve=curve.out_sine)
        settings_aa.text_entity.fade_out(duration=1, curve=curve.out_sine)
        settings_shadow.fade_out(duration=1, curve=curve.out_sine)
        settings_shadow.text_entity.fade_out(duration=1, curve=curve.out_sine)
        settings_aa.collision=False
        settings_shadow.collision=False
        pause_sett.text = "Press enter to change settings"
    else:
        settings_open = True
        camera.animate_z(-1.5, duration=1, curve=curve.out_sine)
        pause_title.fade_out(duration=1, curve=curve.out_sine)
        pause_splash.fade_out(duration=1, curve=curve.out_sine)
        pause_guide.fade_out(duration=1, curve=curve.out_sine)
        settings_aa.fade_in(duration=1, curve=curve.out_sine)
        settings_aa.text_entity.fade_in(duration=1, curve=curve.out_sine)
        settings_shadow.fade_in(duration=1, curve=curve.out_sine)
        settings_shadow.text_entity.fade_in(duration=1, curve=curve.out_sine)
        settings_aa.collision=True
        settings_shadow.collision=True
        pause_sett.text = "Press enter to save settings and return to main menu"

def start_game():
    global started
    started = True #top 10 most emotional functions in human history. 2 lines long

def die():
    global dead
    dead = True
    player.animate_y(0.0, duration=0.1)
    player.animate('rotation_x', 90, duration=0.1)
    pause_bg.fade_in(duration=3, curve=curve.linear)
    invoke(death_text, delay=2)

def death_text():
    pause_guide.text = "YOU DIED\nrespawning isnt implemented btw. restart the game"
    pause_guide.origin = 0, 0
    pause_guide.position = 0, 0
    pause_guide.fade_in(duration=0.5, curve=curve.linear)

def update():
    global move_speed, last_rpc_update, points, dead, is_jumping, is_crouching, bg_music, mm_bg_music, started, speedcamera_taken, car_passed, fence_passed, ranking_points, ranking_letter, ranking_decay, last_jump #why are there so many
    player.rotation_y += 50 * time.dt #dis is walking animation. dont touch (actually. touch it once u got 3 .obj files. one for each animation keyframe. cuz ursina like hates armatures)
    player_col_cube.x = player.x
    idle_player.rotation_y += 50 * time.dt
    if is_paused and is_crouching:
        resetcrouch.pause()
    elif not is_paused and is_crouching:
        resetcrouch.resume()

    if is_paused and is_jumping:
        falldown.pause()
    elif not is_paused and is_jumping:
        falldown.resume()

    if not dead and started and not is_paused:
        # Ranking tier calculations (optimized to run once per frame smoothly)
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
            ranking_letter = "U" #U, for Ultrakill (yes. U.png is the ultrakill ranking. from ultrakill
            ranking_bar.scale_x = 2.3
            ranking_decay = 120

        ranking.texture = f"{ranking_letter}.png"

        ranking_points -= ranking_decay * time.dt
        ranking_points = max(0.0, ranking_points)

        ground.texture_offset += Vec2(0, move_speed * time.dt)
        hedgeL.texture_offset += Vec2(0, move_speed * time.dt)
        hedgeR.texture_offset += Vec2(0, move_speed * time.dt)

        obstacle1.z -= (move_speed * time.dt) * 30 #why even is 30 the magic number
        obstacle2.z -= (move_speed * time.dt) * 30
        obstacle3.z -= (move_speed * time.dt) * 30
        speedcamera.z -= (move_speed * time.dt) * 30

        if not is_jumping and player_col_cube.intersects(obstacle1) and not godmode:
            die()
        elif not car_passed and obstacle1.z <= player.z and is_jumping == True and player_col_cube.x == obstacle1.x:
            car_passed = True
            add_ranking_points(50, "+ HOOD JUMP", stackable=True)

        if player_col_cube.intersects(obstacle2) and not godmode:
            if not is_crouching:
                die()
            elif not fence_passed:
                fence_passed = True
                add_ranking_points(50, "+ SLIDE", stackable=True)

        if player_col_cube.intersects(obstacle3) and not godmode: #no way u jumping over this
            die() #yeah thats what i thought, u really tryna jump over a school bus?
            #congrats school bus, ur the only obstacle without a ranking text

        if obstacle1.z < -10:
            obstacle1.z = 50
            obstacle1.x = random.choice(lanes)
            car_passed = False

        if obstacle2.z < -10:
            obstacle2.z = 50
            obstacle2.x = random.choice(lanes)
            fence_passed = False

        if obstacle3.z < -10:
            obstacle3.z = 50 #this is so shitty. im lovin it
            obstacle3.x = random.choice(lanes)

        if speedcamera.z < 2 and not speedcamera_taken:
            speedcamera_taken = True
            add_ranking_points(round(move_speed * 100, 0), f"+ SWOOSH ({round(move_speed * 10, 1)}MPH)", stackable=False)

        if speedcamera.z < -10:
            speedcamera.z = 200
            speedcamera_taken = False

        move_speed += 0.0001 * (time.dt * 72) #so like next git commit, can i like add "* (time.dt * 72)" to this line. please? wait nuh uh im doing it now

        points += (0.1 * multiplier) * (time.dt * 72) #same thing with this one

        if is_jumping:
            last_jump = 0
        else:
            last_jump += time.dt


        points_counter.text = f'Points: {round(points, 0)}'
        multi_counter.text = f'X{multiplier}'

    if time.time() - last_rpc_update > update_interval:
        try:
            RPC.update(
                state="Running from the cops", #TIMMY, PULL OVER NOW
                details=f"Points: {round(points, 0)}, Running at {round(move_speed * 10, 1)} mph",
                start=start_time,
                large_image="logo",
                large_text="Timmy Breadbull Runner"
            )
        except Exception:
            rpc_connected = False
        last_rpc_update = time.time()

    if started_animation and bg_music is None:
        mm_bg_music.stop()
        bg_music = Audio('assets/timmybreadbullrunner.wav', loop=True, autoplay=True) #dis a fire beat dont touch (might add main menu music later (done))
    elif mm_bg_music is None:
        mm_bg_music = Audio('assets/mainmenu.wav', loop=True, autoplay=True)

app.run()