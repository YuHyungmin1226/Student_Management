import json
import os
from typing import Dict, Any

class ConfigManager:
    """설정 파일 관리 클래스"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        default_config = {
            "database_path": "student.db",
            "backup_auto": True,
            "backup_interval": 7,
            "default_year": 2024,
            "ui_theme": "light",
            "language": "ko",
            "auto_save": True,
            "search_auto": True,
            "stats_auto_refresh": True,
            "shortcuts_enabled": True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 기본값과 병합
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")
                return default_config
        else:
            # 설정 파일이 없으면 기본값으로 생성
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """설정 파일 저장"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.config = config
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """설정값 설정"""
        self.config[key] = value
        return self.save_config()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """여러 설정값 한번에 업데이트"""
        self.config.update(updates)
        return self.save_config() 