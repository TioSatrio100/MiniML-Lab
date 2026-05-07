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
    target: str
    dtypes: Dict[str, str]
    missing_values: Dict[str, int]
    categorical_features: List[str]
    numeric_features: List[str]
    data_summary: str


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
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Generate synthetic dataset for experimentation
        
        Args:
            task: 'classification' or 'regression'
            n_samples: Number of samples
            n_features: Number of features
            test_size: Test split ratio
            random_state: Random seed
            
        Returns:
            Tuple of (features DataFrame, target Series)
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
            raise ValueError(f"Unknown task: {task}")
        
        logger.info(f"Generated synthetic {task} dataset: {df.shape}")
        return df
    
    def load_csv_data(
        self,
        file_content: bytes,
        target_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Load CSV data from uploaded file
        
        Args:
            file_content: File bytes
            target_column: Name of target column (if None, uses last column)
            
        Returns:
            Tuple of (DataFrame, target_column_name)
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
        target_column: str
    ) -> DatasetInfo:
        """
        Analyze dataset and extract information
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            
        Returns:
            DatasetInfo object with analysis results
        """
        # Identify feature types
        numeric_features = df.select_dtypes(
            include=['int64', 'float64']
        ).columns.tolist()
        
        # Remove target from features
        if target_column in numeric_features:
            numeric_features.remove(target_column)
        
        categorical_features = [
            col for col in df.columns
            if col not in numeric_features and col != target_column
        ]
        
        # Count missing values
        missing_values = df.isnull().sum().to_dict()
        missing_values = {k: v for k, v in missing_values.items() if v > 0}
        
        # Create summary
        summary = f"""
Dataset Shape: {df.shape}
Numeric Features: {len(numeric_features)}
Categorical Features: {len(categorical_features)}
Missing Values: {len(missing_values)} columns with missing data
Target Class Distribution:
{df[target_column].value_counts().to_string() if target_column in df.columns else 'N/A'}
"""
        
        info = DatasetInfo(
            shape=df.shape,
            features=[col for col in df.columns if col != target_column],
            target=target_column,
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            missing_values=missing_values,
            categorical_features=categorical_features,
            numeric_features=numeric_features,
            data_summary=summary
        )
        
        self.numeric_features = numeric_features
        self.categorical_features = categorical_features
        
        logger.info(f"Dataset analysis complete: {len(numeric_features)} numeric, {len(categorical_features)} categorical")
        return info
    
    def preprocess(
        self,
        df: pd.DataFrame,
        target_column: str,
        fit: bool = True
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Apply complete preprocessing pipeline
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            fit: Whether to fit transformers or use existing
            
        Returns:
            Tuple of (processed features, target)
        """
        df = df.copy()
        
        # Separate features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Handle missing values
        X = self._handle_missing_values(X, fit)
        
        # Encode categorical features
        X = self._encode_categorical(X, fit)
        
        # Scale numeric features
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
                    # Numeric: fill with median
                    fill_value = X[col].median()
                    X[col].fillna(fill_value, inplace=True)
                    logger.info(f"Filled {col} with median: {fill_value:.2f}")
                else:
                    # Categorical: fill with mode
                    fill_value = X[col].mode()[0] if not X[col].mode().empty else 'unknown'
                    X[col].fillna(fill_value, inplace=True)
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
        
        Args:
            X: Features
            y: Target
            test_size: Test set ratio
            random_state: Random seed
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y if len(y.unique()) < 20 else None
        )
        
        logger.info(f"Data split: train {X_train.shape}, test {X_test.shape}")
        return X_train, X_test, y_train, y_test


# Utility functions
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
    
    Args:
        file_content: Uploaded file bytes (None for synthetic)
        task: ML task type
        synthetic: Whether to generate synthetic data
        target_column: Target column name
        
    Returns:
        Tuple of (processed_df, target_col, dataset_info)
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
    
    dataset_info = preprocessor.analyze_data(df, target_column)
    return df, target_column, dataset_info