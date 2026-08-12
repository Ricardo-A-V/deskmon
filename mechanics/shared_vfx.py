import random
import math
import os

class SharedVFX:
    def _draw_pixel_circle_bbox(self, canvas, x1, y1, x2, y2, **kwargs):
        import math
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        r = abs(x2 - x1) / 2
        fill = kwargs.get('fill', '')
        outline = kwargs.get('outline', '')
        tags = kwargs.get('tags', '')
        width = kwargs.get('width', 1)
        p_size = 6
        if r <= p_size:
            return canvas.create_rectangle(cx-r, cy-r, cx+r, cy+r, fill=fill, outline=outline, width=width, tags=tags)
        
        r = int(r)
        half_pts = []
        for y in range(-r, r, p_size):
            y_top = y
            y_bottom = min(y + p_size, r)
            eval_y = min(abs(y_top), abs(y_bottom))
            try: x = math.sqrt(r**2 - eval_y**2)
            except: x = 0
            x = round(x / p_size) * p_size
            if x == 0: x = p_size
            half_pts.extend([x, y_top, x, y_bottom])
            
        pts = []
        for i in range(0, len(half_pts), 2):
            pts.extend([cx + half_pts[i], cy + half_pts[i+1]])
        for i in range(len(half_pts)-2, -1, -2):
            pts.extend([cx - half_pts[i], cy + half_pts[i+1]])
            
        return canvas.create_polygon(*pts, fill=fill, outline=outline, width=width, tags=tags, smooth=False)

    def _draw_pixel_polygon(self, canvas, *pts, **kwargs):
        import random
        fill = kwargs.get('fill', '')
        outline = kwargs.get('outline', '')
        tags = kwargs.get('tags', '')
        p_size = 6
        
        uid = f"pix_poly_{random.randint(10000, 99999)}"
        all_tags = (tags, uid) if tags else (uid,)
        
        flat_pts = []
        for p in pts:
            if isinstance(p, (list, tuple)): flat_pts.extend(p)
            else: flat_pts.append(p)
                
        edges = []
        for i in range(0, len(flat_pts), 2):
            x1, y1 = flat_pts[i], flat_pts[i+1]
            nx, ny = flat_pts[(i+2)%len(flat_pts)], flat_pts[(i+3)%len(flat_pts)]
            edges.append((x1, y1, nx, ny))
            
        min_y = min(flat_pts[1::2])
        max_y = max(flat_pts[1::2])
        
        min_y = round(min_y / p_size) * p_size
        max_y = round(max_y / p_size) * p_size
        
        for y in range(int(min_y), int(max_y) + p_size, p_size):
            y_mid = y + p_size / 2.0
            intersects = []
            for ex1, ey1, ex2, ey2 in edges:
                if (ey1 <= y_mid < ey2) or (ey2 <= y_mid < ey1):
                    t = (y_mid - ey1) / (ey2 - ey1)
                    ix = ex1 + t * (ex2 - ex1)
                    intersects.append(ix)
            
            intersects.sort()
            for i in range(0, len(intersects)-1, 2):
                x_start = round(intersects[i] / p_size) * p_size
                x_end = round(intersects[i+1] / p_size) * p_size
                if x_start == x_end: x_end += p_size
                
                canvas.create_rectangle(x_start, y, x_end, y + p_size, fill=fill, outline="", tags=all_tags)
        return uid

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
        
        # Generate 6-9 sparks of light
        for _ in range(random.randint(6, 9)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            size = random.choice([1, 2])
            color = random.choice(["#FFB6C1", "#FF69B4", "#FF1493", "#F08080", "#FFFFFF"]) # Range of pinks and white
            
            pid = self.canvas.create_rectangle(cx-size, cy-size, cx+size, cy+size, fill=color, outline=color, tags="vfx_fairy")
            particles.append({'id': pid, 'vx': vx, 'vy': vy, 'life': random.randint(20, 35)})
            
        def animate_sparkles():
            if getattr(self, 'current_state', 'exiting') == 'exiting': return
            
            alive_count = 0
            for p in particles:
                if p['life'] > 0:
                    self.canvas.move(p['id'], p['vx'], p['vy'])
                    
                    # Magical physics: Horizontal braking and constant vertical elevation
                    p['vx'] *= 0.85 
                    p['vy'] *= 0.85 
                    p['vy'] -= 0.3 
                    
                    p['life'] -= 1
                    
                    # Stroboscopic blinking in its last frames of life
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
