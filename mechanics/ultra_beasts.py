import random
import math
import tkinter as tk
import uuid

class UltraBeastsMechanics:
    def start_ub_mechanic(self):
        if getattr(self, 'current_state', '') in ['dragged', 'exiting']: return
        if getattr(self, 'ub_cooldown', 0) > 0: return
        if hasattr(self, 'is_global_mechanic_active') and self.is_global_mechanic_active(): return

        name = self.pet_name.lower().replace("_", "").replace("-", "")
        
        # Valid Ultra Beasts
        ub_colors = {
            "nihilego": "#00FFFF",
            "buzzwole": "#FF4500",
            "pheromosa": "#FFFFFF",
            "xurkitree": "#FFD700",
            "xurkillree": "#FFD700",
            "celesteela": "#2E8B57",
            "kartana": "#FFA500",
            "guzzlord": "#000000",
            "necrozma": "#191970",
            "necrozma1": "#191970",
            "necrozma2": "#191970",
            "poipole": "#9370DB",
            "naganadel": "#8A2BE2",
            "stakataka": "#708090",
            "blacephalon": "#FF69B4"
        }
        
        if name not in ub_colors: return

        self.current_state = 'ub_channeling'
        self.ub_timer = 90  # 3 seconds at 30ms approx
        self.ub_cooldown = 120000  # 1 hour
        self.ub_color = ub_colors[name]
        
        # Target for the portal (top 1/6th of screen)
        min_y = self.v_y
        max_y = self.v_y + (self.v_height // 6)
        self.ub_target_x = random.randint(self.v_x + 100, self.v_x + self.v_width - 100)
        self.ub_target_y = random.randint(min_y, max_y)
        
        self.is_facing_right = (self.ub_target_x > self.x)
        self.v_x_velocity = 0.0
        self.v_y_velocity = 0.0

        self._init_ub_vfx()
        self.schedule_loop(30, self.physics_loop)

    def _init_ub_vfx(self):
        if hasattr(self, 'ub_vfx_win') and self.ub_vfx_win and self.ub_vfx_win.winfo_exists():
            return
            
        self.ub_vfx_win = tk.Toplevel(self.window.master)
        self.ub_vfx_win.title("VFX_UB_Ignore")
        self.ub_vfx_win.overrideredirect(True)
        self.ub_vfx_win.attributes('-topmost', True)
        TRANS_COLOR = '#010101'
        self.ub_vfx_win.config(bg=TRANS_COLOR)
        try: self.ub_vfx_win.wm_attributes('-transparentcolor', TRANS_COLOR)
        except: pass
        self.ub_vfx_win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        
        self.ub_canvas = tk.Canvas(self.ub_vfx_win, width=self.v_width, height=self.v_height, bg=TRANS_COLOR, highlightthickness=0)
        self.ub_canvas.pack(fill="both", expand=True)
        self.ub_particles = []
        self.ub_portal = None

    def cancel_ub_arts(self):
        if hasattr(self, 'ub_vfx_win') and self.ub_vfx_win and self.ub_vfx_win.winfo_exists():
            # Only destroy if portal hasn't been fully formed.
            # If portal is active, we let it run independently!
            if not getattr(self, 'ub_portal_active', False):
                self.ub_vfx_win.destroy()
                self.ub_vfx_win = None
                if hasattr(self, 'ub_canvas'): delattr(self, 'ub_canvas')
            else:
                # Detach so it can finish its lifecycle
                pass
            
        for attr in ['ub_timer', 'ub_target_x', 'ub_target_y', 'ub_color', 'ub_particles']:
            if hasattr(self, attr): delattr(self, attr)

        if self.current_state not in ['dragged', 'exiting']:
            self.current_state = 'falling'
            self.v_x_velocity = 0.0
            self.v_y_velocity = 0.0

    def _fsm_ub_channeling(self):
        self.ub_timer -= 1
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        # Spiral absorb particles
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(50, 100)
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        
        # Spiral velocity inwards
        tangent = angle + math.pi/2
        speed_in = random.uniform(2, 5)
        speed_tan = random.uniform(3, 6)
        
        vx = math.cos(tangent) * speed_tan - math.cos(angle) * speed_in
        vy = math.sin(tangent) * speed_tan - math.sin(angle) * speed_in
        
        self._spawn_ub_particle(px, py, vx, vy, 15, self.ub_color)
        self._update_ub_vfx()
        
        # Force idle animation
        self.canvas.itemconfig(self.canvas_image_id, state='normal')
        
        if self.ub_timer <= 0:
            self.current_state = 'ub_shooting'
            self.ub_proj_x = cx
            self.ub_proj_y = cy
            self.ub_timer = 20 # Travel time for projectile
            
        self.schedule_loop(30, self.physics_loop)

    def _fsm_ub_shooting(self):
        self.ub_timer -= 1
        
        cx = self.x - self.v_x + self.size_w/2
        cy = self.y - self.v_y + self.size_h/2
        
        # Projectile logic
        target_cx = self.ub_target_x - self.v_x
        target_cy = self.ub_target_y - self.v_y
        
        progress = 1.0 - (self.ub_timer / 20.0)
        self.ub_proj_x = cx + (target_cx - cx) * progress
        self.ub_proj_y = cy + (target_cy - cy) * progress
        
        # Draw projectile
        self._spawn_ub_particle(self.ub_proj_x, self.ub_proj_y, random.uniform(-2,2), random.uniform(-2,2), 5, self.ub_color, size=6)
        
        self._update_ub_vfx()
        
        if self.ub_timer <= 0:
            self.current_state = 'idle'
            self.ub_portal_active = True
            
            # Explosion
            for _ in range(30):
                ang = random.uniform(0, 2*math.pi)
                spd = random.uniform(3, 10)
                self._spawn_ub_particle(self.ub_proj_x, self.ub_proj_y, math.cos(ang)*spd, math.sin(ang)*spd, 20, self.ub_color, size=4)
                
            # Create Portal
            self.ub_portal = {
                'x': target_cx,
                'y': target_cy,
                'radius': 0.0,
                'max_radius': 40.0,
                'life': 900,  # 30 seconds at ~30 ticks/sec
                'shrink_timer': 150, # 5 seconds to shrink
                'spawn_tick': random.randint(150, 750) # Random time to spawn the pokemon
            }
            
            self._ub_portal_loop()
            
        self.schedule_loop(30, self.physics_loop)

    def _spawn_ub_particle(self, cx, cy, vx, vy, life, color, size=None):
        if not hasattr(self, 'ub_canvas') or not self.ub_canvas.winfo_exists(): return
        if size is None: size = random.choice([2, 3, 4])
        pid = self.ub_canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline="", tags="ub_vfx")
        self.ub_particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'max_size': size})

    def _update_ub_vfx(self):
        if not hasattr(self, 'ub_canvas') or not self.ub_canvas.winfo_exists(): return
        
        new_parts = []
        for p in self.ub_particles:
            p['life'] -= 1
            if p['life'] > 0:
                self.ub_canvas.move(p['id'], p['vx'], p['vy'])
                ratio = p['life'] / p['max_life']
                new_size = max(1, int(p['max_size'] * ratio))
                coords = self.ub_canvas.coords(p['id'])
                if coords:
                    cx = (coords[0] + coords[2])/2
                    cy = (coords[1] + coords[3])/2
                    self.ub_canvas.coords(p['id'], cx-new_size, cy-new_size, cx+new_size, cy+new_size)
                new_parts.append(p)
            else:
                self.ub_canvas.delete(p['id'])
        self.ub_particles = new_parts

    def _ub_portal_loop(self):
        if not hasattr(self, 'ub_canvas') or not self.ub_canvas.winfo_exists() or not self.ub_portal:
            return
            
        portal = self.ub_portal
        
        if portal['life'] > 0:
            portal['life'] -= 1
            if portal['radius'] < portal['max_radius']:
                portal['radius'] += 1.0
                
            if portal['life'] == portal['spawn_tick']:
                self._ub_spawn_rare_pokemon(portal['x'] + self.v_x, portal['y'] + self.v_y)
                
        else:
            portal['shrink_timer'] -= 1
            portal['radius'] -= portal['max_radius'] / 150.0
            
            if portal['shrink_timer'] <= 0 or portal['radius'] <= 0:
                self.ub_portal_active = False
                if hasattr(self, 'ub_vfx_win') and self.ub_vfx_win:
                    self.ub_vfx_win.destroy()
                    self.ub_vfx_win = None
                return
                
        # Draw portal
        self.ub_canvas.delete("ub_portal")
        
        if portal['radius'] > 2:
            colors = ["#FFD700", "#FF4500", "#8A2BE2", "#00FFFF", "#FFFFFF"]
            c1 = colors[(portal['life'] // 10) % len(colors)]
            c2 = colors[((portal['life'] // 10) + 1) % len(colors)]
            
            # Pixelated hexagon or octagon
            cx, cy = portal['x'], portal['y']
            r = portal['radius']
            
            steps = 12
            G = 3
            
            def get_pixelated_polygon(radius):
                pts = []
                last_x, last_y = None, None
                for i in range(steps + 1):
                    a = (i / steps) * 2 * math.pi
                    px = round((cx + math.cos(a) * radius) / G) * G
                    py = round((cy + math.sin(a) * radius) / G) * G
                    if last_x is not None and (px != last_x or py != last_y):
                        if px != last_x and py != last_y:
                            pts.extend([last_x, py])
                        pts.extend([px, py])
                    elif last_x is None:
                        pts.extend([px, py])
                    last_x, last_y = px, py
                return pts
                
            self.ub_canvas.create_polygon(get_pixelated_polygon(r), fill=c1, outline=c2, width=2, tags="ub_portal")
            self.ub_canvas.create_polygon(get_pixelated_polygon(r*0.6), fill="#010101", outline=c1, width=2, tags="ub_portal")

            # Ambient particles
            if random.randint(1, 100) <= 30:
                ang = random.uniform(0, 2*math.pi)
                spd = random.uniform(1, 3)
                self._spawn_ub_particle(cx, cy, math.cos(ang)*spd, math.sin(ang)*spd, 25, c1, size=2)

        self._update_ub_vfx()
        if hasattr(self, 'ub_vfx_win') and self.ub_vfx_win and self.ub_vfx_win.winfo_exists():
            self.ub_vfx_win.after(30, self._ub_portal_loop)

    def _ub_spawn_rare_pokemon(self, global_x, global_y):
        if not hasattr(self, 'game_controller') or not self.game_controller: return
        
        gc = self.game_controller
        if hasattr(gc, 'spawn_pool_species') and gc.spawn_pool_species:
            # Find pokemon below average weight (which means they are rarer than average)
            avg_weight = sum(gc.spawn_pool_weights) / len(gc.spawn_pool_weights)
            rare_pool = [sp for sp, w in zip(gc.spawn_pool_species, gc.spawn_pool_weights) if w <= avg_weight]
            
            if not rare_pool:
                rare_pool = gc.spawn_pool_species
                
            target = random.choice(rare_pool)
        else:
            target = "pikachu"
            
        is_shiny = (random.randint(1, 100) <= 25)
        lvl = random.randint(10, 50)
        
        wild_data = {
            "id": str(uuid.uuid4()), "species": target, "level": lvl, 
            "xp": 0, "is_shiny": is_shiny, "last_evolution_level": lvl,
            "flying_height_pct": 3.0, "xp_boost_expiry": 0
        }
        
        gc.spawn_entity(wild_data, is_wild=True, coords=(global_x, global_y))
