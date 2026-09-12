from ensurepip import version
from statistics import multimode

# pyrefly: ignore [missing-import]
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'shadow-depth-bits 24')
loadPrcFileData('', 'shadow-depth-bits 24')
loadPrcFileData('', 'shadow-smoothing 1')
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
from ursina.shaders import lit_with_shadows_shader
import webbrowser
from babel import Locale
from itertools import chain

VERSION = "v1.4.2-alpha"

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
        avail_lang = data.get("avail_lang", [])

with open(resource_path("config.json"), "r") as file:
    config_file = json.load(file)

antialiasing = config_file["antialiasing"]
pre_aa = config_file["antialiasing"]
antialiasing_changed = False
shadows = config_file["shadows"]
muted = config_file["mute"]

locale = Locale('en')
lang_code = config_file["lang"]
lang_name = locale.languages[lang_code]
if lang_code in avail_lang:
    lang_index = avail_lang.index(lang_code)
    pre_lang_index = lang_index
    #print(lang_index)
else:
    print("==============\n\n\ncritical error with language stuff\n\n\n==================")
with open(resource_path(f"lang/{lang_code}.json"), "r", encoding="utf-8") as file:
    lang = json.load(file)

if antialiasing == "true":
    loadPrcFileData('', 'framebuffer-multisample 1')
    loadPrcFileData('', 'multisamples 4')

loadPrcFileData('', 'shadow-bias 0.01')

def open_discord():
    webbrowser.open('https://discord.gg/DAVM6RSJ23')

app = Ursina(development_mode=False, vsync=True)
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

powerup1 = Entity(model='assets/breadbull.obj', texture='canofbreadbull.png', position=(3, 1, 35), shader=lit_with_shadows_shader, scale=0.5, rotation_z=20, collider='box')

thesun = DirectionalLight(position=(10, 2, 3), shadows=shadows, rotation=(90, 0, 0), color=Vec4(1, 1, 1, 1))
if shadows:
    thesun.shadow_map_resolution = Vec2(2048, 2048)

ranking = Entity(model='quad', texture='D.png', scale=(2.5, 1.25), position=(-5.7, 7.5, -1), unlit=True)
ranking_bg = Entity(model='quad', scale=(2.5, 3.4), position=(-6, 6.3, 0), color=(0, 0, 0, 0.4), unlit=True)
ranking_bar = Entity(model='quad', scale=(2.3, 0.20), position=(-5.7, 6.95, -1), unlit=True)

font_path = 'assets/textures/ranking/vcr.ttf' #bros trynna be retro. retroslop (i googled ultrakill font and clicked the top result. VCR OSD Mono)
Text.default_font=font_path

fps_count = Text(text='FPS=60', position=(0.9, 0.5), origin=(0.5, 0.5), font=font_path) #60 is a placeholder, its updated instantly anyways

points_counter = Text(text='Points: 0', position=(-0.87, 0.475), scale=1, font=font_path)
multi_counter = Text(text=' ', position=(-0.87, 0.44), scale=1)

pause_title = Text(text='TIMMY BREADBULL RUNNER', position=(-0.8, 0.1), scale=2, font=font_path, color=color.red)
pause_guide = Text(text=lang["start_tip"], position=(-0.8, -0.1), scale=1.75, font=font_path, color=color.white)
pause_sett = Text(text=lang["settings_tip"], position=(-0.8, -0.2), scale=1.75, font=font_path, color=color.white)
pause_splash = Text(text=random.choice(string_list), position=(0.325, -0.02, -0.1), scale=0.5, font=font_path, color=color.yellow, rotation=(0, 0, -15), parent=pause_title, origin=(0, 0, 0)) #as i said, these are goated
pause_bg = Entity(model='quad', scale=(100,100), position=(4, 1, 0), rotation=(0, 90, 0), color=(0, 0, 0, 0.9))
pause_dc = Button(texture='Discord-Symbol-Blurple.png', scale=(0.075, 0.075*0.76), z=10, color=color.white, position=(0.85, -0.45), on_click=open_discord)
pause_ver = Text(text=VERSION, position=(-0.9, -0.475))

def toggle_aa():
    global antialiasing
    antialiasing = not antialiasing
    settings_aa.text = lang["anti_aliasing"].format(value=antialiasing)
def toggle_shadows():
    global shadows
    shadows = not shadows
    thesun.shadows = shadows
    settings_shadow.text = lang["shadows"].format(value=shadows)
