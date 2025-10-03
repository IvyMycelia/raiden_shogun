"""
Test script to validate the refactored system.
"""

import sys
import os

# Add bot directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Set environment variables for testing
        os.environ['BOT_TOKEN'] = 'test_token'
        os.environ['GUILD_ID'] = '123456789'
        os.environ['ADMIN_USER_ID'] = '987654321'
        
        # Test config
        from config.settings import config
        from config.constants import GameConstants
        print("✅ Config modules imported successfully")
        
        # Test models
        from models.nation import Nation, City
        from models.alliance import Alliance
        from models.war import War
        from models.user import User
        print("✅ Model classes imported successfully")
        
        # Test services
        from services.nation_service import NationService
        from services.alliance_service import AllianceService
        from services.war_service import WarService
        from services.raid_service import RaidService
        from services.cache_service import CacheService
        print("✅ Service classes imported successfully")
        
        # Test API
        from api.key_manager import APIKeyManager
        from api.politics_war_api import PoliticsWarAPI
        print("✅ API classes imported successfully")
        
        # Test utils
        from utils.pagination import Paginator, RaidPaginator
        from utils.formatting import format_number, format_currency
        from utils.validation import validate_nation_id
        from utils.logging import setup_logging
        print("✅ Utility functions imported successfully")
        
        # Test cogs
        from cogs.nation.info import NationInfoCog
        from cogs.nation.raid import RaidCog
        from cogs.nation.search import NationSearchCog
        from cogs.alliance.audit import AllianceAuditCog
        from cogs.alliance.management import AllianceManagementCog
        from cogs.war.detection import WarDetectionCog
        from cogs.war.analysis import WarAnalysisCog
        from cogs.utility.help import HelpCog
        from cogs.utility.feedback import FeedbackCog
        print("✅ Cog classes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration system."""
    print("\nTesting configuration...")
    
    try:
        # Set environment variables for testing
        os.environ['BOT_TOKEN'] = 'test_token'
        os.environ['GUILD_ID'] = '123456789'
        os.environ['ADMIN_USER_ID'] = '987654321'
        
        from config.settings import config
        from config.constants import GameConstants
        
        # Test API keys
        assert len(config.API_KEYS) == 4, "Should have 4 API key scopes"
        assert "everything_scope" in config.API_KEYS, "Should have everything_scope"
        assert "alliance_scope" in config.API_KEYS, "Should have alliance_scope"
        assert "personal_scope" in config.API_KEYS, "Should have personal_scope"
        assert "messaging_scope" in config.API_KEYS, "Should have messaging_scope"
        
        # Test constants
        assert GameConstants.WAR_DURATION_TURNS == 60, "War duration should be 60 turns"
        assert GameConstants.MIN_LOOT_POTENTIAL == 100000, "Min loot potential should be 100k"
        
        print("✅ Configuration system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_services():
    """Test service layer."""
    print("\nTesting services...")
    
    try:
        # Set environment variables for testing
        os.environ['BOT_TOKEN'] = 'test_token'
        os.environ['GUILD_ID'] = '123456789'
        os.environ['ADMIN_USER_ID'] = '987654321'
        
        from services.nation_service import NationService
        from services.alliance_service import AllianceService
        from services.war_service import WarService
        from services.raid_service import RaidService
        from services.cache_service import CacheService
        
        # Test service instantiation
        nation_service = NationService()
        alliance_service = AllianceService()
        war_service = WarService()
        raid_service = RaidService()
        cache_service = CacheService()
        
        print("✅ All services instantiated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Service error: {e}")
        return False

def test_models():
    """Test data models."""
    print("\nTesting models...")
    
    try:
        from models.nation import Nation, City
        from models.alliance import Alliance
        from models.war import War
        from models.user import User
        
        # Test City model
        city_data = {
            'id': 1,
            'name': 'Test City',
            'nation_id': 123,
            'infrastructure': 1000,
            'land': 500,
            'population': 100000,
            'age': 30,
            'pollution': 10,
            'commerce': 50,
            'crime': 5.0,
            'disease': 2.0,
            'power': 1000,
            'power_plants': {},
            'improvements': {},
            'resources': {}
        }
        city = City.from_dict(city_data)
        assert city.name == 'Test City'
        assert city.infrastructure == 1000
        
        # Test Nation model
        nation_data = {
            'id': 123,
            'nation_name': 'Test Nation',
            'leader_name': 'Test Leader',
            'score': 1000.0,
            'cities': 1,
            'color': 'blue',
            'alliance_id': 456,
            'alliance': 'Test Alliance',
            'alliance_position': 'MEMBER',
            'last_active': '2024-01-01T00:00:00+00:00',
            'soldiers': 1000,
            'tanks': 50,
            'aircraft': 10,
            'ships': 5,
            'spies': 25,
            'missiles': 0,
            'nukes': 0,
            'projects': 5,
            'vmode': False,
            'beige_turns': 0,
            'defensive_wars': 0,
            'offensive_wars': 0,
            'money': 1000000.0,
            'coal': 1000.0,
            'oil': 1000.0,
            'uranium': 100.0,
            'iron': 1000.0,
            'bauxite': 1000.0,
            'lead': 1000.0,
            'gasoline': 500.0,
            'munitions': 500.0,
            'steel': 500.0,
            'aluminum': 500.0,
            'food': 1000.0,
            'credits': 10,
            'gdp': 1000000.0,
            'cities': [city_data],
            'wars': []
        }
        nation = Nation.from_dict(nation_data)
        assert nation.name == 'Test Nation'
        assert nation.score == 1000.0
        assert len(nation.cities_data) == 1
        
        print("✅ All models working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_utils():
    """Test utility functions."""
    print("\nTesting utilities...")
    
    try:
        # Set environment variables for testing
        os.environ['BOT_TOKEN'] = 'test_token'
        os.environ['GUILD_ID'] = '123456789'
        os.environ['ADMIN_USER_ID'] = '987654321'
        
        # Import after setting environment variables
        import importlib
        import sys
        sys.path.append('bot')
        
        # Force reload modules to pick up environment variables
        if 'config.settings' in sys.modules:
            importlib.reload(sys.modules['config.settings'])
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        
        from utils.formatting import format_number, format_currency
        from utils.validation import validate_nation_id
        
        # Test formatting
        assert format_number(1000) == "1K"
        assert format_number(1000000) == "1M"
        assert format_number(1000000000) == "1B"
        assert format_currency(1000) == "$1.00K"
        
        # Test validation
        assert validate_nation_id(123) == 123
        assert validate_nation_id("123") == 123
        assert validate_nation_id(-1) is None
        assert validate_nation_id("invalid") is None
        
        print("✅ Utility functions working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Utility error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Raiden Shogun Bot System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_models,
        test_services,
        test_utils
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
