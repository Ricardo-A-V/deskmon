import math
import random
import tkinter as tk


class RayquazaDeoxysDuoMechanics:
    """Modular two-Pokemon encounter for Rayquaza and any Deoxys form."""

    DUO_STATES = ("rayquaza_deoxys_duo", "rayquaza_deoxys_duo_partner")
    DEOXYS_FORMS = {"deoxys", "deoxys1", "deoxys2", "deoxys3"}
    ATTACKS = ("ray_beam", "psychic_orbs", "tackle")
    BEAM_SPEED = 150.0
    BEAM_DEFENSE_OVERSHOOT = 42.0
    ORB_SPEED_MULTIPLIER = 1.5
    MOVE_TICKS = 20
    TACKLE_SPEED = 100.0
    COLORS = {
        "ray": ("#FFFFFF", "#FFD21F", "#FF8C00"),
        "deoxys": ("#FFFFFF", "#00E5FF", "#0066FF"),
        "trail_ray": ("#FFFFFF", "#FFD21F", "#FF8C00"),
        "trail_deoxys": ("#FF4500", "#00FFFF", "#FFA500"),
    }

    def _duo_name(self, pet):
        return self._duo_normalize(pet.pet_name)

    def _duo_normalize(self, name):
        return name.lower().replace("_", "").replace("-", "").replace(" ", "")

    def _duo_partner(self, rayquaza):
        if not getattr(rayquaza, "get_all_pets", None):
            return None
        for pet in rayquaza.get_all_pets():
            if pet is rayquaza:
                continue
            if self._duo_name(pet) in self.DEOXYS_FORMS and pet.current_state in ("idle", "walking"):
                return pet
        return None

    def start_rayquaza_deoxys_duo(self):
        if self._duo_name(self) != "rayquaza":
            return False
        deoxys = self._duo_partner(self)
        if not deoxys:
            return False

        context = {
            "ray": self,
            "deoxys": deoxys,
            "phase": "attack",
            "timer": 0,
            "attack_index": 0,
            "attacks": [self.ATTACKS[0]] + random.choices(
                self.ATTACKS,
                weights=(0.325, 0.325, 0.35),
                k=random.randint(14, 24),
            ),
            "attack": None,
            "attack_data": {},
            "last_attacker": None,
            "winner": None,
            "particles": [],
            "orb_particles": [],
            "impact_particles": [],
            "projectiles": [],
            "projectile_serial": 0,
            "hit_ids": set(),
        }
        self.rayquaza_deoxys_duo = context
        deoxys.rayquaza_deoxys_duo = context
        self.current_state = "rayquaza_deoxys_duo"
        deoxys.current_state = "rayquaza_deoxys_duo_partner"
        cooldown = self.get_legendary_cooldown(72000)
        self.rayquaza_deoxys_cooldown = cooldown
        self.rayquaza_cooldown = cooldown
        deoxys.rayquaza_deoxys_cooldown = cooldown
        deoxys.deoxys_cooldown = cooldown
        self._duo_make_vfx()
        self._duo_begin_attack(context, context["attacks"][0])
        self.schedule_loop(30, self.physics_loop)
        return True

    def cancel_rayquaza_deoxys_duo(self):
        context = getattr(self, "rayquaza_deoxys_duo", None)
        if not context:
            context = getattr(getattr(self, "rayquaza_deoxys_duo_partner", None), "rayquaza_deoxys_duo", None)
        if not context:
            context = getattr(self, "rayquaza_deoxys_context", None)
        if not context:
            return

        ray = context.get("ray")
        deoxys = context.get("deoxys")
        vfx = context.get("vfx")
        canvas = context.get("canvas")
        if canvas and canvas.winfo_exists():
            for particle in (
                context.get("particles", [])
                + context.get("orb_particles", [])
                + context.get("impact_particles", [])
            ):
                canvas.delete(particle["id"])
            for projectile in context.get("projectiles", []):
                canvas.delete(projectile["tag"])
            for tag in (
                "duo_beam_current", "duo_orb_current", "duo_orb_trail",
                "duo_beam_burst", "duo_orb_burst", "duo_impact", "duo_burst", "duo_charge",
            ):
                canvas.delete(tag)
            context["particles"] = []
            context["orb_particles"] = []
            context["impact_particles"] = []
            context["projectiles"] = []
        if vfx and vfx.winfo_exists():
            vfx.destroy()
        context["vfx"] = None
        winner = context.get("winner")
        loser = context.get("loser")
        for pet in (ray, deoxys):
            if pet:
                if context.get("ending"):
                    pet.surface_angle = 0
                    pet.x = max(pet.v_x + 10, min(pet.x, pet.v_x + pet.v_width - pet.size_w - 10))
                    if pet is loser:
                        self._duo_start_final_loss(
                            pet,
                            context.get("final_push_direction", (1.0, 0.0)),
                        )
                    elif pet is ray:
                        pet.v_x_velocity = 0.0
                        pet.v_y_velocity = 0.0
                        self._duo_start_winner_motion(pet, "rayquaza")
                    else:
                        pet.v_x_velocity = 0.0
                        pet.v_y_velocity = 8.0
                        self._duo_start_winner_motion(pet, "deoxys")
                elif getattr(pet, "current_state", "") in (*self.DUO_STATES, "thrown"):
                    pet.current_state = "falling"
                    pet.x = max(pet.v_x + 10, min(pet.x, pet.v_x + pet.v_width - pet.size_w - 10))
                    pet.y = max(pet.v_y + 10, min(pet.y, pet.v_y + pet.v_height - pet.size_h - 10))
                    pet.v_x_velocity = 0.0
                    pet.v_y_velocity = min(0.0, getattr(pet, "v_y_velocity", 0.0))
                    pet.surface_angle = 0
                    pet.schedule_loop(30, pet.physics_loop)
                pet.rayquaza_deoxys_duo = None
                pet.rayquaza_deoxys_context = None

    def _duo_start_final_loss(self, pet, direction):
        direction_x, direction_y = direction
        direction_length = math.hypot(direction_x, direction_y) or 1.0
        direction_x /= direction_length
        direction_y /= direction_length
        target_x = pet.x
        target_y = pet.target_floor_y if self._duo_name(pet) == "rayquaza" else pet.default_floor_y
        boundary_distances = []
        if direction_x < 0:
            boundary_distances.append((pet.v_x - pet.size_w - 40 - pet.x) / direction_x)
        elif direction_x > 0:
            boundary_distances.append((pet.v_x + pet.v_width + 40 - pet.x) / direction_x)
        if direction_y < 0:
            boundary_distances.append((pet.v_y - pet.size_h - 40 - pet.y) / direction_y)
        elif direction_y > 0:
            boundary_distances.append((pet.v_y + pet.v_height + 40 - pet.y) / direction_y)
        travel_distance = max(500.0, min(distance for distance in boundary_distances if distance > 0))
        exit_x = pet.x + direction_x * travel_distance
        exit_y = pet.y + direction_y * travel_distance
        pet._duo_final_return = {
            "phase": "launch",
            "ticks": 18,
            "launch_ticks": 18,
            "launch_start_x": pet.x,
            "launch_start_y": pet.y,
            "launch_x": exit_x,
            "launch_y": exit_y,
            "return_ticks": 120,
            "start_x": exit_x,
            "start_y": exit_y,
            "target_x": target_x,
            "target_y": target_y,
            "rotation_speed": 32.0 if direction_x >= 0 else -32.0,
        }
        pet.current_state = "duo_final_loss"
        pet.surface_angle = 0
        pet.v_x_velocity = 0.0
        pet.v_y_velocity = 0.0
        pet.x = exit_x
        pet.y = exit_y
        pet.update_position()
        pet.schedule_loop(30, self._duo_tick_final_loss, pet)

    def _duo_tick_final_loss(self, pet):
        data = getattr(pet, "_duo_final_return", None)
        if not data or not pet.window.winfo_exists():
            return

        if data["phase"] == "launch":
            progress = 1.0 - (data["ticks"] / data["launch_ticks"])
            eased = 1.0 - (1.0 - progress) * (1.0 - progress)
            pet.x = data["launch_start_x"] + (data["launch_x"] - data["launch_start_x"]) * eased
            pet.y = data["launch_start_y"] + (data["launch_y"] - data["launch_start_y"]) * eased
            pet.surface_angle = (pet.surface_angle + data["rotation_speed"]) % 360
            data["ticks"] -= 1
            pet.update_position()
            if data["ticks"] > 0:
                pet.schedule_loop(30, self._duo_tick_final_loss, pet)
                return
            data["phase"] = "away"
            data["ticks"] = 500
            pet.x = data["launch_x"]
            pet.y = data["launch_y"]
            pet.surface_angle = 0

        if data["phase"] == "away":
            data["ticks"] -= 1
            pet.update_position()
            if data["ticks"] > 0:
                pet.schedule_loop(30, self._duo_tick_final_loss, pet)
                return
            data["phase"] = "returning"
            data["ticks"] = data["return_ticks"]
            pet.current_state = "walking"
            pet._duo_final_returning = True
            pet.is_facing_right = data["target_x"] > data["start_x"]

        progress = 1.0 - (data["ticks"] / data["return_ticks"])
        eased = progress * progress * (3.0 - 2.0 * progress)
        pet.x = data["start_x"] + (data["target_x"] - data["start_x"]) * eased
        pet.y = data["start_y"] + (data["target_y"] - data["start_y"]) * eased
        data["ticks"] -= 1
        pet.update_position()
        if data["ticks"] > 0:
            pet.schedule_loop(30, self._duo_tick_final_loss, pet)
            return

        pet.x = data["target_x"]
        pet.y = data["target_y"]
        pet.floor_y = data["target_y"]
        pet.v_x_velocity = 0.0
        pet.v_y_velocity = 0.0
        pet.surface_angle = 0
        pet.current_state = "idle"
        pet._duo_final_returning = False
        pet.update_position()
        pet._duo_final_return = None
        pet.schedule_loop(50, pet.physics_loop)

    def _duo_start_winner_motion(self, pet, kind):
        pet.current_state = (
            "duo_final_winner_rayquaza"
            if kind == "rayquaza"
            else "duo_final_winner_deoxys"
        )
        pet.surface_angle = 0
        pet.v_x_velocity = 0.0
        pet.v_y_velocity = 0.0
        pet.schedule_loop(30, self._duo_tick_winner_motion, pet, kind)

    def _duo_tick_winner_motion(self, pet, kind):
        if not pet.window.winfo_exists():
            return
        target_y = pet.target_floor_y if kind == "rayquaza" else pet.default_floor_y
        step = 4.0 if kind == "rayquaza" else 8.0
        delta = target_y - pet.y
        if abs(delta) <= step:
            pet.y = target_y
            pet.floor_y = target_y
            pet.v_x_velocity = 0.0
            pet.v_y_velocity = 0.0
            pet.surface_angle = 0
            pet.current_state = "idle"
            pet.update_position()
            pet.schedule_loop(50, pet.physics_loop)
            return
        pet.y += step if delta > 0 else -step
        pet.floor_y = pet.y
        pet.surface_angle = 0
        pet.update_position()
        pet.schedule_loop(30, self._duo_tick_winner_motion, pet, kind)

    def _duo_make_vfx(self):
        context = self.rayquaza_deoxys_duo
        win = tk.Toplevel(self.window.master)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        bg = "#010101"
        win.config(bg=bg)
        try:
            win.wm_attributes("-transparentcolor", bg)
        except tk.TclError:
            pass
        win.geometry(f"{self.v_width}x{self.v_height}+{self.v_x}+{self.v_y}")
        context["vfx"] = win
        context["canvas"] = tk.Canvas(win, width=self.v_width, height=self.v_height, bg=bg, highlightthickness=0)
        context["canvas"].pack()

    def _duo_alive(self, context):
        return (
            context
            and context.get("ray")
            and context.get("deoxys")
            and context["ray"].window.winfo_exists()
            and context["deoxys"].window.winfo_exists()
            and context["ray"].current_state in self.DUO_STATES
            and context["deoxys"].current_state in self.DUO_STATES
        )

    def _duo_point(self, pet):
        return pet.x + pet.size_w / 2, pet.y + pet.size_h / 2

    def _duo_move(self, pet, x, y, speed=24.0):
        x = max(pet.v_x + 10, min(x, pet.v_x + pet.v_width - pet.size_w - 10))
        y = max(pet.v_y + 10, min(y, pet.v_y + pet.v_height - pet.size_h - 10))
        dx, dy = x - pet.x, y - pet.y
        distance = math.hypot(dx, dy)
        if distance <= speed or distance == 0:
            pet.x, pet.y = x, y
            return True
        pet.x += dx / distance * speed
        pet.y += dy / distance * speed
        return False

    def _duo_begin_move(self, context):
        move_data = {}
        for key in ("ray", "deoxys"):
            pet = context[key]
            start_x, start_y = pet.x, pet.y
            min_x = pet.v_x + 60
            max_x = pet.v_x + pet.v_width - pet.size_w - 60
            min_y = pet.v_y + 40
            max_y = pet.v_y + pet.v_height // 2
            target_x, target_y = start_x, start_y
            for _ in range(12):
                target_x = random.uniform(min_x, max_x)
                target_y = random.uniform(min_y, max_y)
                if math.hypot(target_x - start_x, target_y - start_y) >= 150:
                    break
            dx, dy = target_x - start_x, target_y - start_y
            length = math.hypot(dx, dy) or 1.0
            bend = random.choice((-1.0, 1.0)) * random.uniform(60.0, 110.0)
            control_x = (start_x + target_x) / 2 - dy / length * bend
            control_y = (start_y + target_y) / 2 + dx / length * bend
            move_data[key] = {
                "start": (start_x, start_y),
                "control": (control_x, control_y),
                "target": (target_x, target_y),
                "progress": 0.0,
            }
        ray_target = move_data["ray"]["target"]
        deoxys_target = move_data["deoxys"]["target"]
        target_distance = math.hypot(
            deoxys_target[0] - ray_target[0],
            deoxys_target[1] - ray_target[1],
        )
        minimum_distance = max(
            220.0,
            (context["ray"].size_w + context["deoxys"].size_w) * 0.9,
        )
        if target_distance < minimum_distance:
            for _ in range(12):
                pet = context["deoxys"]
                target_x = random.uniform(pet.v_x + 60, pet.v_x + pet.v_width - pet.size_w - 60)
                target_y = random.uniform(pet.v_y + 40, pet.v_y + pet.v_height // 2)
                if math.hypot(target_x - ray_target[0], target_y - ray_target[1]) >= minimum_distance:
                    move_data["deoxys"]["target"] = (target_x, target_y)
                    break
        context["move_data"] = move_data

    def _duo_tick_move(self, context):
        for key in ("ray", "deoxys"):
            pet = context[key]
            data = context["move_data"][key]
            data["progress"] = min(1.0, data["progress"] + 1.0 / self.MOVE_TICKS)
            progress = data["progress"]
            inverse = 1.0 - progress
            start_x, start_y = data["start"]
            control_x, control_y = data["control"]
            target_x, target_y = data["target"]
            x = inverse * inverse * start_x + 2 * inverse * progress * control_x + progress * progress * target_x
            y = inverse * inverse * start_y + 2 * inverse * progress * control_y + progress * progress * target_y
            pet.x = max(pet.v_x + 10, min(x, pet.v_x + pet.v_width - pet.size_w - 10))
            pet.y = max(pet.v_y + 10, min(y, pet.v_y + pet.v_height - pet.size_h - 10))

    def _duo_trail(self, context):
        canvas = context.get("canvas")
        if not canvas:
            return
        for pet, colors in ((context["ray"], self.COLORS["trail_ray"]), (context["deoxys"], self.COLORS["trail_deoxys"])):
            x, y = self._duo_point(pet)
            particle = {
                "id": canvas.create_rectangle(
                    x - self.v_x - 1, y - self.v_y - 1, x - self.v_x + 1, y - self.v_y + 1,
                    fill=random.choice(colors), outline=""
                ),
                "life": 17,
            }
            context["particles"].append(particle)
        alive = []
        for particle in context["particles"]:
            particle["life"] -= 1
            if particle["life"] > 0:
                alive.append(particle)
            else:
                canvas.delete(particle["id"])
        context["particles"] = alive

        orb_alive = []
        for particle in context["orb_particles"]:
            particle["life"] -= 1
            if particle["life"] > 0:
                if particle.get("vx") or particle.get("vy"):
                    canvas.move(particle["id"], particle.get("vx", 0), particle.get("vy", 0))
                orb_alive.append(particle)
            else:
                canvas.delete(particle["id"])
        context["orb_particles"] = orb_alive

        impact_alive = []
        for particle in context["impact_particles"]:
            particle["life"] -= 1
            if particle["life"] > 0:
                bbox = particle["bbox"]
                grow = particle["grow"]
                particle["bbox"] = (bbox[0] - grow, bbox[1] - grow, bbox[2] + grow, bbox[3] + grow)
                canvas.delete(particle["id"])
                if particle["ring"]:
                    particle["id"] = self._draw_pixel_circle_bbox(
                        canvas, *particle["bbox"], outline=particle["color"], width=4, tags="duo_impact"
                    )
                else:
                    particle["id"] = self._draw_pixel_circle_bbox(
                        canvas, *particle["bbox"], fill=particle["color"], outline="", tags="duo_impact"
                    )
                impact_alive.append(particle)
            else:
                canvas.delete(particle["id"])
        context["impact_particles"] = impact_alive

    def _duo_set_form(self, deoxys, form):
        target = {"base": "deoxys", "attack": "deoxys_1", "defense": "deoxys_2", "speed": "deoxys_3"}[form]
        if self._duo_name(deoxys) != self._duo_normalize(target):
            deoxys.swap_form_generic(target, ["#FF4500", "#00FFFF", "#FFA500"])
        deoxys.current_state = "rayquaza_deoxys_duo_partner"

    def _duo_spawn_line(self, context, start, end, colors, widths=(38, 24, 8), tag="duo_beam_current"):
        canvas = context["canvas"]
        canvas.delete(tag)
        x1, y1 = start[0] - self.v_x, start[1] - self.v_y
        x2, y2 = end[0] - self.v_x, end[1] - self.v_y
        for color, width in zip(colors, widths):
            canvas.create_line(x1, y1, x2, y2, fill=color, width=width, capstyle=tk.ROUND, tags=tag)

    def _duo_screen_endpoint(self, start, target):
        dx, dy = target[0] - start[0], target[1] - start[1]
        if dx == 0 and dy == 0:
            dx = 1.0
        scales = []
        if dx < 0:
            scales.append((self.v_x - start[0]) / dx)
        elif dx > 0:
            scales.append((self.v_x + self.v_width - start[0]) / dx)
        if dy < 0:
            scales.append((self.v_y - start[1]) / dy)
        elif dy > 0:
            scales.append((self.v_y + self.v_height - start[1]) / dy)
        scale = min(value for value in scales if value > 0)
        return start[0] + dx * scale, start[1] + dy * scale

    def _duo_face_each_other(self, context):
        ray, deoxys = context["ray"], context["deoxys"]
        for first, second in ((ray, deoxys), (deoxys, ray)):
            dx = second.x - first.x
            dy = second.y - first.y
            first.is_facing_right = dx >= 0
            tilt = math.degrees(math.atan2(-dy, max(1.0, abs(dx))))
            first.surface_angle = tilt if first.is_facing_right else -tilt

    def _duo_spawn_orb(self, context, x, y, previous_x, previous_y, tag="duo_orb_current"):
        canvas = context["canvas"]
        x -= self.v_x
        y -= self.v_y
        previous_x -= self.v_x
        previous_y -= self.v_y
        if hasattr(self, "_draw_pixel_circle_bbox"):
            self._draw_pixel_circle_bbox(
                canvas, x - 28, y - 28, x + 28, y + 28,
                fill="#7E22CE", outline="#FF4FA3", width=3, tags=tag
            )
            self._draw_pixel_circle_bbox(
                canvas, x - 20, y - 20, x + 20, y + 20,
                fill="#C026D3", outline="#F5A3FF", width=2, tags=tag
            )
            self._draw_pixel_circle_bbox(
                canvas, x - 9, y - 9, x + 9, y + 9,
                fill="#FFFFFF", outline="#FFB7F5", width=2, tags=tag
            )
        else:
            canvas.create_oval(
                x - 28, y - 28, x + 28, y + 28,
                fill="#C026D3", outline="#FF4FA3", width=3, tags=tag
            )
            canvas.create_oval(
                x - 9, y - 9, x + 9, y + 9,
                fill="#FFFFFF", outline="", tags=tag
            )
        for angle, color in ((0.0, "#FF4FA3"), (math.pi / 2, "#F5A3FF"),
                             (math.pi, "#C026D3"), (math.pi * 1.5, "#FF4FA3")):
            tip_x = x + math.cos(angle) * 36
            tip_y = y + math.sin(angle) * 36
            side_x = x + math.cos(angle + math.pi / 2) * 5
            side_y = y + math.sin(angle + math.pi / 2) * 5
            canvas.create_polygon(
                tip_x, tip_y, side_x, side_y, x, y, -side_x + 2 * x, -side_y + 2 * y,
                fill=color, outline="", tags=tag
            )
        for _ in range(2):
            particle = {
                "id": canvas.create_rectangle(
                    previous_x - 1, previous_y - 1, previous_x + 1, previous_y + 1,
                    fill=random.choice(("#FF4FA3", "#C026D3", "#7E22CE")), outline="",
                    tags="duo_orb_trail"
                ),
                "life": 17,
            }
            context["orb_particles"].append(particle)

    def _duo_keep_beam_alive(self, context, data, colors, widths, source):
        context["projectile_serial"] += 1
        context["projectiles"].append({
            "type": "beam",
            "source": source,
            "end": data["beam_end"],
            "distance": data["beam_distance"],
            "travel": data["beam_travel"],
            "colors": colors,
            "widths": widths,
            "burst_scale": data.get("burst_scale", 1.0),
            "tag": f"duo_beam_active_{context['projectile_serial']}",
        })

    def _duo_keep_orbs_alive(self, context, data, source):
        context["projectile_serial"] += 1
        context["projectiles"].append({
            "type": "orbs",
            "source": source,
            "orbs": [orb.copy() for orb in data.get("orbs", [])],
            "tag": f"duo_orb_active_{context['projectile_serial']}",
        })

    def _duo_tick_projectiles(self, context):
        canvas = context["canvas"]
        active = []
        for projectile in context["projectiles"]:
            if projectile["type"] == "beam":
                projectile["travel"] += self.BEAM_SPEED
                start = self._duo_point(projectile["source"])
                projectile["distance"] = math.hypot(
                    projectile["end"][0] - start[0],
                    projectile["end"][1] - start[1],
                ) or 1.0
                progress = min(1.0, projectile["travel"] / projectile["distance"])
                edge = projectile["end"]
                end = (
                    start[0] + (edge[0] - start[0]) * progress,
                    start[1] + (edge[1] - start[1]) * progress,
                )
                self._duo_spawn_line(
                    context, start, end, projectile["colors"], projectile["widths"], projectile["tag"]
                )
                self._duo_hit_others(projectile["source"], start, end, projectile["widths"][0] / 2, context)
                if progress >= 1.0:
                    self._duo_beam_edge_burst(
                        context, edge[0], edge[1], projectile["colors"], projectile["burst_scale"]
                    )
                    canvas.delete(projectile["tag"])
                else:
                    active.append(projectile)
            else:
                canvas.delete(projectile["tag"])
                pending = False
                for orb in projectile["orbs"]:
                    if orb["done"]:
                        continue
                    source_x, source_y = self._duo_point(projectile["source"])
                    offset_x, offset_y = orb["offset"]
                    origin_x, origin_y = source_x + offset_x, source_y + offset_y
                    previous_x = orb.get("draw_x", origin_x)
                    previous_y = orb.get("draw_y", origin_y)
                    distance = math.hypot(orb["tx"] - origin_x, orb["ty"] - origin_y) or 1.0
                    orb["progress"] += orb["speed"] / distance
                    x = origin_x + (orb["tx"] - origin_x) * orb["progress"]
                    y = origin_y + (orb["ty"] - origin_y) * orb["progress"]
                    if orb["progress"] >= 1.0:
                        x, y = orb["tx"], orb["ty"]
                        orb["done"] = True
                        self._duo_orb_explosion(context, x, y)
                    if not orb["done"]:
                        pending = True
                        self._duo_spawn_orb(context, x, y, previous_x, previous_y, projectile["tag"])
                        self._duo_hit_others(projectile["source"], (x, y), (x + 1, y), 24, context)
                    orb["draw_x"], orb["draw_y"] = x, y
                if pending:
                    active.append(projectile)
                else:
                    canvas.delete(projectile["tag"])
        context["projectiles"] = active
        self._duo_avoid_active_beams(context)
        self._duo_avoid_active_orbs(context)

    def _duo_avoid_active_beams(self, context):
        deoxys = context["deoxys"]
        deoxys_x, deoxys_y = self._duo_point(deoxys)
        safety_radius = max(90.0, deoxys.size_w * 0.8)
        for projectile in context["projectiles"]:
            if projectile["type"] != "beam" or projectile["source"] is not context["ray"]:
                continue
            start = self._duo_point(projectile["source"])
            end = projectile["end"]
            dx, dy = end[0] - start[0], end[1] - start[1]
            length_sq = dx * dx + dy * dy or 1.0
            projection = max(
                0.0,
                min(1.0, ((deoxys_x - start[0]) * dx + (deoxys_y - start[1]) * dy) / length_sq),
            )
            nearest_x = start[0] + dx * projection
            nearest_y = start[1] + dy * projection
            distance_x = deoxys_x - nearest_x
            distance_y = deoxys_y - nearest_y
            distance = math.hypot(distance_x, distance_y)
            if distance >= safety_radius:
                continue
            if distance == 0:
                length = math.hypot(dx, dy) or 1.0
                distance_x, distance_y = -dy / length, dx / length
            else:
                distance_x /= distance
                distance_y /= distance
            self._duo_move(
                deoxys,
                deoxys.x + distance_x * (safety_radius + 80.0),
                deoxys.y + distance_y * (safety_radius + 80.0),
                speed=36.0,
            )
            deoxys_x, deoxys_y = self._duo_point(deoxys)

    def _duo_avoid_active_orbs(self, context):
        ray = context["ray"]
        deoxys = context["deoxys"]
        ray_x, ray_y = self._duo_point(ray)
        safety_radius = max(80.0, ray.size_w * 0.7)
        for projectile in context["projectiles"]:
            if projectile["type"] != "orbs":
                continue
            source_x, source_y = self._duo_point(deoxys)
            for orb in projectile["orbs"]:
                if orb["done"]:
                    continue
                offset_x, offset_y = orb["offset"]
                start = (source_x + offset_x, source_y + offset_y)
                end = (orb["tx"], orb["ty"])
                dx, dy = end[0] - start[0], end[1] - start[1]
                length_sq = dx * dx + dy * dy or 1.0
                projection = max(
                    0.0,
                    min(1.0, ((ray_x - start[0]) * dx + (ray_y - start[1]) * dy) / length_sq),
                )
                nearest_x = start[0] + dx * projection
                nearest_y = start[1] + dy * projection
                distance_x = ray_x - nearest_x
                distance_y = ray_y - nearest_y
                distance = math.hypot(distance_x, distance_y)
                if distance >= safety_radius:
                    continue
                if distance == 0:
                    length = math.hypot(dx, dy) or 1.0
                    distance_x, distance_y = -dy / length, dx / length
                else:
                    distance_x /= distance
                    distance_y /= distance
                self._duo_move(
                    ray,
                    ray.x + distance_x * (safety_radius + 70.0),
                    ray.y + distance_y * (safety_radius + 70.0),
                    speed=34.0,
                )
                ray_x, ray_y = self._duo_point(ray)

    def _duo_beam_edge_burst(self, context, x, y, colors, scale=1.0):
        canvas = context["canvas"]
        for _ in range(int(10 * scale)):
            size = random.uniform(2.0, 4.0) * scale
            context["orb_particles"].append({
                "id": canvas.create_rectangle(
                    x - self.v_x - size, y - self.v_y - size,
                    x - self.v_x + size, y - self.v_y + size,
                    fill=random.choice(colors), outline="", tags="duo_beam_burst"
                ),
                "life": random.randint(5, 9) + int(3 * scale),
                "vx": random.uniform(-4, 4) * scale,
                "vy": random.uniform(-4, 4) * scale,
            })

    def _duo_evade_perpendicular(self, pet, origin, target, context, speed=42.0):
        data = context["attack_data"]
        if not data.get("evade_target"):
            dx, dy = target[0] - origin[0], target[1] - origin[1]
            length = math.hypot(dx, dy) or 1.0
            side = random.choice((-1.0, 1.0))
            perpendicular_x, perpendicular_y = -dy / length * side, dx / length * side
            data["evade_target"] = (
                pet.x + perpendicular_x * 360.0,
                pet.y + perpendicular_y * 360.0,
            )
        return self._duo_move(pet, *data["evade_target"], speed=speed)

    def _duo_center_distance(self, first, second):
        first_x, first_y = self._duo_point(first)
        second_x, second_y = self._duo_point(second)
        return math.hypot(second_x - first_x, second_y - first_y)

    def _duo_ranged_allowed(self, context):
        ray, deoxys = context["ray"], context["deoxys"]
        minimum_distance = max(220.0, (ray.size_w + deoxys.size_w) * 0.9)
        return self._duo_center_distance(ray, deoxys) >= minimum_distance

    def _duo_next_attack_after_dodge(self, dodger):
        if self._duo_name(dodger) in self.DEOXYS_FORMS:
            return random.choices(("psychic_orbs", "tackle"), weights=(0.65, 0.35), k=1)[0]
        return random.choices(("ray_beam", "tackle"), weights=(0.65, 0.35), k=1)[0]

    def _duo_orb_explosion(self, context, x, y):
        canvas = context["canvas"]
        for _ in range(16):
            particle = {
                "id": canvas.create_rectangle(
                    x - self.v_x - 2, y - self.v_y - 2, x - self.v_x + 2, y - self.v_y + 2,
                    fill=random.choice(("#FF4FA3", "#C026D3", "#7E22CE")), outline="", tags="duo_orb_burst"
                ),
                "life": random.randint(8, 14),
                "vx": random.uniform(-7, 7),
                "vy": random.uniform(-7, 7),
            }
            context["orb_particles"].append(particle)

    def _duo_tackle_impact(self, context, x, y, colors):
        canvas = context["canvas"]
        cx, cy = x - self.v_x, y - self.v_y
        if hasattr(self, "_draw_pixel_circle_bbox"):
            for ring, radius, color, grow in (
                (False, 10, "#FFFFFF", 2),
                (True, 20, colors[0], 3),
            ):
                bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
                particle = {
                    "id": self._draw_pixel_circle_bbox(
                        canvas, *bbox, fill=color if not ring else "", outline=color if ring else "", width=4, tags="duo_impact"
                    ),
                    "life": 10,
                    "bbox": bbox,
                    "color": color,
                    "grow": grow,
                    "ring": ring,
                }
                context["impact_particles"].append(particle)
        for _ in range(10):
            context["orb_particles"].append({
                "id": canvas.create_rectangle(
                    cx - 3, cy - 3, cx + 3, cy + 3,
                    fill=random.choice(colors), outline="", tags="duo_impact"
                ),
                "life": 10,
                "vx": random.uniform(-7, 7),
                "vy": random.uniform(-7, 7),
            })

    def _duo_hit_others(self, source, start, end, radius, context):
        if not getattr(source, "get_all_pets", None):
            return
        dx, dy = end[0] - start[0], end[1] - start[1]
        length_sq = dx * dx + dy * dy or 1
        for target in source.get_all_pets():
            if target in (context["ray"], context["deoxys"]) or getattr(target, "is_egg", False):
                continue
            if target.current_state in ("exiting", "dragged"):
                continue
            tx, ty = self._duo_point(target)
            t = max(0.0, min(1.0, ((tx - start[0]) * dx + (ty - start[1]) * dy) / length_sq))
            distance = math.hypot(tx - (start[0] + t * dx), ty - (start[1] + t * dy))
            if distance <= radius and id(target) not in context["hit_ids"]:
                context["hit_ids"].add(id(target))
                if hasattr(target, "interrupt_current_state"):
                    target.interrupt_current_state()
                target.current_state = "thrown"
                target.v_x_velocity = 25.0 if tx >= start[0] else -25.0
                target.v_y_velocity = -12.0

    def _duo_explosion(self, context, x, y):
        canvas = context["canvas"]
        for _ in range(12):
            size = random.randint(2, 5)
            canvas.create_rectangle(
                x - self.v_x - size, y - self.v_y - size, x - self.v_x + size, y - self.v_y + size,
                fill=random.choice(self.COLORS["trail_deoxys"]), outline="", tags="duo_burst"
            )

    def _duo_final_explosion(self, context, x, y, colors):
        self._duo_tackle_impact(context, x, y, colors)
        canvas = context["canvas"]
        for _ in range(36):
            size = random.uniform(4.0, 9.0)
            context["orb_particles"].append({
                "id": canvas.create_rectangle(
                    x - self.v_x - size, y - self.v_y - size,
                    x - self.v_x + size, y - self.v_y + size,
                    fill=random.choice(colors), outline="", tags="duo_final_burst"
                ),
                "life": random.randint(14, 24),
                "vx": random.uniform(-12, 12),
                "vy": random.uniform(-12, 12),
            })

    def _duo_begin_attack(self, context, attack):
        if attack in ("ray_beam", "psychic_orbs") and not self._duo_ranged_allowed(context):
            attack = "tackle"
        context["canvas"].delete("duo_beam_current")
        context["canvas"].delete("duo_orb_current")
        context["canvas"].delete("duo_charge")
        context["attack"] = attack
        context["attack_data"] = {
            "timer": 0,
            "is_final": context["attack_index"] >= len(context["attacks"]) - 1,
        }
        if attack == "ray_beam":
            context["last_attacker"] = context["ray"]
        elif attack == "psychic_orbs":
            context["last_attacker"] = context["deoxys"]
        context["hit_ids"] = set()
        ray, deoxys = context["ray"], context["deoxys"]
        if attack == "psychic_orbs":
            self._duo_set_form(deoxys, "attack")
        elif attack == "tackle":
            self._duo_set_form(deoxys, "base")
        elif attack == "ray_beam":
            if (
                context["attack_data"]["is_final"]
                and context.get("last_attacker") is context["ray"]
            ):
                current_form = self._duo_name(deoxys)
                if current_form == "deoxys2":
                    response_form = random.choice(("base", "attack", "speed"))
                    self._duo_set_form(deoxys, response_form)
                context["attack_data"]["ray_response"] = self._duo_name(deoxys)
            else:
                response_form = "speed" if random.random() < 0.5 else "defense"
                self._duo_set_form(deoxys, response_form)
                context["attack_data"]["ray_response"] = self._duo_name(deoxys)
        if attack == "ray_beam":
            shooter = context["ray"]
            target = context["deoxys"]
            start = self._duo_point(shooter)
            target_point = self._duo_point(target)
            context["attack_data"]["beam_start"] = start
            if context["attack_data"]["is_final"] or context["attack_data"]["ray_response"] == "deoxys2":
                if context["attack_data"]["ray_response"] == "deoxys2":
                    dx = target_point[0] - start[0]
                    dy = target_point[1] - start[1]
                    length = math.hypot(dx, dy) or 1.0
                    target_point = (
                        target_point[0] + dx / length * self.BEAM_DEFENSE_OVERSHOOT,
                        target_point[1] + dy / length * self.BEAM_DEFENSE_OVERSHOOT,
                    )
                context["attack_data"]["beam_end"] = target_point
            else:
                context["attack_data"]["beam_end"] = self._duo_screen_endpoint(start, target_point)
            context["attack_data"]["beam_distance"] = math.hypot(
                context["attack_data"]["beam_end"][0] - start[0],
                context["attack_data"]["beam_end"][1] - start[1],
            ) or 1.0
            context["attack_data"]["beam_travel"] = 0.0
            context["attack_data"]["beam_source"] = shooter
            context["attack_data"]["burst_scale"] = (
                2.0 if context["attack_data"]["ray_response"] == "deoxys2" else 1.0
            )
        context["phase"] = "attack"
        self._duo_face_each_other(context)

    def _duo_finish(self, context):
        ray, deoxys = context["ray"], context["deoxys"]
        winner = context.get("last_attacker")
        if winner not in (ray, deoxys):
            winner = random.choice((ray, deoxys))
        loser = deoxys if winner is ray else ray
        context["winner"], context["phase"] = winner, "finish"
        context["ending"] = True
        context["loser"] = loser
        winner_x, winner_y = self._duo_point(winner)
        loser_x, loser_y = self._duo_point(loser)
        context["final_push_direction"] = (
            loser_x - winner_x,
            loser_y - winner_y,
        )
        context["attack_data"] = {"timer": 12, "loser": loser}
        colors = ("#27AE60", "#2ECC71", "#A9DFBF") if loser is ray else ("#0066FF", "#00BFFF", "#FF8C00")
        self._duo_final_explosion(context, *self._duo_point(loser), colors)

    def _duo_tick_attack(self, context):
        ray, deoxys = context["ray"], context["deoxys"]
        data = context["attack_data"]
        data["timer"] += 1
        attack = context["attack"]
        ray_pos, deoxys_pos = self._duo_point(ray), self._duo_point(deoxys)
        self._duo_face_each_other(context)

        if attack == "ray_beam":
            if not data["is_final"] and data.get("ray_response") == "deoxys3":
                if self._duo_evade_perpendicular(deoxys, ray_pos, deoxys_pos, context):
                    data["start_next_immediately"] = deoxys
                    self._duo_keep_beam_alive(context, data, self.COLORS["ray"], (50, 32, 12), ray)
                    return True
            data["beam_travel"] += self.BEAM_SPEED
            start = self._duo_point(data["beam_source"])
            data["beam_distance"] = math.hypot(
                data["beam_end"][0] - start[0], data["beam_end"][1] - start[1]
            ) or 1.0
            progress = min(1.0, data["beam_travel"] / data["beam_distance"])
            edge = data["beam_end"]
            end = (
                start[0] + (edge[0] - start[0]) * progress,
                start[1] + (edge[1] - start[1]) * progress,
            )
            self._duo_spawn_line(context, start, end, self.COLORS["ray"], (50, 32, 12))
            self._duo_hit_others(ray, start, end, 40, context)
            if progress >= 1.0:
                self._duo_beam_edge_burst(context, edge[0], edge[1], self.COLORS["ray"], data["burst_scale"])
                context["canvas"].delete("duo_beam_current")
                return True
        elif attack == "psychic_orbs":
            context["canvas"].delete("duo_orb_current")
            if data["timer"] == 1:
                orb_target = (
                    ray_pos if data["is_final"] else self._duo_screen_endpoint(deoxys_pos, ray_pos)
                )
                direction_x = orb_target[0] - deoxys_pos[0]
                direction_y = orb_target[1] - deoxys_pos[1]
                direction_length = math.hypot(direction_x, direction_y) or 1.0
                perpendicular = (-direction_y / direction_length, direction_x / direction_length)
                spacing = 42.0
                data["orbs"] = [
                    {"tx": orb_target[0] + perpendicular[0] * (index - 1) * spacing,
                     "ty": orb_target[1] + perpendicular[1] * (index - 1) * spacing,
                     "offset": (perpendicular[0] * (index - 1) * spacing,
                                perpendicular[1] * (index - 1) * spacing),
                     "progress": 0.0,
                     "speed": random.uniform(42.0, 62.0) * self.ORB_SPEED_MULTIPLIER,
                     "done": False}
                    for index in range(random.randint(1, 3))
                ]
            for orb in data.get("orbs", []):
                if orb["done"]:
                    continue
                source_x, source_y = self._duo_point(deoxys)
                offset_x, offset_y = orb["offset"]
                origin_x, origin_y = source_x + offset_x, source_y + offset_y
                previous_x = orb.get("draw_x", origin_x)
                previous_y = orb.get("draw_y", origin_y)
                distance = math.hypot(orb["tx"] - origin_x, orb["ty"] - origin_y) or 1.0
                orb["progress"] += orb["speed"] / distance
                x = origin_x + (orb["tx"] - origin_x) * orb["progress"]
                y = origin_y + (orb["ty"] - origin_y) * orb["progress"]
                if orb["progress"] >= 1.0:
                    x, y = orb["tx"], orb["ty"]
                    orb["done"] = True
                    self._duo_orb_explosion(context, x, y)
                if not orb["done"]:
                    self._duo_spawn_orb(context, x, y, previous_x, previous_y)
                orb["draw_x"], orb["draw_y"] = x, y
                if not orb["done"]:
                    self._duo_hit_others(deoxys, (x, y), (x + 1, y), 24, context)
            if not data["is_final"] and self._duo_evade_perpendicular(ray, deoxys_pos, ray_pos, context):
                data["start_next_immediately"] = ray
                self._duo_keep_orbs_alive(context, data, deoxys)
                context["canvas"].delete("duo_orb_current")
                return True
        elif attack == "tackle":
            if not data.get("tackle_hit"):
                ray_x, ray_y = self._duo_point(ray)
                deoxys_x, deoxys_y = self._duo_point(deoxys)
                dx, dy = deoxys_x - ray_x, deoxys_y - ray_y
                distance = math.hypot(dx, dy) or 1.0
                contact_distance = max(
                    (ray.size_w + deoxys.size_w) / 2,
                    (ray.size_h + deoxys.size_h) / 2,
                )
                step = min(
                    self.TACKLE_SPEED,
                    max(0.0, distance - contact_distance) / 2,
                )
                if step:
                    move_x, move_y = dx / distance * step, dy / distance * step
                    ray.x += move_x
                    ray.y += move_y
                    deoxys.x -= move_x
                    deoxys.y -= move_y
                ray_x, ray_y = self._duo_point(ray)
                deoxys_x, deoxys_y = self._duo_point(deoxys)
                touching_x = abs(ray_x - deoxys_x) <= (ray.size_w + deoxys.size_w) / 2
                touching_y = abs(ray_y - deoxys_y) <= (ray.size_h + deoxys.size_h) / 2
                if touching_x and touching_y:
                    data["tackle_hit"] = True
                    data["tackle_hit_timer"] = data["timer"]
                    ray_pos, deoxys_pos = (ray_x, ray_y), (deoxys_x, deoxys_y)
                    direction = 1.0 if ray_x < deoxys_x else -1.0
                    ray.v_x_velocity = -direction * 38.0
                    deoxys.v_x_velocity = direction * 38.0
                    ray.v_y_velocity = deoxys.v_y_velocity = -14.0
                    self._duo_tackle_impact(context, *ray_pos, ("#27AE60", "#2ECC71", "#A9DFBF"))
                    self._duo_tackle_impact(context, *deoxys_pos, ("#0066FF", "#00BFFF", "#FF8C00"))
        self._duo_trail(context)
        if attack == "psychic_orbs":
            return data["timer"] >= 28 and all(orb["done"] for orb in data.get("orbs", []))
        if attack == "tackle":
            return data.get("tackle_hit", False) and data["timer"] >= data["tackle_hit_timer"] + 8
        return data["timer"] >= (90 if attack == "ray_beam" else 28)

    def _fsm_rayquaza_deoxys_duo(self):
        context = getattr(self, "rayquaza_deoxys_duo", None)
        if not self._duo_alive(context):
            self.cancel_rayquaza_deoxys_duo()
            return
        self._duo_face_each_other(context)
        if context["phase"] == "charge":
            context["timer"] -= 1
            context["canvas"].delete("duo_beam_current")
            canvas = context["canvas"]
            x, y = self._duo_point(context["ray"])
            for radius, color in ((18, "#FF8C00"), (12, "#FFD21F"), (6, "#FFFFFF")):
                canvas.create_oval(x - self.v_x - radius, y - self.v_y - radius,
                                   x - self.v_x + radius, y - self.v_y + radius,
                                   fill=color, outline="", tags="duo_charge")
            self._duo_trail(context)
            if context["timer"] <= 0:
                context["attack_index"] = 0
                self._duo_begin_attack(context, context["attacks"][0])
        elif context["phase"] == "attack":
            if self._duo_tick_attack(context):
                context["canvas"].delete("duo_beam_current")
                context["canvas"].delete("duo_orb_current")
                context["canvas"].delete("duo_charge")
                context["attack_index"] += 1
                if context["attack_index"] >= len(context["attacks"]):
                    self._duo_finish(context)
                elif context["attack_data"].get("start_next_immediately"):
                    dodger = context["attack_data"]["start_next_immediately"]
                    next_attack = self._duo_next_attack_after_dodge(dodger)
                    context["attacks"][context["attack_index"]] = next_attack
                    self._duo_begin_attack(context, next_attack)
                else:
                    context["phase"] = "move"
                    context["timer"] = self.MOVE_TICKS
                    self._duo_begin_move(context)
        elif context["phase"] == "move":
            context["timer"] -= 1
            self._duo_tick_move(context)
            self._duo_trail(context)
            if context["timer"] <= 0:
                self._duo_begin_attack(context, context["attacks"][context["attack_index"]])
        elif context["phase"] == "finish":
            context["timer"] -= 1
            self._duo_trail(context)
            if context["timer"] <= 0:
                self.cancel_rayquaza_deoxys_duo()
        if context.get("vfx") and context["vfx"].winfo_exists():
            self._duo_tick_projectiles(context)
        for pet in (context["ray"], context["deoxys"]):
            if pet.current_state in self.DUO_STATES:
                pet.update_position()
        if context.get("vfx") and context["vfx"].winfo_exists():
            self.schedule_loop(30, self.physics_loop)

    def _fsm_rayquaza_deoxys_duo_partner(self):
        context = getattr(self, "rayquaza_deoxys_duo", None)
        if context and self._duo_alive(context):
            self.update_position()
            self.schedule_loop(30, self.physics_loop)