def change_lang():
    global lang_index, lang_code, lang_name
    lang_index = (lang_index + 1) % len(avail_lang)
    lang_code = avail_lang[lang_index]
    lang_name = locale.languages[lang_code]
    settings_language.text=(f'language\ncurrently set to:\n{lang_name}')
def toggle_mute():
    global muted
    muted = not muted
    settings_mute.text=(f'muted\ncurrently set to:\n{muted}')

setting_cat_graphics = Text(text="GRAPHICS", scale=1.5, position=(0, 0.45), origin=(0, 0), color=color.black, alpha=0)
setting_cat_display = Text(text="DISPLAY", scale=1.5, position=(0.3, 0.45), origin=(0, 0), color=color.black, alpha=0)
setting_cat_audio = Text(text="AUDIO", scale=1.5, position=(0.6, 0.45), origin=(0, 0), color=color.black, alpha=0)

settings_bar = Entity(model='quad', parent=setting_cat_display, color=color.dark_gray, z=1, scale=(0.6, 0.05), origin=(0, 0), alpha=0)
settings_select = Entity(model='quad', parent=setting_cat_graphics, z=0.5, scale=(0.15, 0.05), color=color.orange, alpha=0, origin=(0, 0))


settings_aa = Button(text=lang["anti_aliasing"].format(value=antialiasing), scale=(0.3, 0.1), on_click=toggle_aa, position=(0.6, 0.3), alpha=0, collision=False)
settings_shadow = Button(text=lang["shadows"].format(value=shadows), scale=(0.3, 0.1), on_click=toggle_shadows, position=(0.6, 0.17), alpha=0, collision=False)
settings_language = Button(text=f'language\ncurrently set to:\n{lang_name}', scale=(0.3, 0.1), on_click=change_lang, position=(0.6, 0.3), alpha=0, collision=False) #this will be hardcoded so u wont accedently set the language to one u dont know and softlock urself
settings_mute = Button(text=f'muted\ncurrently set to:\n{muted}', scale=(0.3, 0.1), on_click=toggle_mute, position=(0.6, 0.3), alpha=0, collision=False)
settings_aa.text_entity.alpha=0
settings_shadow.text_entity.alpha=0
settings_language.text_entity.alpha=0
settings_mute.text_entity.alpha=0
settings_warning = Text(text=' ', color=color.yellow, position=(0.35, 0.42))
if lang_code == 'fr':
    settings_warning.x=0.30

sett_graphics = [settings_aa, settings_shadow]
sett_display = [settings_language]
sett_audio = [settings_mute]

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
    x_pos = -0.4 + (i * 0.0027)
    y_pos = 0.1 - (i * 0.060)
    row = Text(text=' ', position=(x_pos, y_pos, -0.5), rotation_x=0, font=font_path, parent=ranking_bg, scale=3)
    text_rows.append(row)

def update_text_display():
    for i in range(8):
        if i < len(letters_data):
            text_rows[i].text = str(letters_data[i])
        else:
            text_rows[i].text = ''

def add_ranking_points(points_to_add, message=None, stackable=True):
    global ranking_points, points
    ranking_points += points_to_add
    points += points_to_add
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
invincible = False #this is not the same thing as godmode
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

def update_fps():
    fps = int(1 / time.dt) if time.dt > 0 else 0
    fps_count.text = f'FPS={fps}'
    invoke(update_fps, delay=1)
update_fps()

def update_settings(category):
    if settings_open:
        if category == 1:
            for el in sett_graphics:
                el.visible=True
                el.collision=True
            for el in chain(sett_display, sett_audio):
                el.visible=False
                el.collision=False
        elif category == 2:
            for el in sett_display:
                el.visible=True
                el.collision=True
            for el in chain(sett_graphics, sett_audio):
                el.visible=False
                el.collision=False
        elif category == 3:
            for el in sett_audio:
                el.visible=True
                el.collision=True
            for el in chain(sett_graphics, sett_display):
                el.visible=False
                el.collision=False

cur_sett_index = 1

