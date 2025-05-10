import json
import os
from pathlib import Path
import logging
from kivy.utils import platform

logger = logging.getLogger("chexam.secure_storage")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define the secure storage location based on platform
if platform == 'android':
    try:
        from android.storage import app_storage_path
        from jnius import autoclass
        
        # Use Android's secure storage
        Context = autoclass('android.content.Context')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        
        # Get the activity and context
        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()
        
        # Get the shared preferences
        SHARED_PREFS_NAME = "ChexamSecurePrefs"
        MODE_PRIVATE = 0
        secure_prefs = context.getSharedPreferences(SHARED_PREFS_NAME, MODE_PRIVATE)
        
        def save_api_key(key_name, api_key):
            """Save API key to Android's SharedPreferences"""
            editor = secure_prefs.edit()
            editor.putString(key_name, api_key)
            editor.apply()
            logger.info(f"Saved {key_name} to secure storage")
            return True
            
        def get_api_key(key_name, default=None):
            """Get API key from Android's SharedPreferences"""
            if secure_prefs.contains(key_name):
                return secure_prefs.getString(key_name, default)
            return default
            
        def delete_api_key(key_name):
            """Delete API key from Android's SharedPreferences"""
            if secure_prefs.contains(key_name):
                editor = secure_prefs.edit()
                editor.remove(key_name)
                editor.apply()
                logger.info(f"Deleted {key_name} from secure storage")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Failed to initialize Android secure storage: {e}")
        # Fall back to file-based storage
        platform = 'fallback'

# For non-Android platforms or if Android initialization fails, use file-based storage
if platform != 'android':
    # Create a secure directory for storing API keys
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    secure_dir = os.path.join(app_dir, 'secure')
    os.makedirs(secure_dir, exist_ok=True)
    
    # Create a .gitignore file to prevent accidental commits
    gitignore_path = os.path.join(secure_dir, '.gitignore')
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write('*\n!.gitignore\n')
    
    # File to store API keys
    keys_file = os.path.join(secure_dir, 'api_keys.json')
    
    def save_api_key(key_name, api_key):
        """Save API key to secure file storage"""
        try:
            # Load existing keys if file exists
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    keys = json.load(f)
            else:
                keys = {}
            
            # Update the key
            keys[key_name] = api_key
            
            # Save back to file
            with open(keys_file, 'w') as f:
                json.dump(keys, f)
                
            logger.info(f"Saved {key_name} to secure storage file")
            return True
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            return False
    
    def get_api_key(key_name, default=None):
        """Get API key from secure file storage"""
        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    keys = json.load(f)
                return keys.get(key_name, default)
            return default
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return default
    
    def delete_api_key(key_name):
        """Delete API key from secure file storage"""
        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    keys = json.load(f)
                
                if key_name in keys:
                    del keys[key_name]
                    
                    with open(keys_file, 'w') as f:
                        json.dump(keys, f)
                    
                    logger.info(f"Deleted {key_name} from secure storage file")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False

# Constants for key names
GEMINI_API_KEY = "GEMINI_API_KEY"
