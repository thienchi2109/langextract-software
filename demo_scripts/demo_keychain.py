#!/usr/bin/env python3
"""
Demonstration script for KeychainManager functionality.
This script shows how to use the KeychainManager for secure credential storage.
"""

import sys
import os

# Add the current directory to Python path so we can import core modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.keychain import KeychainManager
from core.exceptions import CredentialError


def main():
    """Demonstrate KeychainManager functionality."""
    print("=== KeychainManager Demonstration ===\n")
    
    try:
        # Initialize KeychainManager
        print("1. Initializing KeychainManager...")
        keychain = KeychainManager()
        print("   ✓ KeychainManager initialized successfully")
        
        # Check if API key already exists
        print("\n2. Checking for existing API key...")
        if keychain.has_api_key():
            masked_key = keychain.get_masked_api_key()
            print(f"   ✓ Found existing API key: {masked_key}")
            
            # Ask user if they want to replace it
            response = input("   Do you want to replace the existing key? (y/n): ").lower().strip()
            if response != 'y':
                print("   Keeping existing key.")
                return
        else:
            print("   No existing API key found.")
        
        # Get API key from user
        print("\n3. API Key Input:")
        print("   Note: For demonstration, you can enter 'demo-key' to skip validation")
        api_key = input("   Enter your Gemini API key: ").strip()
        
        if not api_key:
            print("   No API key provided. Exiting.")
            return
        
        # Save API key
        print("\n4. Saving API key...")
        if api_key == "demo-key":
            print("   Demo mode: Skipping validation and using mock storage")
            # For demo purposes, we'll simulate success
            print("   ✓ API key saved successfully (demo mode)")
        else:
            try:
                success = keychain.save_api_key(api_key)
                if success:
                    print("   ✓ API key saved and validated successfully")
                else:
                    print("   ✗ Failed to save API key")
                    return
            except CredentialError as e:
                print(f"   ✗ Error saving API key: {e.message}")
                return
        
        # Load and display masked key
        print("\n5. Loading and displaying masked API key...")
        if api_key == "demo-key":
            masked = "demo****key"
        else:
            masked = keychain.get_masked_api_key()
        
        if masked:
            print(f"   ✓ Masked API key: {masked}")
        else:
            print("   ✗ Could not retrieve API key")
        
        # Ask if user wants to delete the key
        print("\n6. Cleanup:")
        response = input("   Do you want to delete the stored API key? (y/n): ").lower().strip()
        if response == 'y':
            if api_key == "demo-key":
                print("   ✓ API key deleted successfully (demo mode)")
            else:
                try:
                    success = keychain.delete_api_key()
                    if success:
                        print("   ✓ API key deleted successfully")
                    else:
                        print("   ✗ Failed to delete API key")
                except CredentialError as e:
                    print(f"   ✗ Error deleting API key: {e.message}")
        else:
            print("   API key kept in secure storage")
        
        print("\n=== Demonstration Complete ===")
        
    except CredentialError as e:
        print(f"\n✗ Credential Error: {e.message}")
        if e.suggestions:
            print("Suggestions:")
            for suggestion in e.suggestions:
                print(f"  • {suggestion}")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {str(e)}")


if __name__ == "__main__":
    main()