def input(key):
    global current_lane, started
    global is_jumping, is_crouching, resetcrouch, is_paused, falldown, started_animation, bhop_count, bg_music, cur_sett_index
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
        pause_dc.fade_out(duration=0.2)
        pause_ver.fade_out(duration=0.2)

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

    #normal stuff under here
    elif settings_open and not started and not cur_sett_index == 3 and key == 'right arrow' or key == 'd' or key == "e":
        cur_sett_index += 1
        settings_select.parent=[setting_cat_graphics, setting_cat_display, setting_cat_audio][cur_sett_index-1]
        update_settings(cur_sett_index)
    elif settings_open and not started and not cur_sett_index == 1 and key == 'left arrow' or key == 'a' or key == "q":
        cur_sett_index -= 1
        settings_select.parent=[setting_cat_graphics, setting_cat_display, setting_cat_audio][cur_sett_index-1]
        update_settings(cur_sett_index)

    elif is_paused or not started:
        return



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
                    add_ranking_points(25, f"+ BHOP (X{bhop_count})", stackable=False)
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
    global settings_open, cur_sett_index
    settings_open = not settings_open
    main_menu_elements = [pause_title, pause_splash, pause_guide]
    settings_elements = [settings_aa, settings_aa.text_entity, settings_shadow, settings_shadow.text_entity, settings_language, settings_language.text_entity, settings_mute, settings_mute.text_entity, settings_bar, settings_select, setting_cat_graphics, setting_cat_display, setting_cat_audio]
    setting_buttons = [settings_aa, settings_shadow, settings_language, settings_mute]

    if not settings_open:
        pause_splash.text = random.choice(string_list)   
        settings_to_save = {"antialiasing": antialiasing, "shadows": shadows, "lang": lang_code, "mute": muted}
        with open(resource_path("config.json"), "w") as file:
            json.dump(settings_to_save, file, indent=4)
        camera.animate_z(0, duration=1, curve=curve.out_sine)     
        for el in main_menu_elements:
            el.fade_in(duration=1, curve=curve.out_sine)
        for el in settings_elements:
            el.fade_out(duration=1, curve=curve.out_sine)
        for btn in setting_buttons:
            btn.collision = False           
        pause_sett.text = lang["settings_tip"]    

    else:
        cur_sett_index = 1
        settings_select.parent=[setting_cat_graphics, setting_cat_display, setting_cat_audio][cur_sett_index-1]
        camera.animate_z(-1.5, duration=1, curve=curve.out_sine)
        for el in main_menu_elements:
            el.fade_out(duration=1, curve=curve.out_sine)
        for el in settings_elements:
            el.fade_in(duration=1, curve=curve.out_sine)
        for btn in setting_buttons:
            btn.collision = True
        for el in sett_graphics:
            el.visible=True
        for el in chain(sett_display, sett_audio):
            el.visible=False
            el.collision = False
            
        pause_sett.text = lang["exit_settings_tip"]



def start_game():
    global started
    started = True
    all_delete = [settings_aa, settings_shadow, settings_language, settings_warning, pause_title, pause_sett, pause_splash, pause_dc, pause_ver, idle_player]
    for item in all_delete:
        destroy(item)

def die():
    global dead
    dead = True
    if is_crouching:
        resetcrouch.kill()
    player.animate_y(0.0, duration=0.1)
    player.animate('rotation_x', 90, duration=0.1)
    pause_bg.fade_in(duration=3, curve=curve.linear)
    invoke(death_text, delay=2)

def death_text():
    pause_guide.text = lang["death_message"]
    pause_guide.origin = 0, 0
    pause_guide.position = 0, 0
    pause_guide.fade_in(duration=0.5, curve=curve.linear)

def breadbullpowerup():
    global invincible 
    invincible = True
    resetinvincible = invoke(invincible_reset, delay=10)

def invincible_reset():
    global invincible
    if invincible:
        invincible = False

def camera_shake(intensity=0.3, duration=0.2):
    original_x = camera.x
    original_y = camera.y
    def camera_step(remaining_time):
        if remaining_time > 0:
            camera.x = original_x + random.uniform(-intensity, intensity)
            camera.y = original_y + random.uniform(-intensity, intensity)
            invoke(camera_step, remaining_time - 0.03, delay=0.03)
        else:
            camera.x = original_x
            camera.y = original_y
    camera_step(duration)

def spawn_powerup1():
    powerup1.z = 50
    powerup1.y = 1
    while powerup1.intersects():
        powerup1.x = random.choice(lanes)


