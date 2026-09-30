class FightingMechanics:
    def get_attack_chance(self, default_chance):
        return 5 if getattr(self, 'fighting_type', False) else default_chance
        
    def get_attack_cooldown(self, default_cd):
        return 3600 if getattr(self, 'fighting_type', False) else default_cd
