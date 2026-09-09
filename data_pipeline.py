"""
data_pipeline.py - Robust Data Preprocessing Pipeline
Supports synthetic data generation, CSV upload, and automated preprocessing
"""

import logging
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from dataclasses import dataclass
import io

logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    """Information about a dataset"""
    shape: Tuple[int, int]
    features: List[str]
    target: Optional[str]
    dtypes: Dict[str, str]
    missing_values: Dict[str, int]
    categorical_features: List[str]
    numeric_features: List[str]
    data_summary: str
    task_type: str = "classification"


class DataPreprocessor:
    """Handles data preprocessing and preparation"""
    
    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler: Optional[StandardScaler] = None
        self.numeric_features: List[str] = []
        self.categorical_features: List[str] = []
        
    def generate_synthetic_data(
        self,
        task: str = "classification",
        n_samples: int = 200,
        n_features: int = 10,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> pd.DataFrame:
        """
        Generate synthetic dataset for experimentation
        Only supports classification and regression tasks.
        """
        np.random.seed(random_state)
        
        if task == "classification":
            from sklearn.datasets import make_classification
            X, y = make_classification(
                n_samples=n_samples,
                n_features=n_features,
                n_informative=n_features - 2,
                n_redundant=1,
                n_clusters_per_class=2,
                random_state=random_state
            )
            feature_names = [f"feature_{i}" for i in range(n_features)]
            df = pd.DataFrame(X, columns=feature_names)
            df['target'] = y
            
        elif task == "regression":
            from sklearn.datasets import make_regression
            X, y = make_regression(
                n_samples=n_samples,
                n_features=n_features,
                random_state=random_state
            )
            feature_names = [f"feature_{i}" for i in range(n_features)]
            df = pd.DataFrame(X, columns=feature_names)
            df['target'] = y
        else:
            raise ValueError(f"Synthetic data only supports classification/regression, not {task}")
        
        logger.info(f"Generated synthetic {task} dataset: {df.shape}")
        return df

    async def generate_ai_data(
        self, 
        api_key: str, 
        model: str, 
        base_url: str,
        user_description: str, 
        n_samples: int,
        task: str = "classification"
    ):
        """Generate realistic data using LLM to write the script"""
        from llm_agent import create_agent
        
        prompt_templates = {
            "classification": f"""Create a Python script to generate synthetic data for: "{user_description}"

Requirements:
1. Generate {n_samples} rows with MEANINGFUL column names (e.g., 'age', 'income', 'category')
2. Include a 'target' column for classification task (0 or 1)
3. Use realistic distributions (np.random.normal, uniform, choice)
4. Save to: 'output.csv'
5. Print columns at end: print(f"Columns: {{list(df.columns)}}")

Return ONLY Python code, no markdown blocks.""",

            "regression": f"""Create a Python script to generate synthetic data for: "{user_description}"

Requirements:
1. Generate {n_samples} rows with MEANINGFUL column names (e.g., 'age', 'income', 'years_experience')
2. Include a 'target' column for regression task (continuous values)
3. Use realistic distributions (np.random.normal, uniform)
4. Save to: 'output.csv'
5. Print columns at end: print(f"Columns: {{list(df.columns)}}")

Return ONLY Python code, no markdown blocks.""",

            "clustering": f"""Create a Python script to generate synthetic data for: "{user_description}"

Requirements:
1. Generate {n_samples} rows with MEANINGFUL column names (e.g., 'age', 'income', 'spending_score')
2. NO target column - this is unsupervised clustering
3. Create natural clusters/groups in the data using different distributions
4. Save to: 'output.csv'
5. Print columns at end: print(f"Columns: {{list(df.columns)}}")

Return ONLY Python code, no markdown blocks.""",

            "recommendation": f"""Create a Python script to generate synthetic data for: "{user_description}"

Requirements:
1. Generate {n_samples} rows for a content-based recommendation system
2. Include columns: 'user_id', 'item_id', 'rating', and item feature columns
3. Item features should describe items (e.g., 'genre_action', 'genre_comedy', 'year', 'duration')
4. Use realistic distributions
5. Save to: 'output.csv'
6. Print columns at end: print(f"Columns: {{list(df.columns)}}")

Return ONLY Python code, no markdown blocks."""
        }
        
        prompt = prompt_templates.get(task, prompt_templates["classification"])
        
        agent = create_agent(api_key, model, base_url)
        code = await agent._call_ai(prompt)
        
        if not code:
            raise Exception("AI returned empty response")
        
        code = code.strip()
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        self.last_generated_code = code
        
        import tempfile, subprocess, sys, os
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "gen.py")
        csv_path = os.path.join(temp_dir, "output.csv")
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=45, cwd=temp_dir
        )
        
        if result.returncode != 0:
            raise Exception(f"Script failed: {result.stderr[:200]}")
        
        if not os.path.exists(csv_path):
            import glob
            csv_files = glob.glob(os.path.join(temp_dir, "*.csv"))
            if csv_files:
                csv_path = csv_files[0]
            else:
                raise Exception("No CSV generated")
        
        df = pd.read_csv(csv_path)
        
        if task in ["classification", "regression"]:
            target_col = 'target' if 'target' in df.columns else df.columns[-1]
        elif task == "clustering":
            target_col = None
        elif task == "recommendation":
            target_col = 'rating' if 'rating' in df.columns else None
        else:
            target_col = None
        
        return df, target_col, code
    
    def load_csv_data(
        self,
        file_content: bytes,
        target_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Load CSV data from uploaded file
        """
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            logger.info(f"Loaded CSV: {df.shape}")
            
            if target_column is None:
                target_column = df.columns[-1]
            elif target_column not in df.columns:
                raise ValueError(f"Column '{target_column}' not found in dataset")
            
            return df, target_column
            
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            raise
    
    def analyze_data(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        task_type: str = "classification"
    ) -> DatasetInfo:
        """
        Analyze dataset and extract information
        """
        numeric_features = df.select_dtypes(
            include=['int64', 'float64']
        ).columns.tolist()
        
        if target_column and target_column in numeric_features:
            numeric_features.remove(target_column)
        
        categorical_features = [
            col for col in df.columns
            if col not in numeric_features and col != target_column
        ]
        
        missing_values = df.isnull().sum().to_dict()
        missing_values = {k: v for k, v in missing_values.items() if v > 0}
        
        target_info = "N/A"
        if target_column and target_column in df.columns:
            if task_type in ["classification", "regression"]:
                target_info = df[target_column].value_counts().head(10).to_string()
            elif task_type == "recommendation":
                target_info = f"Rating range: {df[target_column].min():.1f} - {df[target_column].max():.1f}, Mean: {df[target_column].mean():.2f}"
        
        summary = f"""
Dataset Shape: {df.shape}
Task Type: {task_type}
Numeric Features: {len(numeric_features)}
Categorical Features: {len(categorical_features)}
Missing Values: {len(missing_values)} columns with missing data
Target Info:
{target_info}
"""
        
        info = DatasetInfo(
            shape=df.shape,
            features=[col for col in df.columns if col != target_column],
            target=target_column,
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            missing_values=missing_values,
            categorical_features=categorical_features,
            numeric_features=numeric_features,
            data_summary=summary,
            task_type=task_type
        )
        
        self.numeric_features = numeric_features
        self.categorical_features = categorical_features
        
        logger.info(f"Dataset analysis complete: {len(numeric_features)} numeric, {len(categorical_features)} categorical")
        return info
    
    def preprocess(
        self,
        df: pd.DataFrame,
        target_column: Optional[str],
        fit: bool = True
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Apply complete preprocessing pipeline
        """
        df = df.copy()
        
        if target_column and target_column in df.columns:
            X = df.drop(columns=[target_column])
            y = df[target_column]
        else:
            X = df
            y = None
        
        X = self._handle_missing_values(X, fit)
        X = self._encode_categorical(X, fit)
        X = self._scale_features(X, fit)
        
        logger.info("Data preprocessing complete")
        return X, y
    
    def _handle_missing_values(
        self,
        X: pd.DataFrame,
        fit: bool = True
    ) -> pd.DataFrame:
        """Handle missing values using appropriate strategies"""
        X = X.copy()
        
        for col in X.columns:
            if X[col].isnull().any():
                if X[col].dtype in ['int64', 'float64']:
                    fill_value = X[col].median()
                    X[col] = X[col].fillna(fill_value)
                    logger.info(f"Filled {col} with median: {fill_value:.2f}")
                else:
                    fill_value = X[col].mode()[0] if not X[col].mode().empty else 'unknown'
                    X[col] = X[col].fillna(fill_value)
                    logger.info(f"Filled {col} with mode: {fill_value}")
        
        return X
    
    def _encode_categorical(
        self,
        X: pd.DataFrame,
        fit: bool = True
    ) -> pd.DataFrame:
        """Encode categorical features"""
        X = X.copy()
        
        for col in self.categorical_features:
            if col not in X.columns:
                continue
            
            if fit:
                encoder = LabelEncoder()
                X[col] = encoder.fit_transform(X[col].astype(str))
                self.label_encoders[col] = encoder
                logger.info(f"Encoded categorical feature: {col}")
            else:
                if col in self.label_encoders:
                    encoder = self.label_encoders[col]
                    X[col] = encoder.transform(X[col].astype(str))
        
        return X
    
    def _scale_features(
        self,
        X: pd.DataFrame,
        fit: bool = True
    ) -> pd.DataFrame:
        """Scale numeric features"""
        if not self.numeric_features:
            return X
        
        X = X.copy()
        numeric_cols = [col for col in self.numeric_features if col in X.columns]
        
        if not numeric_cols:
            return X
        
        if fit:
            self.scaler = StandardScaler()
            X[numeric_cols] = self.scaler.fit_transform(X[numeric_cols])
            logger.info(f"Scaled {len(numeric_cols)} numeric features")
        else:
            if self.scaler:
                X[numeric_cols] = self.scaler.transform(X[numeric_cols])
        
        return X
    
    def split_data(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into train and test sets
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y if len(y.unique()) < 20 else None
        )
        
        logger.info(f"Data split: train {X_train.shape}, test {X_test.shape}")
        return X_train, X_test, y_train, y_test


def create_preprocessor() -> DataPreprocessor:
    """Create and return a new DataPreprocessor instance"""
    return DataPreprocessor()


def load_and_preprocess(
    file_content: Optional[bytes] = None,
    task: str = "classification",
    synthetic: bool = False,
    target_column: Optional[str] = None
) -> Tuple[pd.DataFrame, str, DatasetInfo]:
    """
    Convenience function to load and analyze data
    """
    preprocessor = DataPreprocessor()
    
    if synthetic or file_content is None:
        df = preprocessor.generate_synthetic_data(task=task)
        target_column = 'target'
    else:
        df, target_column = preprocessor.load_csv_data(
            file_content,
            target_column
        )
    
    dataset_info = preprocessor.analyze_data(df, target_column, task)
    return df, target_column, dataset_info
