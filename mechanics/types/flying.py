import random
import math

class FlyingMechanics:
    def check_flying_mechanic(self):
        if not hasattr(self, 'whirlwinds'):
            self.whirlwinds = []
            
        if getattr(self, 'flying_cooldown', 0) == 0 and random.randint(1, 100) <= 10:
            self.flying_cooldown = 18000
            wx = self.x + self.size_w/2
            wy = self.y + self.size_h
            
            import tkinter as tk
            win = tk.Toplevel(self.window)
            win.title("Deskmon_VFX")
            win.overrideredirect(True)
            win.attributes("-transparentcolor", "white")
            win.attributes("-topmost", True)
            canvas = tk.Canvas(win, bg='white', highlightthickness=0)
            canvas.pack(fill='both', expand=True)
            
            w = {
                'win': win,
                'canvas': canvas,
                'x': wx,
                'y': wy,
                'vx': random.choice([-8.0, 8.0]),
                'life': 80,
                'anim_step': 0,
                'debris': [{'xo': random.uniform(-20, 20), 'yo': random.uniform(0, 60), 's': random.uniform(2, 5)} for _ in range(5)]
            }
            self.whirlwinds.append(w)
            
            def animate_whirlwind(w):
                if w['life'] <= 0:
                    try: w['win'].destroy()
                    except: pass
                    if w in self.whirlwinds: self.whirlwinds.remove(w)
                    return
                    
                try:
                    if not w['win'].winfo_exists(): return
                except:
                    return
                    
                w['x'] += w['vx']
                w['life'] -= 1
                w['anim_step'] += 1
                
                width, height = 80, 80
                w['win'].geometry(f"{width}x{height}+{int(w['x'] - width/2)}+{int(w['y'] - height)}")
                w['canvas'].delete('all')
                step = w['anim_step']
                
                colors = ["#E0E0E0", "#CCCCCC", "#F0F0F0"]
                for i in range(7):
                    layer_y = 65 - i * 9
                    layer_w = 12 + i * 8
                    offset = math.sin(step * 0.4 + i) * (5 + i * 2)
                    
                    w['canvas'].create_rectangle(
                        40 - layer_w/2 + offset, layer_y,
                        40 + layer_w/2 + offset, layer_y + 9,
                        fill=colors[i % len(colors)], outline=""
                    )
                    
                    w['canvas'].create_rectangle(
                        40 - layer_w/2 + offset + 2, layer_y + 2,
                        40, layer_y + 7,
                        fill="#999999", outline=""
                    )
                    
                for deb in w['debris']:
                    deb['yo'] = (deb['yo'] - 4) % 80
                    angle = step * 0.5 + deb['yo']
                    dx = math.sin(angle) * (15 + (80 - deb['yo']) * 0.3)
                    w['canvas'].create_rectangle(
                        40 + dx, deb['yo'],
                        40 + dx + deb['s'], deb['yo'] + deb['s'],
                        fill="#888888", outline=""
                    )
                    
                if getattr(self, 'get_all_pets', None):
                    for other in self.get_all_pets():
                        if other == self or getattr(other, 'is_egg', False) or other.current_state in ['exiting', 'dragged', 'poisoned', 'burning', 'frozen', 'asleep', 'paralyzed', 'webbed', 'bubbled', 'tk_lifted', 'dragon_fear', 'dragon_flee']: continue
                        
                        dx = abs((other.x + other.size_w/2) - w['x'])
                        dy = abs((other.y + other.size_h/2) - (w['y'] - height/2))
                        
                        if dx < 40 and dy < 40:
                            if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                            other.current_state = 'thrown'
                            other.v_y_velocity = -50.0 
                            other.v_x_velocity = random.uniform(-25, 25)
                            
                self.window.after(30, lambda: animate_whirlwind(w))
                
            animate_whirlwind(w)
