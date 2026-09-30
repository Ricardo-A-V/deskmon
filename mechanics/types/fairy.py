class FairyMechanics:
    def check_fairy_mechanic(self):
        if getattr(self, 'fairy_type', False) and self.current_state in ['idle', 'walking']:
            if getattr(self, 'get_all_pets', None):
                for other in self.get_all_pets():
                    if other != self and other.current_state == 'attacking' and abs(self.x - other.x) < self.size_w and abs(self.y - other.y) < self.size_h:
                        opponent = getattr(other, 'attack_target', None)
                        if opponent:
                            if hasattr(opponent, 'interrupt_current_state'): opponent.interrupt_current_state()
                            opponent.current_state = 'thrown' if getattr(opponent, 'is_flying', False) else 'falling'
                            opponent.v_y_velocity = 0.0
                            opponent.v_x_velocity = 0.0
                            opponent.attack_cooldown = 12000
                            opponent.attack_target = None
                            if hasattr(opponent, 'show_fairy_sparkles_vfx'): opponent.show_fairy_sparkles_vfx()
                            
                        if hasattr(other, 'interrupt_current_state'): other.interrupt_current_state()
                        other.current_state = 'thrown' if getattr(other, 'is_flying', False) else 'falling'
                        other.v_y_velocity = 0.0
                        other.v_x_velocity = 0.0
                        other.attack_cooldown = 12000
                        other.attack_target = None
                        if hasattr(other, 'show_fairy_sparkles_vfx'): other.show_fairy_sparkles_vfx()
                        
                        if hasattr(self, 'show_fairy_sparkles_vfx'): self.show_fairy_sparkles_vfx()
                        
                        self.current_state = 'jumping_arc'
                        self.v_x_velocity = 0.0
                        self.v_y_velocity = -12.0
                        self.arc_target_x = self.x
                        self.arc_target_y = self.y
                        return True
        return False
