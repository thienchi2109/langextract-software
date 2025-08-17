"""
Unit tests for configuration management system.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.models import AppConfig
from core.utils import load_config, save_config, get_app_data_dir, get_config_file
from core.exceptions import ConfigurationError


class TestConfigManagement:
    """Test cases for configuration management."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_app_data_dir(self, temp_dir):
        """Mock app data directory to use temp directory."""
        with patch('core.utils.get_app_data_dir', return_value=temp_dir):
            yield temp_dir
    
    def test_app_config_default_values(self):
        """Test AppConfig default values."""
        config = AppConfig()
        
        assert config.ocr_enabled is True
        assert config.ocr_languages == ['vi', 'en']
        assert config.proofread_enabled is True
        assert config.pii_masking_enabled is True
        assert config.offline_mode is False
        assert config.max_workers == 4
        assert config.log_level == 'INFO'
        assert config.ocr_dpi == 300
        assert config.api_timeout == 30
    
    def test_app_config_to_dict(self):
        """Test AppConfig serialization to dictionary."""
        config = AppConfig(
            ocr_enabled=False,
            ocr_languages=['en'],
            proofread_enabled=False,
            pii_masking_enabled=False,
            offline_mode=True,
            max_workers=2,
            log_level='DEBUG',
            ocr_dpi=150,
            api_timeout=60
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['ocr_enabled'] is False
        assert config_dict['ocr_languages'] == ['en']
        assert config_dict['proofread_enabled'] is False
        assert config_dict['pii_masking_enabled'] is False
        assert config_dict['offline_mode'] is True
        assert config_dict['max_workers'] == 2
        assert config_dict['log_level'] == 'DEBUG'
        assert config_dict['ocr_dpi'] == 150
        assert config_dict['api_timeout'] == 60
    
    def test_app_config_from_dict(self):
        """Test AppConfig deserialization from dictionary."""
        config_data = {
            'ocr_enabled': False,
            'ocr_languages': ['en'],
            'proofread_enabled': False,
            'pii_masking_enabled': False,
            'offline_mode': True,
            'max_workers': 2,
            'log_level': 'DEBUG',
            'ocr_dpi': 150,
            'api_timeout': 60
        }
        
        config = AppConfig.from_dict(config_data)
        
        assert config.ocr_enabled is False
        assert config.ocr_languages == ['en']
        assert config.proofread_enabled is False
        assert config.pii_masking_enabled is False
        assert config.offline_mode is True
        assert config.max_workers == 2
        assert config.log_level == 'DEBUG'
        assert config.ocr_dpi == 150
        assert config.api_timeout == 60
    
    def test_app_config_from_dict_partial(self):
        """Test AppConfig deserialization with partial data (uses defaults)."""
        config_data = {
            'ocr_enabled': False,
            'max_workers': 8
        }
        
        config = AppConfig.from_dict(config_data)
        
        assert config.ocr_enabled is False  # From data
        assert config.max_workers == 8      # From data
        assert config.ocr_languages == ['vi', 'en']  # Default
        assert config.proofread_enabled is True      # Default
        assert config.log_level == 'INFO'            # Default
    
    def test_app_config_from_dict_empty(self):
        """Test AppConfig deserialization with empty data (all defaults)."""
        config = AppConfig.from_dict({})
        
        # Should use all default values
        assert config.ocr_enabled is True
        assert config.ocr_languages == ['vi', 'en']
        assert config.proofread_enabled is True
        assert config.pii_masking_enabled is True
        assert config.offline_mode is False
        assert config.max_workers == 4
        assert config.log_level == 'INFO'
        assert config.ocr_dpi == 300
        assert config.api_timeout == 30
    
    def test_load_config_no_file(self, mock_app_data_dir):
        """Test loading config when no config file exists (returns defaults)."""
        config = load_config()
        
        # Should return default configuration
        assert isinstance(config, AppConfig)
        assert config.ocr_enabled is True
        assert config.ocr_languages == ['vi', 'en']
        assert config.max_workers == 4
    
    def test_load_config_valid_file(self, mock_app_data_dir):
        """Test loading config from valid file."""
        config_file = mock_app_data_dir / 'config.json'
        config_data = {
            'ocr_enabled': False,
            'max_workers': 8,
            'log_level': 'DEBUG'
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        config = load_config()
        
        assert config.ocr_enabled is False
        assert config.max_workers == 8
        assert config.log_level == 'DEBUG'
        # Should use defaults for missing values
        assert config.ocr_languages == ['vi', 'en']
        assert config.proofread_enabled is True
    
    def test_load_config_invalid_json(self, mock_app_data_dir):
        """Test loading config from file with invalid JSON."""
        config_file = mock_app_data_dir / 'config.json'
        config_file.write_text("{ invalid json }")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config()
        
        assert "Failed to load configuration" in str(exc_info.value)
    
    def test_load_config_missing_required_keys(self, mock_app_data_dir):
        """Test loading config with missing required structure."""
        config_file = mock_app_data_dir / 'config.json'
        # Valid JSON but might cause issues in from_dict
        config_file.write_text('{"invalid_key": "value"}')
        
        # Should still work because from_dict uses defaults for missing keys
        config = load_config()
        assert isinstance(config, AppConfig)
        assert config.ocr_enabled is True  # Default value
    
    def test_save_config_success(self, mock_app_data_dir):
        """Test successful config saving."""
        config = AppConfig(
            ocr_enabled=False,
            max_workers=8,
            log_level='DEBUG'
        )
        
        save_config(config)
        
        # Verify file was created and contains correct data
        config_file = mock_app_data_dir / 'config.json'
        assert config_file.exists()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['ocr_enabled'] is False
        assert saved_data['max_workers'] == 8
        assert saved_data['log_level'] == 'DEBUG'
    
    def test_save_config_creates_directory(self, temp_dir):
        """Test that save_config creates directory if it doesn't exist."""
        non_existent_dir = temp_dir / 'non_existent'
        
        with patch('core.utils.get_app_data_dir', return_value=non_existent_dir):
            config = AppConfig()
            save_config(config)
            
            # Directory should be created
            assert non_existent_dir.exists()
            assert (non_existent_dir / 'config.json').exists()
    
    @patch('builtins.open')
    def test_save_config_io_error(self, mock_open, mock_app_data_dir):
        """Test handling of IO errors during config save."""
        mock_open.side_effect = OSError("Permission denied")
        
        config = AppConfig()
        
        with pytest.raises(ConfigurationError) as exc_info:
            save_config(config)
        
        assert "Failed to save configuration" in str(exc_info.value)
    
    def test_save_and_load_roundtrip(self, mock_app_data_dir):
        """Test saving and loading config maintains data integrity."""
        original_config = AppConfig(
            ocr_enabled=False,
            ocr_languages=['en', 'fr'],
            proofread_enabled=False,
            pii_masking_enabled=False,
            offline_mode=True,
            max_workers=16,
            log_level='WARNING',
            ocr_dpi=600,
            api_timeout=120
        )
        
        # Save config
        save_config(original_config)
        
        # Load config
        loaded_config = load_config()
        
        # Verify all values match
        assert loaded_config.ocr_enabled == original_config.ocr_enabled
        assert loaded_config.ocr_languages == original_config.ocr_languages
        assert loaded_config.proofread_enabled == original_config.proofread_enabled
        assert loaded_config.pii_masking_enabled == original_config.pii_masking_enabled
        assert loaded_config.offline_mode == original_config.offline_mode
        assert loaded_config.max_workers == original_config.max_workers
        assert loaded_config.log_level == original_config.log_level
        assert loaded_config.ocr_dpi == original_config.ocr_dpi
        assert loaded_config.api_timeout == original_config.api_timeout
    
    def test_get_app_data_dir_creates_directory(self):
        """Test that get_app_data_dir creates directory if it doesn't exist."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path(tempfile.mkdtemp())
            
            app_data_dir = get_app_data_dir()
            
            assert app_data_dir.exists()
            assert app_data_dir.is_dir()
            assert app_data_dir.name == 'LangExtractor'
            
            # Cleanup
            shutil.rmtree(mock_home.return_value)
    
    def test_get_config_file_path(self, mock_app_data_dir):
        """Test get_config_file returns correct path."""
        config_file = get_config_file()
        
        assert config_file == mock_app_data_dir / 'config.json'
        assert config_file.parent == mock_app_data_dir
        assert config_file.name == 'config.json'
    
    def test_config_unicode_support(self, mock_app_data_dir):
        """Test that config supports Unicode characters."""
        config = AppConfig(
            ocr_languages=['vi', 'en', 'zh'],  # Multiple languages
            log_level='THÔNG TIN'  # Vietnamese text
        )
        
        # Save and load
        save_config(config)
        loaded_config = load_config()
        
        assert loaded_config.ocr_languages == ['vi', 'en', 'zh']
        assert loaded_config.log_level == 'THÔNG TIN'
    
    def test_config_validation_edge_cases(self):
        """Test AppConfig with edge case values."""
        # Test with extreme values
        config = AppConfig(
            max_workers=1,  # Minimum
            ocr_dpi=72,     # Low DPI
            api_timeout=1   # Very short timeout
        )
        
        config_dict = config.to_dict()
        restored_config = AppConfig.from_dict(config_dict)
        
        assert restored_config.max_workers == 1
        assert restored_config.ocr_dpi == 72
        assert restored_config.api_timeout == 1