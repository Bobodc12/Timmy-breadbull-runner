from ursina import *
import random
from pypresence import Presence
import time
import math

client_id = '1535037932828889178'

RPC = Presence(client_id)
RPC.connect()

start_time = time.time()
last_rpc_update = 0
update_interval = 15

app = Ursina()
player = Entity(model='assets/farmer.obj', texture='lambert1_albedo', scale=(0.5), position=(0, 1, 0)) #his name is timmy, and he likes redbull
sky = Sky(texture='sky_sunset')
ground = Entity(model='plane', texture='grass_tintable', color=color.light_gray, scale=(50, 50, 50), texture_scale=(1, 1))

hedgeL = Entity(model='Cube', texture='grass', scale=(1, 3, 50), position=(-5, 0, 0))
hedgeR = Entity(model='Cube', texture='grass', scale=(1, 3, 50), position=(5, 0, 0))

obstacle1 = Entity(model='assets/pol.obj', texture="2015_Ranger_Pol_d", position=(3, 1, 50), scale=(1.5), rotation=(0, 180, 0))
obstacle2 = Entity(model='assets/fence.obj', position=(-3, 1, 10), scale=(0.15), rotation=(0, 180, 0))

points_counter = Text(text='Points: 0', position=(-0.87, 0.475), scale=1.5)
multi_counter = Text(text='X1', position=(-0.87, 0.44), scale=1)

current_lane = 0
lanes = [-3, 0, 3]

points = 0
multiplier = 1

dead = False
collision_threshold_pick = 3
collision_threshold_fence = 1

camera.y = 10
camera.rotation_x = 15

move_speed = 0.5

is_jumping = False
is_crouching = False

def input(key):
    global current_lane
    global is_jumping, is_crouching
    if key == 'd' or key == 'right arrow':
        if current_lane < 1:
            current_lane += 1
    elif key == 'a' or key == 'left arrow':
        if current_lane > -1:
            current_lane -= 1
    elif key == 'space' or key == 'w' or key == 'up arrow':
        if not is_jumping:
            reset_crouch()
            is_jumping = True
            player.animate_y(player.y + 2, duration=0.25 / move_speed, curve=curve.out_sine)
            player.animate('rotation_x', 0, duration=0.25 / move_speed, curve=curve.out_sine)
            invoke(fall_down, delay=0.25 / move_speed)
    elif key == "c" or key == "control" or key == 'down arrow':
        reset_jump()
        is_crouching = True
        player.animate_y(0.5, duration=0.1)
        player.animate('rotation_x', 90, duration=0.1)
        invoke(reset_crouch, delay=1 / move_speed)

    target_x = lanes[current_lane + 1]
    player.animate_x(target_x, duration=0.1, curve=curve.out_quad)

def fall_down():
    global is_jumping
    player.animate_y(1, duration=0.25 / move_speed, curve=curve.in_sine)
    invoke(reset_jump, delay=0.25 / move_speed)

def reset_jump():
    global is_jumping
    is_jumping = False

def reset_crouch():
    if not is_jumping:
        is_crouching = False
        player.animate_y(1, duration=0.1)
        player.animate('rotation_x', 0, duration=0.1)


def update():
    global move_speed, last_rpc_update, points, dead, is_jumping, is_crouching
    player.rotation_y += 50 * time.dt #dis is walking animation. dont touch
    if not dead:
        ground.texture_offset += Vec2(0, move_speed * time.dt)
        hedgeL.texture_offset += Vec2(0, move_speed * time.dt)
        hedgeR.texture_offset += Vec2(0, move_speed * time.dt)

        obstacle1.z -= (move_speed * time.dt) * 30
        obstacle2.z -= (move_speed * time.dt) * 30

        if obstacle1.x == player.x and abs(player.z - obstacle1.z) <= collision_threshold_pick and not is_jumping:
            dead = True
        if obstacle2.x == player.x and abs(player.z - obstacle2.z) <= collision_threshold_fence and not is_crouching:
            dead = True

        if obstacle1.z < -2:
            obstacle1.z = 50
            obstacle1.x = random.choice(lanes)

        if obstacle2.z < -2:
            obstacle2.z = 50
            obstacle2.x = random.choice(lanes)

        move_speed += 0.0001

        points += 0.1 * multiplier

        points_counter.text = f'Points: {round(points, 0)}'
        multi_counter.text = f'X{multiplier}'

    if time.time() - last_rpc_update > update_interval:
        RPC.update(
            state="Running from the cops",
            details="RPC is still WIP",
            start=start_time,
            large_image="logo",
            large_text="Timmy Redbull Runner"
        )
        last_rpc_update = time.time()

app.run()