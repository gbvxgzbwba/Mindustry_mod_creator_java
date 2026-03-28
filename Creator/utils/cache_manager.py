import json
import os
VERSION = "1.2"
class CacheManager:
    def __init__(self, mod_name):
        self.mod_name = mod_name
        self.cache_dir = os.path.join("mindustry_mod_creator", "cache")
        self.cache_file = os.path.join(self.cache_dir, f"{mod_name}.json")
        self.default_cache = self._get_default_cache()
    
    def _get_default_cache(self):
        return {
            "_comment": "Не удаляйте этот фаил он нужен для работы исследования",
            "wall": [
                "copper-wall",
                "copper-wall-large",
                "titanium-wall",
                "titanium-wall-large",
                "plastanium-wall",
                "plastanium-wall-large",
                "thorium-wall",
                "thorium-wall-large",
                "surge-wall",
                "surge-wall-large",
                "phase-wall",
                "phase-wall-large"
            ],
            "ThermalGenerator": [
                "thermal-generator"
            ],
            "SolarGenerator": [
                "solar-panel",
                "solar-panel-large"
            ],
            "ConsumeGenerator": [
                "combustion-generator",
                "steam-generator",
                "rtg-generator",
                "differential-generator"
            ],
            "StorageBlock": [
                "container",
                "vault"
            ],
            "GenericCrafter": [
                "graphite-press",
                "pyratite-mixer",
                "blast-mixer",
                "silicon-smelter",
                "spore-press",
                "coal-centrifuge",
                "multi-press",
                "silicon-crucible",
                "plastanium-compressor",
                "phase-weaver",
                "kiln",
                "pulverizer",
                "melter",
                "surge-smelter",
                "separator",
                "cryofluid-mixer",
                "disassembler"
            ],
            "beam-node":[
                "beam-node"
            ],
            "conveyor": [
                "conveyor",
                "titanium-conveyor"
            ],
            "conduit": [
                "conduit",
                "pulse-conduit"
            ],
            "MendProjector": [
                "mend-projector",
                "mender"
            ],
            "Pump": ["impulse-pump", "rotary-pump", "mechanical-pump"],
            "SolidPump": ["water-extractor"],
            "PowerNode": ["power-node", "power-node-large"],
            "router": ["Router", "Distributor"],
            "Junction": ["Junction"],
            "Unloader": ["Unloader"],
            "liquid_router": ["liquid-router"],
            "Liquid_Junction": ["Liquid-Junction"],
            "Liquid_Tank": ["liquid-container", "liquid-tank"],
            "Battery": ["Battery-large", "Battery"],
            "OverdriveProjector": ["overdrive-projector"]
        }
    
    def load_or_create_cache(self):
        """Загрузка или создание кэша"""
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if not os.path.exists(self.cache_file):
            self._save_cache(self.default_cache)
            return self.default_cache
        
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Обновляем устаревший кэш
            updated = False
            for key, default_value in self.default_cache.items():
                if key not in cache_data:
                    cache_data[key] = default_value
                    updated = True
                elif not isinstance(cache_data[key], list):
                    cache_data[key] = default_value
                    updated = True
            
            if updated:
                self._save_cache(cache_data)
            
            return cache_data
            
        except json.JSONDecodeError:
            self._save_cache(self.default_cache)
            return self.default_cache
    
    def _save_cache(self, cache_data):
        """Сохранение кэша"""
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=4, ensure_ascii=False)
    
    def add_to_cache(self, category, item_name):
        """Добавление элемента в кэш"""
        cache_data = self.load_or_create_cache()
        
        if category not in cache_data:
            cache_data[category] = []
        
        if item_name not in cache_data[category]:
            cache_data[category].append(item_name)
            self._save_cache(cache_data)
    
    def remove_from_cache(self, item_name):
        """Удаление элемента из кэша"""
        cache_data = self.load_or_create_cache()
        item_removed = False
        
        for category in list(cache_data.keys()):
            if category == "_comment":
                continue
            
            if isinstance(cache_data[category], list) and item_name in cache_data[category]:
                cache_data[category].remove(item_name)
                item_removed = True
                
                if not cache_data[category]:
                    del cache_data[category]
                break
        
        if item_removed:
            self._save_cache(cache_data)
        
        return item_removed