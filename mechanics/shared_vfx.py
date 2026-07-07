import random
import math
import os

class SharedVFX:
    def show_dirt_vfx(self):
        particles = []
        cx = self.size_w // 2
        is_inverted = getattr(self, 'gravity_inverted', False)
        cy = 5 if is_inverted else self.size_h - 5 
        
        for _ in range(random.randint(3, 4)):
            angle = random.choice([
                random.uniform(math.pi + 0.4, math.pi + 0.9),      
                random.uniform(2 * math.pi - 0.9, 2 * math.pi - 0.4) 
            ])
            if is_inverted: angle = 2 * math.pi - angle
                
            speed = random.uniform(6.0, 10.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            if is_inverted: vy = abs(vy)
            
            size = random.choice([2, 3, 4]) 
            color = random.choice(["#3E2723", "#4E342E", "#5D4037", "#8D6E63", "#795548"])
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_dirt")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(12, 18)})
            
        def animate_dirt():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    p['vy'] += -0.9 if is_inverted else 0.9
                    p['life'] -= 1
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
            if alive_count > 0:
                self.schedule_loop(30, animate_dirt)
                
        animate_dirt()

    def show_fairy_sparkles_vfx(self):
        particles = []
        cx = self.size_w // 2
        cy = self.size_h // 2
        
        # Generar 6-9 chispas de luz
        for _ in range(random.randint(6, 9)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([1, 2])
            color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493", "#F08080", "#FFFFFF"]) # Gama de rosas y blanco
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_fairy")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(20, 35)})
            
        def animate_sparkles():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    
                    # Físicas mágicas: Frenado horizontal y elevación vertical constante
                    p['vx'] *= 0.85 
                    p['vy'] *= 0.85 
                    p['vy'] -= 0.3 
                    
                    p['life'] -= 1
                    
                    # Parpadeo estroboscópico en sus últimos frames de vida
                    if p['life'] < 10 and p['life'] % 2 == 0:
                        self.canvas.itemconfig(p['id'], state='hidden')
                    else:
                        self.canvas.itemconfig(p['id'], state='normal')
                        
                    alive_count += 1
                elif p['life'] == 0:
                    self.canvas.delete(p['id'])
                    p['life'] = -1
                    
            if alive_count > 0:
                self.schedule_loop(30, animate_sparkles)
                
        animate_sparkles()


    def show_time_distortion_vfx(self, is_master=False):
        try:
            import math
            import random
            
            color = "#4B0082" # Indigo
            
            cx = getattr(self, 'size_w', 64) // 2
            cy = getattr(self, 'size_h', 64) // 2
            
            particles = []
            count = 8 if is_master else 3
            max_radius = getattr(self, 'size_w', 64) if is_master else getattr(self, 'size_w', 64) // 2
            
            for _ in range(count):
                angle = random.uniform(0, math.pi * 2)
                size = 3 if is_master else 2
                pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_time")
                
                particles.append({
                    'id': pid,
                    'angle': angle,
                    'radius': 0.0,
                    'speed_r': random.uniform(2.0, 4.0) if is_master else random.uniform(1.0, 2.5),
                    'speed_theta': random.uniform(0.15, 0.4) * random.choice([1, -1]),
                    'life': 1.0,
                    'size': size
                })
                
            def animate_distortion():
                if getattr(self, 'current_state', 'exiting') == 'exiting': return
                
                alive_count = 0
                for p in particles:
                    if p['life'] > 0:
                        p['angle'] += p['speed_theta']
                        p['radius'] += p['speed_r']
                        
                        if p['radius'] > max_radius:
                            self.canvas.delete(p['id'])
                            p['life'] = -1
                        else:
                            alive_count += 1
                            x = cx + math.cos(p['angle']) * p['radius']
                            y = cy + math.sin(p['angle']) * p['radius']
                            sz = p['size']
                            self.canvas.coords(p['id'], x-sz, y-sz, x+sz, y+sz)
                
                if alive_count > 0:
                    self.schedule_loop(30, animate_distortion)
                    
            animate_distortion()
        except Exception:
            pass
