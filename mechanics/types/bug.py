import random

import random
import math

class BugMechanics:
    def check_bug_mechanic(self):
        if getattr(self, 'current_state', 'exiting') in ['exiting', 'dragged', 'webbed']:
            return
            
        if not hasattr(self, 'active_webs'):
            self.active_webs = []
            
        v_width = getattr(self, 'v_width', 1920)
        
        is_left_edge = (self.x - self.v_x < 100)
        is_right_edge = ((self.v_x + self.v_width) - (self.x + self.size_w) < 100)
        
        if getattr(self, 'bug_cooldown', 0) == 0 and (is_left_edge or is_right_edge):
            if __import__('random').randint(1, 100) <= 10:
                self.bug_cooldown = self.get_type_cooldown(18000)
                
                # Corner coordinates
                corner_x = self.v_x if is_left_edge else self.v_x + self.v_width
                is_top_half = (self.y < self.v_y + getattr(self, 'v_height', 1080) / 2)
                corner_y = self.v_y if is_top_half else getattr(self, 'default_floor_y', self.y) + self.size_h
                
                import tkinter as tk
                win = tk.Toplevel(self.window)
                win.title("Deskmon_VFX")
                win.overrideredirect(True)
                win.attributes("-transparentcolor", "white")
                win.attributes("-topmost", True)
                canvas = tk.Canvas(win, bg='white', highlightthickness=0)
                canvas.pack(fill='both', expand=True)
                
                win.geometry(f"400x400+{int(corner_x - 200)}+{int(corner_y - 200)}")
                
                web = {
                    'win': win,
                    'canvas': canvas,
                    'x': corner_x,
                    'y': corner_y,
                    'life': 900,
                    'pieces': []
                }
                
                cx, cy = 200, 200
                for r in [40, 80, 120, 160]:
                    for i in range(16):
                        angle1 = i * (math.pi * 2 / 16)
                        angle2 = (i + 1) * (math.pi * 2 / 16)
                        web['pieces'].append({
                            'type': 'line',
                            'coords': [cx + r * math.cos(angle1), cy + r * math.sin(angle1), cx + r * math.cos(angle2), cy + r * math.sin(angle2)],
                            'drop_time': __import__('random').randint(50, 150),
                            'draw_time': __import__('random').randint(0, 150)
                        })
                for i in range(16):
                    angle = i * (math.pi * 2 / 16)
                    web['pieces'].append({
                        'type': 'line',
                        'coords': [cx, cy, cx + 180 * math.cos(angle), cy + 180 * math.sin(angle)],
                        'drop_time': __import__('random').randint(50, 150),
                        'draw_time': __import__('random').randint(0, 50)
                    })
                    
                self.active_webs.append(web)
                
                def animate_web(w):
                    if w['life'] <= 0:
                        try: w['win'].destroy()
                        except: pass
                        if w in self.active_webs: self.active_webs.remove(w)
                        return
                    
                    try:
                        if not w['win'].winfo_exists(): return
                    except: return
                    
                    w['life'] -= 1
                    w['canvas'].delete('all')
                    
                    for p in w['pieces']:
                        if (900 - w['life']) < p['draw_time']:
                            continue # Not woven yet
                        if w['life'] < p['drop_time']:
                            continue # Piece has broken off
                        
                        crd = p['coords']
                        w['canvas'].create_line(crd[0], crd[1], crd[2], crd[3], fill="#AAAAAA", width=4)
                        w['canvas'].create_line(crd[0]+1, crd[1]+1, crd[2]+1, crd[3]+1, fill="#EEEEEE", width=2)
                        
                    self.window.after(30, lambda: animate_web(w))
                    
                animate_web(web)
                
        # Collision
        if getattr(self, 'get_all_pets', None):
            for other in self.get_all_pets():
                if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                
                in_web = False
                for web in self.active_webs:
                    if abs((other.x + other.size_w/2) - web['x']) < 200 and abs((other.y + other.size_h) - web['y']) < 200:
                        in_web = True
                        other.current_web = web
                        break
                        
                if in_web:
                    if hasattr(other, 'speed') and other.current_state in ['walking', 'running', 'burning', 'poisoned']:
                        correction = -(other.speed * 0.7) if getattr(other, 'is_facing_right', True) else (other.speed * 0.7)
                        other.x += correction
                        
                    other.web_stuck_timer = getattr(other, 'web_stuck_timer', 0) + 1
                    if other.web_stuck_timer > 150: # 5 seconds
                        if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                        other.current_state = 'webbed'

                        
    def _fsm_webbed(self):
        if getattr(self, 'current_state', 'exiting') == 'exiting': return
        self.v_x_velocity = 0
        
        if hasattr(self, 'animator'): self.animator.update_animation('idle', getattr(self, 'is_facing_right', True), self.canvas_image_id, True, getattr(self, 'frame_rate_idle', 100), scale_mod=getattr(self, 'scale', 1.0))
        
        cw = getattr(self, 'current_web', None)
        if cw and cw.get('life', 0) > 0:
            cx = self.size_w / 2
            cy = self.size_h / 2
            rx = min(self.size_w, self.size_h) / 2 - 5
            ry = rx * 0.5
            self.canvas.create_line(cx - rx, cy - ry, cx + rx, cy + ry, fill="#AAAAAA", width=8, tags="vfx")
            self.canvas.create_line(cx - rx, cy + ry, cx + rx, cy - ry, fill="#AAAAAA", width=8, tags="vfx")
            self.canvas.create_line(cx - rx+2, cy - ry+2, cx + rx-2, cy + ry-2, fill="#EEEEEE", width=4, tags="vfx")
            self.canvas.create_line(cx - rx+2, cy + ry-2, cx + rx-2, cy - ry+2, fill="#EEEEEE", width=4, tags="vfx")
        else:
            self.current_state = 'falling'
            self.web_stuck_timer = 0
            
            import tkinter as tk
            import random
            burst_win = tk.Toplevel(self.window)
            burst_win.title("Deskmon_VFX")
            burst_win.overrideredirect(True)
            burst_win.attributes("-transparentcolor", "white")
            burst_win.attributes("-topmost", True)
            b_canvas = tk.Canvas(burst_win, bg='white', highlightthickness=0)
            b_canvas.pack(fill='both', expand=True)
            
            w_w, w_h = 100, 100
            px, py = self.x + self.size_w/2, self.y + self.size_h/2
            burst_win.geometry(f"{w_w}x{w_h}+{int(px - w_w/2)}+{int(py - w_h/2)}")
            
            particles = []
            for _ in range(15):
                angle = random.uniform(0, 6.28)
                speed = random.uniform(2, 6)
                particles.append({
                    'x': w_w/2, 'y': w_h/2,
                    'vx': __import__('math').cos(angle) * speed,
                    'vy': __import__('math').sin(angle) * speed,
                    'life': random.randint(10, 20)
                })
                
            def animate_burst():
                if not burst_win.winfo_exists(): return
                alive = False
                b_canvas.delete('all')
                for p in particles:
                    p['life'] -= 1
                    if p['life'] > 0:
                        alive = True
                        p['x'] += p['vx']
                        p['y'] += p['vy']
                        b_canvas.create_rectangle(p['x']-3, p['y']-3, p['x']+3, p['y']+3, fill="#EEEEEE", outline="")
                        b_canvas.create_rectangle(p['x']-2, p['y']-2, p['x']+2, p['y']+2, fill="#FFFFFF", outline="")
                
                if alive:
                    self.window.after(30, animate_burst)
                else:
                    burst_win.destroy()
                    
            animate_burst()
            
        self.update_position()
        self.schedule_loop(20, self.physics_loop)