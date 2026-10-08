"""
model_manager.py - Model Management and Artifact Handling
"""
import logging
import pickle
import json
import os
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path
from backend.core import storage

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self, artifacts_dir: Optional[str] = None):
        if artifacts_dir is None:
            self.artifacts_dir = os.path.join(os.getcwd(), "models")
        else:
            self.artifacts_dir = artifacts_dir

        Path(self.artifacts_dir).mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, Dict[str, Any]] = storage.load_models()
        logger.info(f"ModelManager initialized at: {self.artifacts_dir} ({len(self.models)} models)")
    
    def save_model(
        self,
        model: Any,
        name: str,
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None
    ) -> Dict[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"{name}_{timestamp}"
        artifacts = {}
        
        try:
            # Save Model
            model_path = os.path.join(self.artifacts_dir, f"{model_name}_model.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            artifacts['model'] = model_path
            
            # Save Metadata
            metadata_dict = {
                'name': name,
                'timestamp': timestamp,
                'metrics': metrics or {},
                'metadata': metadata or {},
                'model_path': model_path
            }
            
            metadata_path = os.path.join(self.artifacts_dir, f"{model_name}_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
            artifacts['metadata'] = metadata_path
            
            # Save Code
            if code:
                code_path = os.path.join(self.artifacts_dir, f"{model_name}_code.py")
                with open(code_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                artifacts['code'] = code_path
            
            # Register in memory + persist
            self.models[model_name] = {
                'name': name,
                'timestamp': timestamp,
                'metrics': metrics or {},
                'artifacts': artifacts
            }
            storage.save_models(self.models)

            logger.info(f"Model saved: {model_name}")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def list_models(self) -> List[Dict[str, Any]]:
        models_list = []
        for model_name, model_info in self.models.items():
            models_list.append({
                'name': model_info['name'],
                'model_name': model_name,
                'timestamp': model_info['timestamp'],
                'metrics': model_info['metrics'],
                'artifacts': model_info['artifacts']
            })
        return sorted(models_list, key=lambda x: x['timestamp'], reverse=True)
    
    def get_best_model(self, metric: str = 'accuracy', higher_is_better: bool = True) -> Optional[Dict[str, Any]]:
        if not self.models: return None
        models = self.list_models()
        if higher_is_better:
            return max(models, key=lambda x: x['metrics'].get(metric, 0))
        else:
            return min(models, key=lambda x: x['metrics'].get(metric, float('inf')))
    
    def rename_model(self, old_model_name: str, new_name: str) -> bool:
        """Rename a saved model"""
        if old_model_name not in self.models:
            logger.error(f"Model not found: {old_model_name}")
            return False
        
        try:
            model_info = self.models[old_model_name]
            model_info['name'] = new_name
            
            # Update metadata file if it exists
            if 'metadata' in model_info['artifacts']:
                metadata_path = model_info['artifacts']['metadata']
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata_dict = json.load(f)
                    metadata_dict['name'] = new_name
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
            
            storage.save_models(self.models)
            logger.info(f"Model renamed from {old_model_name} to {new_name}")
            return True
        except Exception as e:
            logger.error(f"Error renaming model: {str(e)}")
            return False

class ExperimentTracker:
    def __init__(self):
        self.experiments: List[Dict[str, Any]] = storage.load_experiments()

    def log_experiment(self, iteration, code, execution_time, success, metrics=None, error=None, model_path=None):
        self.experiments.append({
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'code': code,
            'execution_time': execution_time,
            'success': success,
            'metrics': metrics or {},
            'error': error,
            'model_path': model_path
        })
        storage.save_experiments(self.experiments)
    
    def get_experiment_history(self): return self.experiments
    def get_successful_experiments(self): return [e for e in self.experiments if e['success']]
    
    def get_performance_trend(self, metric='accuracy'):
        successful = self.get_successful_experiments()
        return [exp['metrics'].get(metric, 0) for exp in successful]
    
    def export_report(self):
        successful = self.get_successful_experiments()
        total = len(self.experiments)
        rate = (len(successful) / total * 100) if total > 0 else 0
        return f"Total: {total}, Success: {len(successful)}, Rate: {rate:.1f}%"

def create_model_manager(artifacts_dir=None): return ModelManager(artifacts_dir)
def create_experiment_tracker(): return ExperimentTracker()