def update():
    global move_speed, last_rpc_update, points, dead, is_jumping, is_crouching, bg_music, mm_bg_music, started, speedcamera_taken, car_passed, fence_passed, ranking_points, ranking_letter, ranking_decay, last_jump, invincible #why are there so many
    player.rotation_y += 50 * time.dt * (invincible * 5 + 1) #dis is walking animation. dont touch (actually. touch it once u got 3 .obj files. one for each animation keyframe. cuz ursina like hates armatures)
    player_col_cube.x = player.x
    powerup1.rotation_y += 50 * time.dt
    if not started:
        idle_player.rotation_y += 50 * time.dt
    if is_paused and is_crouching:
        resetcrouch.pause()
    elif not is_paused and is_crouching:
        resetcrouch.resume()

    if is_paused and is_jumping:
        falldown.pause()
    elif not is_paused and is_jumping:
        falldown.resume()

    if antialiasing != pre_aa or lang_index != pre_lang_index and not started:
        settings_warning.text = lang["settings_restart_warning"]
    else:
        settings_warning.text = ''

    if not dead and started and not is_paused:
        #smth i forgor
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
        powerup1.z -= (move_speed * time.dt) * 30

        if not is_jumping and player_col_cube.intersects(obstacle1) and not godmode:
            if invincible:
                obstacle1.y = -10
                add_ranking_points(200, "+ KILL", stackable=True)
                invincible = False
                camera_shake() #add this later
            else:
                die()
        elif not car_passed and obstacle1.z <= player.z and is_jumping == True and player_col_cube.x == obstacle1.x:
            car_passed = True
            add_ranking_points(50, "+ HOOD JUMP", stackable=True)

        if player_col_cube.intersects(obstacle2) and not godmode:
            if not is_crouching:
                if invincible:
                    obstacle2.y = -10
                    add_ranking_points(200, "+ KILL", stackable=True)
                    invincible = False
                    camera_shake()
                else:
                    die()
            elif not fence_passed:
                fence_passed = True
                add_ranking_points(50, "+ SLIDE", stackable=True)

        if player_col_cube.intersects(obstacle3) and not godmode: #no way u jumping over this
            if invincible:
                obstacle3.y = -10
                add_ranking_points(250, "+ WAR CRIME", stackable=True) #heyy thats not very nice D:
                invincible = False
                camera_shake()
            else:
                die() #yeah thats what i thought, u really tryna jump over a school bus?

        if player_col_cube.intersects(powerup1):
            powerup1.y = -10 #fire way of hiding it
            add_ranking_points(50, "+ 300% SAFE", stackable = True)
            breadbullpowerup()

        if obstacle1.z < -10:
            obstacle1.z = 50
            obstacle1.x = random.choice(lanes)
            car_passed = False
            obstacle1.y = 1.5

        if obstacle2.z < -10:
            obstacle2.z = 50
            obstacle2.x = random.choice(lanes)
            fence_passed = False
            obstacle2.y = 0.3

        if obstacle3.z < -10:
            obstacle3.z = 50 #this is so shitty. im lovin it
            obstacle3.x = random.choice(lanes)
            obstacle3.y = 0

        if speedcamera.z < 2 and not speedcamera_taken:
            speedcamera_taken = True
            add_ranking_points(round(move_speed * 100, 0), f"+ SWOOSH ({round(move_speed * 10, 1)}MPH)", stackable=False)

        if speedcamera.z < -10:
            speedcamera.z = 200
            speedcamera_taken = False

        if powerup1.z < -10:
            invoke(spawn_powerup1, delay=30)
            powerup1.z = 50000
            #powerup1.y = 1
            #powerup1.x = random.choice(lanes)

        move_speed += 0.0001 * (time.dt * 72) #so like next git commit, can i like add "* (time.dt * 72)" to this line. please? wait nuh uh im doing it now

        points += (0.1 * multiplier) * (time.dt * 72) #same thing with this one

        if is_jumping:
            last_jump = 0
        else:
            last_jump += time.dt


        points_counter.text = lang["points_label"] + str(int(points))
        multi_counter.text = f' '

    if time.time() - last_rpc_update > update_interval:
        try:
            RPC.update(
                state="Running from the cops", #TIMMY, PULL OVER NOW
                details=f"Points: {round(points, 0)}, Running at {round(move_speed * 10, 1)} mph",
                start=start_time,
                large_image="logo",
                large_text=f"Timmy Breadbull Runner {VERSION}"
            )
        except Exception:
            rpc_connected = False
        last_rpc_update = time.time()
    if started_animation and bg_music is None:
        mm_bg_music.stop()
        bg_music = Audio('assets/timmybreadbullrunner.wav', loop=True, autoplay=True) #dis a fire beat dont touch (might add main menu music later (done))
    elif mm_bg_music is None:
        mm_bg_music = Audio('assets/mainmenu.wav', loop=True, autoplay=True)
    if bg_music:
        bg_music.volume = not muted
    if mm_bg_music:
        mm_bg_music.volume = not muted

app.run()