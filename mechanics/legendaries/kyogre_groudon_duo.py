import math
import random
import tkinter as tk

from core.overlays import FloodOverlay


class KyogreGroudonDuoMechanics:
    """Modular Kyogre/Groudon primal-weather duel."""

    KYOGRE_GROUDON_DUO_STATES = ("kyogre_groudon_duo", "kyogre_groudon_duo_partner")
    WATER_RISE_TICKS = 120
    TERRAIN_RISE_TICKS = 100
    BATTLE_TICKS = 1000
    RETURN_DELAY_TICKS = 500
    DRAIN_TICKS = 334
    KYOGRE_SWIM_SPEED = 6.0
    DODGE_HEIGHT = 230.0

    def _kg_name(self, pet):
        return pet.pet_name.lower().replace("_", "").replace("-", "").replace(" ", "")

    def _kg_partner(self, kyogre):
        if not getattr(kyogre, "get_all_pets", None):
            return None
        for pet in kyogre.get_all_pets():
            if pet is not kyogre and self._kg_name(pet) == "groudon":
                if pet.current_state in ("idle", "walking"):
                    return pet
        return None

    def _kg_point(self, pet):
        return pet.x + pet.size_w / 2, pet.y + pet.size_h / 2

    def _kg_create_vfx(self, context):
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
        canvas = tk.Canvas(win, width=self.v_width, height=self.v_height, bg=bg, highlightthickness=0)
        canvas.pack()
        context["vfx"] = win
        context["canvas"] = canvas

    def start_kyogre_groudon_duo(self):
        initiator = self
        if self._kg_name(self) == "groudon":
            for pet in self.get_all_pets():
                if self._kg_name(pet) == "kyogre" and pet.current_state in ("idle", "walking"):
                    initiator = pet
                    break
        if self._kg_name(initiator) != "kyogre":
            return False
        groudon = initiator._kg_partner(initiator)
        if not groudon:
            return False

        context = {
            "kyogre": initiator,
            "groudon": groudon,
            "phase": "position",
            "timer": 0,
            "water_progress": 0.0,
            "mountain_height": 0.0,
            "mountain_target": 250.0,
            "projectiles": [],
            "particles": [],
            "last_attacker": None,
            "finished": False,
            "ending_ticks": 0,
            "rise_start_kyogre": (initiator.x, initiator.y),
            "rise_start_groudon": (groudon.x, groudon.y),
            "projectile_serial": 0,
            "swim": None,
        }
        initiator.kyogre_groudon_duo = context
        groudon.kyogre_groudon_duo = context
        initiator.current_state = "kyogre_groudon_duo"
        groudon.current_state = "kyogre_groudon_duo_partner"

        cooldown = initiator.get_legendary_cooldown(72000)
        initiator.kyogre_groudon_cooldown = cooldown
        groudon.kyogre_groudon_cooldown = cooldown
        initiator.kyogre_cooldown = cooldown
        groudon.groudon_cooldown = cooldown

        initiator._kg_create_vfx(context)
        overlay = FloodOverlay(
            initiator.window.master,
            initiator.v_x,
            initiator.v_y,
            initiator.v_width,
            initiator.v_height,
        )
        overlay.flood_h = int(initiator.v_height * 0.32)
        context["mountain_target"] = max(180.0, overlay.flood_h + 140.0)
        context["overlay"] = overlay
        context["vfx"].lower(initiator.window)
        initiator.window.lift()
        groudon.window.lift()
        overlay.window.lift()
        initiator.schedule_loop(30, initiator.physics_loop)
        return True

    def cancel_kyogre_groudon_duo(self):
        context = getattr(self, "kyogre_groudon_duo", None)
        if not context:
            context = getattr(self, "kyogre_groudon_context", None)
        if not context:
            return
        kyogre, groudon = context["kyogre"], context["groudon"]
        if context.get("finished"):
            self._kg_cleanup_context(context, keep_loser=True)
            return
        self._kg_cleanup_context(context)
        for pet in (kyogre, groudon):
            if pet.window.winfo_exists():
                pet.kyogre_groudon_duo = None
                pet.kyogre_groudon_context = None
                if pet.current_state in self.KYOGRE_GROUDON_DUO_STATES:
                    pet.current_state = "falling"
                    pet.surface_angle = 0
                    pet.v_x_velocity = 0.0
                    pet.v_y_velocity = 0.0
                    pet.schedule_loop(30, pet.physics_loop)

    def _kg_cleanup_context(self, context, keep_loser=False):
        canvas = context.get("canvas")
        if canvas and canvas.winfo_exists():
            canvas.delete("kg_all")
        vfx = context.get("vfx")
        if vfx and vfx.winfo_exists():
            vfx.destroy()
        overlay = context.get("overlay")
        if overlay and getattr(overlay, "active", False):
            overlay.destroy()
        context["projectiles"] = []
        context["particles"] = []
        if not keep_loser:
            context["finished"] = True

    def _kg_screen_targets(self, context):
        kyogre = context["kyogre"]
        left = kyogre.v_x
        right = kyogre.v_x + kyogre.v_width
        midpoint = (left + right) / 2
        kyogre_center = self._kg_point(kyogre)[0]
        kyogre_half = 0 if kyogre_center < midpoint else 1
        kyogre_x = left + (right - left) * (0.25 if kyogre_half == 0 else 0.75)
        groudon_x = left + (right - left) * (0.75 if kyogre_half == 0 else 0.25)
        return kyogre_x, groudon_x

    def _kg_draw_mountain(self, context):
        canvas = context["canvas"]
        canvas.delete("kg_mountain")
        if context["mountain_height"] <= 0:
            return
        groudon = context["groudon"]
        gx = self._kg_point(groudon)[0] - self.v_x
        base_y = self.v_height
        top_y = base_y - context["mountain_height"]
        step = 16
        left = gx - 520
        right = gx + 520
        peak_x = gx - 35
        for x in range(int(left), int(right), step):
            if x <= peak_x:
                ratio = (x - left) / max(1.0, peak_x - left)
                profile = math.sin(max(0.0, min(1.0, ratio)) * math.pi / 2)
            else:
                ratio = (x - peak_x) / max(1.0, right - peak_x)
                profile = math.cos(max(0.0, min(1.0, ratio)) * math.pi / 2)
            column_height = context["mountain_height"] * profile
            for row in range(max(1, int(column_height // step))):
                y = base_y - (row + 1) * step
                if y < top_y:
                    break
                distance = abs(x - peak_x) / max(1.0, right - left)
                if row == int(column_height // step) - 1:
                    color = "#D2691E" if distance < 0.35 else "#A0522D"
                elif (row + x // step) % 5 == 0:
                    color = "#8B4513"
                else:
                    color = "#663C24"
                canvas.create_rectangle(
                    x,
                    y,
                    x + step,
                    y + step,
                    fill=color,
                    outline="",
                    tags=("kg_mountain", "kg_all"),
                )
        canvas.tag_lower("kg_mountain")

    def _kg_groudon_ground_y(self, context):
        return (
            self.v_y
            + self.v_height
            - context["mountain_height"]
            - context["groudon"].size_h
            + 5
        )

    def _kg_face_groudon(self, context):
        kyogre, groudon = context["kyogre"], context["groudon"]
        kyogre_x = self._kg_point(kyogre)[0]
        groudon_x = self._kg_point(groudon)[0]
        groudon.is_facing_right = kyogre_x > groudon_x

    def _kg_particle_burst(self, context, x, y, colors, count=24):
        canvas = context["canvas"]
        for _ in range(count):
            size = random.uniform(2, 6)
            spawn_x = x - self.v_x + random.uniform(-size, size)
            spawn_y = y - self.v_y + random.uniform(0, size)
            item = canvas.create_rectangle(
                spawn_x - size,
                spawn_y - size,
                spawn_x + size,
                spawn_y + size,
                fill=random.choice(colors),
                outline="",
                tags=("kg_particle", "kg_all"),
            )
            context["particles"].append({
                "id": item,
                "life": random.randint(14, 28),
                "x": spawn_x,
                "y": spawn_y,
                "vx": random.uniform(-7, 7),
                "vy": random.uniform(-2, 3),
                "size": 2,
                "gravity": 0.35,
            })

    def _kg_tick_particles(self, context):
        canvas = context["canvas"]
        alive = []
        for particle in context["particles"]:
            if particle["life"] <= 0:
                canvas.delete(particle["id"])
                continue
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += particle.get("gravity", 0.35)
            size = particle.get("size", 2)
            canvas.coords(
                particle["id"],
                particle["x"] - size,
                particle["y"] - size,
                particle["x"] + size,
                particle["y"] + size,
            )
            particle["life"] -= 1
            alive.append(particle)
        context["particles"] = alive

    def _kg_screen_endpoint(self, start, target):
        dx, dy = target[0] - start[0], target[1] - start[1]
        length = math.hypot(dx, dy) or 1.0
        dx, dy = dx / length, dy / length
        distances = []
        if dx > 0:
            distances.append((self.v_x + self.v_width + 40 - start[0]) / dx)
        elif dx < 0:
            distances.append((self.v_x - 40 - start[0]) / dx)
        if dy > 0:
            distances.append((self.v_y + self.v_height + 40 - start[1]) / dy)
        elif dy < 0:
            distances.append((self.v_y - 40 - start[1]) / dy)
        travel = min(value for value in distances if value > 0)
        return start[0] + dx * travel, start[1] + dy * travel

    def _kg_start_jet(self, context):
        kyogre, groudon = context["kyogre"], context["groudon"]
        start = self._kg_point(kyogre)
        dodge_target = self._kg_point(groudon)
        hit = random.random() >= 0.70
        direction_target = (
            dodge_target[0] + random.uniform(-25, 25),
            dodge_target[1] + random.uniform(-25, 25)
            if hit
            else dodge_target[1] - random.uniform(80, 160),
        )
        target = self._kg_screen_endpoint(start, direction_target)
        context["last_attacker"] = kyogre
        context["projectiles"].append({
            "type": "jet",
            "start": start,
            "target": target,
            "dodge_target": dodge_target,
            "progress": 0.0,
            "speed": 0.075,
            "hit": hit,
            "serial": context["projectile_serial"],
        })
        context["projectile_serial"] += 1
        if hit:
            self._kg_dodge_groudon(context)

    def _kg_start_spikes(self, context):
        kyogre, groudon = context["kyogre"], context["groudon"]
        kyogre_x, kyogre_y = self._kg_point(kyogre)
        context["last_attacker"] = groudon
        x = kyogre_x - random.uniform(70, 180)
        if random.random() < 0.35:
            safe_ranges = (
                (self.v_x + 40, kyogre_x - 120),
                (kyogre_x + 120, self.v_x + self.v_width - 40),
            )
            safe_ranges = [bounds for bounds in safe_ranges if bounds[1] > bounds[0]]
            if safe_ranges:
                x_min, x_max = random.choice(safe_ranges)
                x = random.uniform(x_min, x_max)
        target = (
            x,
            random.uniform(
                min(self.v_y + self.v_height * 0.55, kyogre_y),
                max(self.v_y + self.v_height * 0.55, kyogre_y),
            ),
        )
        context["projectiles"].append({
            "type": "spikes",
            "start": (x, self.v_y + self.v_height),
            "target": (x, target[1]),
            "progress": 0.0,
            "speed": 0.16,
            "hit": False,
            "vibrate_ticks": 0,
            "serial": context["projectile_serial"],
        })
        context["projectile_serial"] += 1

    def _kg_tick_projectiles(self, context):
        canvas = context["canvas"]
        alive = []
        for projectile in context["projectiles"]:
            if projectile["type"] == "spikes" and projectile["progress"] >= 1.0:
                if projectile["vibrate_ticks"] <= 0:
                    canvas.delete(f"kg_projectile_{projectile['serial']}")
                    self._kg_particle_burst(
                        context,
                        projectile["target"][0],
                        projectile["target"][1],
                        ("#8B4513", "#FF8C00", "#D2691E"),
                        18,
                    )
                    continue
                projectile["vibrate_ticks"] -= 1
            else:
                projectile["progress"] += projectile["speed"]
            progress = min(1.0, projectile["progress"])
            if (
                projectile["type"] == "spikes"
                and progress >= 1.0
                and projectile["vibrate_ticks"] == 0
            ):
                projectile["vibrate_ticks"] = 25
            sx, sy = projectile["start"]
            tx, ty = projectile["target"]
            ex = sx + (tx - sx) * progress
            ey = sy + (ty - sy) * progress
            tag = f"kg_projectile_{projectile['serial']}"
            canvas.delete(tag)
            if projectile["type"] == "jet":
                water_colors = ("#5DADE2", "#00BFFF", "#D6F5FF", "#3498DB")
                for _ in range(8):
                    trail_x = ex - self.v_x - random.uniform(10, 28)
                    trail_y = ey - self.v_y + random.uniform(-6, 6)
                    size = random.choice((3, 4, 5))
                    canvas.create_rectangle(
                        trail_x - size,
                        trail_y - size,
                        trail_x + size,
                        trail_y + size,
                        fill=random.choice(water_colors),
                        outline="",
                        tags=(tag, "kg_all"),
                    )
            else:
                rock_colors = ("#8B4513", "#A0522D", "#D2691E", "#FF8C00")
                jitter_x = (
                    math.sin(projectile["vibrate_ticks"] * 1.8) * 5
                    if projectile["progress"] >= 1.0
                    else 0
                )
                jitter_y = (
                    math.cos(projectile["vibrate_ticks"] * 1.4) * 2
                    if projectile["progress"] >= 1.0
                    else 0
                )
                blocks = (
                    (-4, -40, 4, -32, "#FFB347"),
                    (-8, -32, 8, -24, "#D2691E"),
                    (-12, -24, 12, -16, "#A0522D"),
                    (-18, -16, 18, -8, "#8B4513"),
                    (-24, -8, 24, 0, "#663C24"),
                )
                for left_offset, top_offset, right_offset, bottom_offset, color in blocks:
                    canvas.create_rectangle(
                        ex - self.v_x + left_offset + jitter_x,
                        ey - self.v_y + top_offset + jitter_y,
                        ex - self.v_x + right_offset + jitter_x,
                        ey - self.v_y + bottom_offset + jitter_y,
                        fill=color,
                        outline="",
                        tags=(tag, "kg_all"),
                    )
            if progress >= 1.0:
                if projectile["type"] == "spikes":
                    alive.append(projectile)
                    continue
                canvas.delete(tag)
                if projectile["hit"]:
                    if projectile["type"] == "jet":
                        self._kg_dodge_groudon(context)
                    else:
                        self._kg_dodge_kyogre(context)
                self._kg_particle_burst(
                    context,
                    tx,
                    ty,
                    ("#5DADE2", "#00BFFF", "#D6F5FF")
                    if projectile["type"] == "jet"
                    else ("#8B4513", "#FF8C00", "#D2691E"),
                    18,
                )
            else:
                alive.append(projectile)
        context["projectiles"] = alive

    def _kg_dodge_groudon(self, context):
        groudon = context["groudon"]
        if groudon.current_state == "kyogre_groudon_duo_partner" and not context.get("groudon_dodge", 0):
            context["groudon_dodge"] = 16
            context["groudon_dodge_y"] = groudon.y - self.DODGE_HEIGHT

    def _kg_dodge_kyogre(self, context):
        kyogre = context["kyogre"]
        if kyogre.current_state == "kyogre_groudon_duo" and not context.get("kyogre_dodge", 0):
            context["kyogre_dodge"] = 18
            context["kyogre_dodge_y"] = kyogre.y - 90

    def _kg_tick_dodges(self, context):
        kyogre, groudon = context["kyogre"], context["groudon"]
        if context.get("groudon_dodge", 0):
            context["groudon_dodge"] -= 1
            progress = context["groudon_dodge"] / 16
            groudon.y = self._kg_groudon_ground_y(context) - math.sin(progress * math.pi) * self.DODGE_HEIGHT
        if context.get("kyogre_dodge", 0):
            context["kyogre_dodge"] -= 1
            progress = context["kyogre_dodge"] / 18
            kyogre.y = context["water_y"] + 25 - math.sin(progress * math.pi) * 90

    def _kg_tick_swim(self, context):
        kyogre = context["kyogre"]
        if context.get("kyogre_dodge", 0):
            return
        water_y = context["water_y"]
        min_x = self.v_x + 25
        max_x = self.v_x + self.v_width - kyogre.size_w - 25
        min_y = water_y + 20
        max_y = self.v_y + self.v_height - kyogre.size_h - 25
        swim = context.get("swim")
        if not swim or swim["progress"] >= 1.0:
            start_x, start_y = kyogre.x, kyogre.y
            target_x = random.uniform(min_x, max_x)
            target_y = random.uniform(min_y, max_y)
            direction = 1 if target_x >= start_x else -1
            swim = {
                "start": (start_x, start_y),
                "control": (
                    (start_x + target_x) / 2,
                    random.uniform(min_y, max_y),
                ),
                "target": (target_x, target_y),
                "progress": 0.0,
                "direction": direction,
            }
            context["swim"] = swim
        p = swim["progress"]
        next_p = min(1.0, p + 0.01)
        current_x, current_y = self._kg_swim_point(swim, p)
        next_x, next_y = self._kg_swim_point(swim, next_p)
        distance = math.hypot(next_x - current_x, next_y - current_y) or 1.0
        swim["progress"] = min(1.0, p + self.KYOGRE_SWIM_SPEED / distance * 0.01)
        p = swim["progress"]
        current_x, current_y = self._kg_swim_point(swim, p)
        next_x, next_y = self._kg_swim_point(swim, min(1.0, p + 0.01))
        kyogre.x, kyogre.y = current_x, current_y
        moving_right = next_x >= current_x
        kyogre.is_facing_right = moving_right
        for _ in range(1):
            bubble_x = self._kg_point(kyogre)[0] - (kyogre.size_w * 0.35 if moving_right else -kyogre.size_w * 0.35)
            bubble_y = kyogre.y + kyogre.size_h * random.uniform(0.65, 0.9)
            bubble = context["canvas"].create_oval(
                bubble_x - self.v_x - 3,
                bubble_y - self.v_y - 3,
                bubble_x - self.v_x + 3,
                bubble_y - self.v_y + 3,
                outline=random.choice(("#BDEBFF", "#E8FAFF", "#7DD3FC")),
                width=1,
                tags=("kg_particle", "kg_all"),
            )
            context["particles"].append({
                "id": bubble,
                "life": 33,
                "x": bubble_x - self.v_x,
                "y": bubble_y - self.v_y,
                "vx": random.uniform(-0.5, 0.5),
                "vy": 0.0,
                "size": random.choice((2, 3)),
                "gravity": 0.0,
            })

    def _kg_swim_point(self, swim, progress):
        inverse = 1.0 - progress
        start_x, start_y = swim["start"]
        control_x, control_y = swim["control"]
        target_x, target_y = swim["target"]
        return (
            inverse * inverse * start_x + 2 * inverse * progress * control_x + progress * progress * target_x,
            inverse * inverse * start_y + 2 * inverse * progress * control_y + progress * progress * target_y,
        )

    def _kg_finish(self, context):
        kyogre, groudon = context["kyogre"], context["groudon"]
        winner = random.choice((kyogre, groudon))
        loser = groudon if winner is kyogre else kyogre
        context["finished"] = True
        context["winner"] = winner
        context["loser"] = loser
        context["ending_ticks"] = self.RETURN_DELAY_TICKS
        canvas = context["canvas"]
        canvas.delete("kg_particle")
        canvas.delete("kg_projectile")
        context["particles"] = []
        self._kg_particle_burst(
            context,
            *self._kg_point(kyogre),
            ("#3498DB", "#00BFFF", "#D6F5FF"),
            24,
        )
        self._kg_particle_burst(
            context,
            *self._kg_point(groudon),
            ("#8B4513", "#FF4500", "#FF8C00"),
            24,
        )
        self._kg_particle_burst(
            context,
            *self._kg_point(loser),
            ("#3498DB", "#00BFFF", "#D6F5FF")
            if winner is kyogre
            else ("#8B4513", "#FF4500", "#FF8C00"),
            48,
        )
        context["projectiles"] = []
        self._kg_start_final_loss(context, loser, winner)
        overlay = context.get("overlay")
        if overlay and overlay.active:
            overlay.is_draining = True

    def _kg_start_final_loss(self, context, loser, winner):
        lx, ly = self._kg_point(loser)
        wx, wy = self._kg_point(winner)
        if self._kg_name(loser) == "kyogre":
            dx, dy = 0.0, -1.0
        else:
            dx, dy = lx - wx, ly - wy
        length = math.hypot(dx, dy) or 1.0
        dx, dy = dx / length, dy / length
        travel = 1400.0
        exit_x = loser.x + dx * travel
        exit_y = loser.y + dy * travel
        if self._kg_name(loser) == "kyogre":
            exit_y = self.v_y - loser.size_h - 80
        loser._kg_final_return = {
            "phase": "launch",
            "ticks": 18,
            "launch_ticks": 18,
            "start_x": loser.x,
            "start_y": loser.y,
            "exit_x": exit_x,
            "exit_y": exit_y,
            "target_x": loser.x,
            "target_y": (
                loser.default_floor_y
                if self._kg_name(loser) == "groudon"
                else loser.target_floor_y
            ),
            "return_ticks": 120,
            "rotation": 32.0 if dx >= 0 else -32.0,
        }
        loser.current_state = "kyogre_groudon_final_loss"
        loser.surface_angle = 0
        loser.v_x_velocity = loser.v_y_velocity = 0.0
        loser.schedule_loop(30, self._kg_tick_final_loss, loser)

    def _kg_tick_final_loss(self, loser):
        data = getattr(loser, "_kg_final_return", None)
        if not data or not loser.window.winfo_exists():
            return
        if data["phase"] == "launch":
            progress = 1.0 - data["ticks"] / data["launch_ticks"]
            eased = 1.0 - (1.0 - progress) ** 2
            loser.x = data["start_x"] + (data["exit_x"] - data["start_x"]) * eased
            loser.y = data["start_y"] + (data["exit_y"] - data["start_y"]) * eased
            loser.surface_angle = (loser.surface_angle + data["rotation"]) % 360
            data["ticks"] -= 1
            loser.update_position()
            if data["ticks"] > 0:
                loser.schedule_loop(30, self._kg_tick_final_loss, loser)
                return
            data["phase"] = "away"
            data["ticks"] = self.RETURN_DELAY_TICKS
            loser.surface_angle = 0
        if data["phase"] == "away":
            data["ticks"] -= 1
            loser.update_position()
            if data["ticks"] > 0:
                loser.schedule_loop(30, self._kg_tick_final_loss, loser)
                return
            data["phase"] = "returning"
            data["ticks"] = data["return_ticks"]
            loser.current_state = "walking" if self._kg_name(loser) == "groudon" else "kyogre_groudon_final_return"
            loser._kg_final_returning = True
            loser.is_facing_right = data["target_x"] > data["exit_x"]
        progress = 1.0 - data["ticks"] / data["return_ticks"]
        eased = progress * progress * (3 - 2 * progress)
        loser.x = data["exit_x"] + (data["target_x"] - data["exit_x"]) * eased
        loser.y = data["exit_y"] + (data["target_y"] - data["exit_y"]) * eased
        loser.surface_angle = 0
        loser.update_position()
        data["ticks"] -= 1
        if data["ticks"] > 0:
            loser.schedule_loop(30, self._kg_tick_final_loss, loser)
            return
        loser.x, loser.y = data["target_x"], data["target_y"]
        loser.floor_y = data["target_y"]
        loser.current_state = "walking" if self._kg_name(loser) == "groudon" else "idle"
        loser._kg_final_returning = False
        loser.surface_angle = 0
        loser.v_x_velocity = loser.v_y_velocity = 0.0
        loser.update_position()
        loser._kg_final_return = None
        loser.schedule_loop(50, loser.physics_loop)

    def _fsm_kyogre_groudon_duo_partner(self):
        context = getattr(self, "kyogre_groudon_duo", None)
        if context and not context.get("finished"):
            self.update_position()
            self.schedule_loop(30, self.physics_loop)

    def _fsm_kyogre_groudon_duo(self):
        context = getattr(self, "kyogre_groudon_duo", None)
        if not context:
            return
        kyogre, groudon = context["kyogre"], context["groudon"]
        if context.get("finished"):
            context["ending_ticks"] -= 1
            context["mountain_height"] = max(
                0.0,
                context["mountain_height"] * (context["ending_ticks"] / self.RETURN_DELAY_TICKS),
            )
            if groudon is context["winner"] and groudon.current_state in self.KYOGRE_GROUDON_DUO_STATES:
                groudon.y = self._kg_groudon_ground_y(context)
            self._kg_draw_mountain(context)
            self._kg_tick_particles(context)
            if context["ending_ticks"] <= 0:
                context["phase"] = "done"
                for pet in (kyogre, groudon):
                    pet.kyogre_groudon_duo = None
                    pet.kyogre_groudon_context = None
                    if pet is not context["loser"] and pet.current_state in self.KYOGRE_GROUDON_DUO_STATES:
                        pet.y = (
                            pet.default_floor_y
                            if self._kg_name(pet) == "groudon"
                            else pet.target_floor_y
                        )
                        pet.floor_y = pet.y
                        pet.current_state = "idle"
                        pet.surface_angle = 0
                        pet.v_x_velocity = pet.v_y_velocity = 0.0
                        pet.update_position()
                context["canvas"].delete("kg_all")
                self._kg_cleanup_context(context, keep_loser=True)
                return
        else:
            context["timer"] += 1
            if context["phase"] == "position":
                progress = min(1.0, context["timer"] / self.WATER_RISE_TICKS)
                context["water_progress"] = progress
                context["mountain_height"] = 0.0
                kyogre_x, groudon_x = self._kg_screen_targets(context)
                kyogre_start_x, kyogre_start_y = context["rise_start_kyogre"]
                groudon_start_x, groudon_start_y = context["rise_start_groudon"]
                kyogre_target_x = kyogre_x - kyogre.size_w / 2
                groudon_target_x = groudon_x - groudon.size_w / 2
                overlay = context["overlay"]
                context["water_y"] = self.v_y + self.v_height - overlay.current_flood_h
                final_kyogre_y = (
                    self.v_y + self.v_height - overlay.flood_h + 25
                )
                final_groudon_y = groudon.default_floor_y
                kyogre.x = kyogre_start_x + (kyogre_target_x - kyogre_start_x) * progress
                kyogre.y = kyogre_start_y + (final_kyogre_y - kyogre_start_y) * progress
                groudon.x = groudon_start_x + (groudon_target_x - groudon_start_x) * progress
                groudon.y = groudon_start_y + (final_groudon_y - groudon_start_y) * progress
                self._kg_face_groudon(context)
                self._kg_draw_mountain(context)
                if progress >= 1.0:
                    context["phase"] = "terrain_rise"
                    context["timer"] = 0
            elif context["phase"] == "terrain_rise":
                progress = min(1.0, context["timer"] / self.TERRAIN_RISE_TICKS)
                context["mountain_height"] = context["mountain_target"] * progress
                overlay = context.get("overlay")
                context["water_y"] = self.v_y + self.v_height - overlay.flood_h
                kyogre.y = context["water_y"] + 25
                groudon.y = self._kg_groudon_ground_y(context)
                self._kg_face_groudon(context)
                self._kg_draw_mountain(context)
                if progress >= 1.0:
                    context["phase"] = "battle"
                    context["timer"] = 0
            else:
                overlay = context.get("overlay")
                if not context.get("water_y"):
                    context["water_y"] = (
                        self.v_y + self.v_height - overlay.flood_h
                        if overlay and overlay.active
                        else self.v_y + self.v_height
                    )
                if context["timer"] % 33 == 1:
                    self._kg_start_jet(context)
                if context["timer"] % 55 == 1 and not context.get("groudon_dodge", 0):
                    self._kg_start_spikes(context)
                self._kg_tick_dodges(context)
                self._kg_tick_projectiles(context)
                self._kg_tick_swim(context)
                if not context.get("groudon_dodge", 0):
                    groudon.y = self._kg_groudon_ground_y(context)
                self._kg_face_groudon(context)
                if context["timer"] >= self.BATTLE_TICKS:
                    self._kg_finish(context)
                self._kg_draw_mountain(context)
            self._kg_tick_particles(context)
        kyogre.update_position()
        groudon.update_position()
        if context.get("vfx") and context["vfx"].winfo_exists():
            self.schedule_loop(30, self.physics_loop)
