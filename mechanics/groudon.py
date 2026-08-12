import random
import math
import os

class GroudonMechanics:
    def cancel_groudon_arts(self):
        # Canceling Groudon only affects him. Victims are no longer logically linked.
        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            
        if hasattr(self, 'groudon_absorb_particles'):
            for p in self.groudon_absorb_particles:
                self.canvas.delete(p['id'])
            self.groudon_absorb_particles = []

    def _fsm_groudon_channeling(self):
        if not hasattr(self, 'groudon_absorb_timer'):
            self.groudon_phase = 'absorbing'
            self.groudon_absorb_timer = 100
            self.groudon_absorb_particles = []
            
        if self.groudon_phase == 'absorbing':
            self.groudon_absorb_timer -= 1
            
            if self.groudon_absorb_timer % 3 == 0:
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(80, 150)
                cx = self.size_w // 2
                cy = self.size_h // 2
                px = cx + math.cos(angle) * dist
                py = cy + math.sin(angle) * dist
                
                color = random.choice(["#8B0000", "#FF4500", "#FF8C00", "#8B4513", "#A0522D"])
                size = random.choice([2, 3])
                
                pid = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill=color, outline=color, tags="vfx_groudon_absorb")
                self.groudon_absorb_particles.append({'id': pid, 'x': px, 'y': py, 'cx': cx, 'cy': cy})
                
            alive = []
            for p in self.groudon_absorb_particles:
                dx = p['cx'] - p['x']
                dy = p['cy'] - p['y']
                d = math.sqrt(dx**2 + dy**2)
                if d > 10.0:
                    speed = 6.0 + (100 - self.groudon_absorb_timer) * 0.05
                    move_x = (dx/d) * speed
                    move_y = (dy/d) * speed
                    self.canvas.move(p['id'], move_x, move_y)
                    p['x'] += move_x
                    p['y'] += move_y
                    alive.append(p)
                else:
                    self.canvas.delete(p['id'])
            self.groudon_absorb_particles = alive
            
            if self.groudon_absorb_timer <= 0:
                for p in self.groudon_absorb_particles:
                    self.canvas.delete(p['id'])
                self.groudon_absorb_particles = []
                self.v_y_velocity = -28.0 # Give it strong upward velocity for the jump
                self.groudon_phase = 'jumping'
                
        elif self.groudon_phase == 'jumping':
            gravity = 4.0
            self.v_y_velocity = getattr(self, 'v_y_velocity', 0.0) + gravity
            self.y += self.v_y_velocity

            self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)

            # PHYSICAL FIX: Continuous topographic scan.
            # If underlying window is deleted, Groudon detects void and its 'floor_y' becomes
            # the next lower window or native taskbar.
            current_env, _ = self.get_window_environment()
            fall_tolerance = max(15, int(self.v_y_velocity) + 15) if self.v_y_velocity > 0 else 15
            self.floor_y = current_env['y'] if self.y <= current_env['y'] + fall_tolerance else self.default_floor_y

            if self.y >= self.floor_y and self.v_y_velocity > 0:
                self.y = self.floor_y
                self.v_y_velocity = 0.0
                
                self.groudon_phase = 'shaking'
                self.groudon_shake_timer = 50 

                self.show_dirt_vfx()
                self.schedule_loop(100, self.show_dirt_vfx)

                # INSTANT SHOCKWAVE (Only occurs in 1 frame)
                if getattr(self, 'get_all_pets', None):
                    for target in self.get_all_pets():
                        if target != self and target.window.winfo_exists() and target.current_state not in ['exiting', 'dragged', 'spawning_wild', 'despawning_wild', 'falling_pokeball', 'falling_egg']:
                            
                            target_env, _ = target.get_window_environment()
                            physical_floor = target_env['y'] if target.y <= target_env['y'] + 15 else target.default_floor_y
                            
                            # Impact condition: Only affected by earthquake if touching the ground
                            if not getattr(target, 'is_flying', False) and target.y >= physical_floor - 15:
                                
                                # EVENT CLEANUP (Severing) ONLY IF HIT
                                if target.current_state.startswith('dark_'): target.cancel_dark_arts()
                                elif target.current_state.startswith('mewtwo_'): target.cancel_mewtwo_arts()
                                elif target.current_state in ['hooh_channeling', 'panic_run']: target.cancel_hooh_arts()
                                elif target.current_state in ['kyogre_channeling', 'deluge_float']: target.cancel_kyogre_arts()
                                elif target.current_state == 'tk_channeling':
                                    target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                    if getattr(target, 'tk_target', None):
                                        if getattr(target.tk_target, 'current_state', '') in ['tk_controlled', 'tk_lifted']:
                                            t_targ = target.tk_target
                                            t_w = t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                            t_h = t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size
                                            target.manage_tk_aura(t_targ.canvas, t_w, t_h, False)
                                            t_targ.current_state = 'falling'
                                            if hasattr(t_targ, 'tk_master'): t_targ.tk_master = None
                                    target.tk_target = None
                                elif target.current_state == 'tk_lifted':
                                    target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
                                    if getattr(target, 'tk_master', None):
                                        target.tk_master.tk_target = None
                                        target.tk_master.manage_tk_aura(target.tk_master.canvas, target.tk_master.size_w, target.tk_master.size_h, False)
                                        target.tk_master.current_state = 'falling'
                                    target.tk_master = None
                                elif target.current_state == 'bubbled':
                                    target.manage_bubble_vfx(False)
                                    target.show_bubble_burst_vfx()

                                if getattr(target, 'is_glitching', False):
                                    target.is_glitching = False
                                    target.glitch_teleports_left = 0
                                    target.glitch_cooldown = 12000

                                target.canvas.itemconfig(target.canvas_image_id, state='normal')
                                target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
                                try: target.window.attributes('-alpha', 1.0)
                                except: pass
                                
                                target.current_state = 'jumping_arc'
                                target.jump_target_y = physical_floor
                                target.v_y_velocity = random.uniform(-10.0, -16.0) 
                                target.v_x_velocity = 0.0
                                target.anchored_hwnd = None
                                target.show_dirt_vfx() 
                            elif getattr(target, 'is_flying', False):
                                # Aerodynamic disturbance for flyers (does not cancel states, just pushes them)
                                target.y += random.uniform(8.0, 20.0)

                if self.game_controller and hasattr(self.game_controller, 'root'):
                    pc = self.game_controller.root
                    try:
                        if not getattr(self.game_controller, 'is_shaking', False):
                            self.game_controller.is_shaking = True
                            ox = pc.winfo_x()
                            oy = pc.winfo_y()
                            shake_x = random.choice([-15, 15])
                            shake_y = random.choice([-15, 15])
                            pc.geometry(f"+{ox + shake_x}+{oy + shake_y}")
                            
                            def restore_pc():
                                if pc.winfo_exists():
                                    pc.geometry(f"+{ox}+{oy}")
                                    self.game_controller.is_shaking = False
                                    
                            self.schedule_loop(60, restore_pc)
                    except: pass

        elif self.groudon_phase == 'shaking':
            self.groudon_shake_timer -= 1
            
            offset_x = random.choice([-8, 0, 8])
            self.canvas.coords(self.canvas_image_id, (self.size_w//2) + offset_x, self.size_h//2)
            
            if self.groudon_shake_timer <= 0:
                self.canvas.coords(self.canvas_image_id, self.size_w//2, self.size_h//2)
                self.groudon_jumps_left -= 1
                
                # Continuity evaluation: Jump again or stop
                if self.groudon_jumps_left > 0:
                    self.groudon_phase = 'jumping'
                    self.v_y_velocity = -28.0 
                else:
                    self.current_state = 'idle'
                    
        self.update_position()
        self.schedule_loop(30, self.physics_loop)

