import random
import math
import tkinter as tk

class XerneasMechanics:
    def cancel_xerneas_arts(self):
        # Destroy the global VFX window to instantly clear the screen of pink particles
        if hasattr(self, 'xerneas_win') and self.xerneas_win and self.xerneas_win.winfo_exists():
            self.xerneas_win.destroy()
            self.xerneas_win = None

        for attr in ['xerneas_phase', 'xerneas_timer']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            if getattr(self, 'is_flying', False):
                self.floor_y = getattr(self, 'target_floor_y', self.y)
                self.current_state = 'ascending'
            else:
                self.current_state = 'falling'

    def _fsm_xerneas_channeling(self):
        if not hasattr(self, 'xerneas_phase'):
            self.xerneas_phase = 0
            self.xerneas_timer = 600 # 30 seconds active duration (600 ticks at 50ms)
            self.spawn_xerneas_aura_vfx()

        self.xerneas_timer -= 1
        
        # Continuously scan the 600px radius to dynamically capture pets that walk into the aura
        if getattr(self, 'get_all_pets', None):
            for target in self.get_all_pets():
                if target != self and target.current_state != 'exiting' and not getattr(target, 'is_egg', False):
                    # Prevent resetting the FSM if the target is already pacified by us
                    if target.current_state != 'xerneas_pacified':
                        dist = math.hypot(target.x - self.x, target.y - self.y)
                        if dist < 600:
                            self.apply_pacification(target)

        if self.xerneas_timer <= 0:
            self.cancel_xerneas_arts()
            self.current_state = 'idle'
            self.xerneas_cooldown = 72000 # 1 hour cooldown lock

        self.update_position()
        self.schedule_loop(50, self.physics_loop)

    def spawn_xerneas_aura_vfx(self):
        # Dedicated borderless window prevents particles from being cropped by the main pet canvas boundaries
        self.xerneas_win = tk.Toplevel(self.window.master)
        self.xerneas_win.title("VFX_Xerneas_Ignore") # Strict radar bypass to prevent physics collision
        self.xerneas_win.overrideredirect(True)
        self.xerneas_win.attributes('-topmost', True)
        
        TRANS_COLOR = '#010101'
        self.xerneas_win.config(bg=TRANS_COLOR)
        try: self.xerneas_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass

        self.xerneas_win_size = 1200 # Represents the 600px radius in both directions
        cx = int(self.x + self.size_w/2 - self.xerneas_win_size/2)
        cy = int(self.y + self.size_h/2 - self.xerneas_win_size/2)
        self.xerneas_win.geometry(f"{self.xerneas_win_size}x{self.xerneas_win_size}+{cx}+{cy}")

        self.xerneas_canvas = tk.Canvas(self.xerneas_win, width=self.xerneas_win_size, height=self.xerneas_win_size, bg=TRANS_COLOR, highlightthickness=0)
        self.xerneas_canvas.pack()
        self.xerneas_particles = []
        self.xerneas_vfx_loop()

    def xerneas_vfx_loop(self):
        if getattr(self, 'current_state', '') != 'xerneas_channeling': return
        if not hasattr(self, 'xerneas_win') or not self.xerneas_win or not self.xerneas_win.winfo_exists(): return

        cx = self.xerneas_win_size / 2
        cy = self.xerneas_win_size / 2

        # Spawn calm, upward-floating fairy particles within the radius
        for _ in range(3):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, 600)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            
            vy = random.uniform(-1.0, -3.0) # Upward float
            vx = random.uniform(-0.5, 0.5)  # Slight lateral sway
            
            size = random.choice([2, 4, 6])
            color = random.choice(["#FFB6C1", "#FF69B4", "#DA70D6", "#FFC0CB"])
            
            pid = self.xerneas_canvas.create_rectangle(
                px-size, py-size, px+size, py+size,
                fill=color, outline=color, tags="vfx_x"
            )
            self.xerneas_particles.append({
                'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(20, 40)
            })

        alive = []
        for p in self.xerneas_particles:
            if p['life'] > 0:
                self.xerneas_canvas.move(p['id'], p['vx'], p['vy'])
                p['life'] -= 1
                alive.append(p)
            else:
                self.xerneas_canvas.delete(p['id'])
        self.xerneas_particles = alive

        self.window.after(50, self.xerneas_vfx_loop)

    def apply_pacification(self, target):
        # Absolute structural sanitation to forcibly rip the target out of any conflicting mechanic
        if target.current_state.startswith('dark_'): target.cancel_dark_arts()
        elif target.current_state == 'tk_channeling':
            target.manage_tk_aura(target.canvas, target.size_w, target.size_h, False)
            if getattr(target, 'tk_target', None):
                t_targ = target.tk_target
                target.manage_tk_aura(t_targ.canvas, t_targ.size_w if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, t_targ.size_h if t_targ.__class__.__name__ == 'DesktopPet' else t_targ.size, False)
                if hasattr(t_targ, 'interrupt_current_state'): t_targ.interrupt_current_state()
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
        elif target.current_state in ['digging_in', 'digging', 'digging_out']:
            # Restore strict default geometric centers to rescue pets stuck underground
            target.canvas.itemconfig(target.canvas_image_id, state='normal')
            target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
            
        if getattr(target, 'is_glitching', False):
            target.is_glitching = False
            target.glitch_teleports_left = 0
            
        for prefix, cancel_func in [('mewtwo_', 'cancel_mewtwo_arts'), ('hooh_', 'cancel_hooh_arts'), ('kyogre_', 'cancel_kyogre_arts'), ('groudon_', 'cancel_groudon_arts'), ('lugia_', 'cancel_lugia_arts'), ('rayquaza_', 'cancel_rayquaza_arts'), ('dialga_', 'cancel_dialga_arts'), ('palkia_', 'cancel_palkia_arts'), ('giratina_', 'cancel_giratina_arts'), ('zekrom_', 'cancel_zekrom_arts'), ('reshiram_', 'cancel_reshiram_arts'), ('kyurem_', 'cancel_kyurem_arts')]:
            if target.current_state.startswith(prefix) and hasattr(target, cancel_func): getattr(target, cancel_func)()

        # Strip opacity filters and hidden states to guarantee visual normalcy
        target.canvas.itemconfig(target.canvas_image_id, state='normal')
        target.canvas.coords(target.canvas_image_id, target.size_w//2, target.size_h//2)
        try: target.window.attributes('-alpha', 1.0)
        except: pass

        if hasattr(target, 'interrupt_current_state'): target.interrupt_current_state()
        target.current_state = 'xerneas_pacified'
        target.xerneas_master = self

    def _fsm_xerneas_pacified(self):
        master = getattr(self, 'xerneas_master', None)
        
        # Link integrity check to ensure Xerneas is still actively channeling
        if not master or master.current_state != 'xerneas_channeling' or not master.window.winfo_exists():
            self.current_state = 'falling'
            self.schedule_loop(50, self.physics_loop)
            return

        # Distance threshold: Breaks the pacification organically if the pet walks out of bounds
        dist = math.hypot(self.x - master.x, self.y - master.y)
        if dist > 600:
            self.current_state = 'falling'
            self.schedule_loop(50, self.physics_loop)
            return

        gravity = 4.0 if getattr(self, 'heavy_fall', False) else 1.5
        self.v_y_velocity += gravity
        self.y += self.v_y_velocity

        current_env, _ = self.get_window_environment()
        physical_floor = current_env['y'] if self.y <= current_env['y'] + 15 else self.default_floor_y

        if self.y >= physical_floor:
            self.y = physical_floor
            self.v_y_velocity = 0.0

            # Restricts movement to simulate a calm walk
            speed = max(1.0, self.speed * 0.4)
            self.x += speed if self.is_facing_right else -speed

            if getattr(self, 'can_screen_wrap', False):
                if self.x <= self.v_x - self.size_w: self.x = self.v_x + self.v_width
                elif self.x >= self.v_x + self.v_width: self.x = self.v_x - self.size_w
            else:
                if self.x <= self.v_x:
                    self.x = self.v_x
                    self.is_facing_right = True
                elif self.x >= (self.v_x + self.v_width) - self.size_w:
                    self.x = (self.v_x + self.v_width) - self.size_w
                    self.is_facing_right = False

            # Decreased individual jump frequency from 8% to 3% to avoid visual clutter
            if random.randint(1, 100) <= 3:
                self.v_y_velocity = -7.0
                if hasattr(self, 'show_heart_vfx'):
                    self.show_heart_vfx()
                
            if random.randint(1, 100) <= 2:
                self.is_facing_right = not self.is_facing_right

            # FSM Lock Prevention: We use the existing social cooldown to prevent pets from getting permanently stuck facing each other
            self.social_cooldown = max(0, getattr(self, 'social_cooldown', 0) - 1)
            
            if getattr(self, 'get_all_pets', None) and self.social_cooldown <= 0:
                for other in self.get_all_pets():
                    if other != self and other.current_state == 'xerneas_pacified':
                        if abs(self.x - other.x) < 60 and abs(self.y - other.y) < 20:
                            # Mutual alignment
                            self.is_facing_right = (other.x > self.x)
                            
                            # Greeting jump logic lowered to 5%
                            if random.randint(1, 100) <= 5:
                                self.v_y_velocity = -6.0
                                if hasattr(self, 'show_heart_vfx'):
                                    self.show_heart_vfx()
                            
                            # Apply a 2-second immunity lock (40 ticks * 50ms) so they can walk past each other
                            self.social_cooldown = 40 
                            break 

        self.update_position()
        self.schedule_loop(50, self.physics_loop)