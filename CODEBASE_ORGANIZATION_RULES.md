# 📋 Codebase Organization Rulesheet

## 🎯 **Overview**
This document defines the organizational structure and coding standards for the Raiden Shogun Discord bot codebase. The goal is to maintain a clean, scalable, and maintainable codebase with clear separation of concerns.

## 📏 **File Size & Structure Rules**

### **1. File Size Limits**
- **Maximum 3,000 LoC per file** (hard limit)
- **Target 500-1,500 LoC per file** (optimal)
- **Minimum 50 LoC per file** (unless utility/constant files)
- **Exception**: Configuration files can be smaller

### **2. Directory Structure**
```
bot/
├── main.py                    # Entry point only (< 200 LoC)
├── runner.py                  # Process management only (< 100 LoC)
├── config/                    # Configuration management
│   ├── __init__.py
│   ├── settings.py           # Environment variables
│   └── constants.py          # Game constants
├── models/                    # Data models & DTOs
│   ├── __init__.py
│   ├── nation.py             # Nation data model
│   ├── alliance.py           # Alliance data model
│   ├── war.py                # War data model
│   └── user.py               # User data model
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── nation_service.py     # Nation operations
│   ├── alliance_service.py   # Alliance operations
│   ├── war_service.py        # War operations
│   ├── raid_service.py       # Raid calculations
│   └── cache_service.py      # Caching operations
├── api/                       # External API interactions
│   ├── __init__.py
│   ├── politics_war_api.py   # P&W API client
│   └── discord_api.py        # Discord API helpers
├── cogs/                      # Discord command groups
│   ├── __init__.py
│   ├── nation/               # Nation-related commands
│   │   ├── __init__.py
│   │   ├── info.py           # Nation info commands
│   │   ├── raid.py           # Raid commands
│   │   └── search.py         # Nation search commands
│   ├── alliance/             # Alliance-related commands
│   │   ├── __init__.py
│   │   ├── audit.py          # Audit commands
│   │   └── management.py     # Alliance management
│   ├── war/                  # War-related commands
│   │   ├── __init__.py
│   │   ├── detection.py      # War detection
│   │   └── analysis.py       # War analysis
│   └── utility/              # Utility commands
│       ├── __init__.py
│       ├── help.py
│       └── feedback.py
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── pagination.py         # Pagination helpers
│   ├── formatting.py         # Text formatting
│   ├── validation.py         # Input validation
│   └── logging.py            # Logging utilities
└── data/                     # Data storage
    ├── cache/                # Cache files
    ├── json/                 # JSON data files
    └── migrations/           # Database migrations
```

## 🎯 **File Purpose Guidelines**

### **3. Single Responsibility Principle**
- **One purpose per file**
- **One class per file** (unless closely related)
- **One service per file**
- **One command group per file**

### **4. Layer Separation**
- **Models**: Data structures only
- **Services**: Business logic only
- **API**: External communication only
- **Cogs**: Discord command handling only
- **Utils**: Pure functions only

### **5. Naming Conventions**
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

## 🔧 **Refactoring Guidelines**

### **6. When to Split Files**
- File exceeds 2,000 LoC
- Multiple unrelated responsibilities
- Complex nested logic
- Hard to navigate or understand

### **7. When to Merge Files**
- Files under 100 LoC with related functionality
- Duplicate code across files
- Overly granular separation

### **8. Service Layer Rules**
- Extract business logic from cogs
- Create dedicated service classes
- Implement dependency injection
- No Discord-specific code in services

## 📝 **Code Quality Standards**

### **9. Documentation**
- **Docstrings** for all public functions
- **Type hints** for all function parameters
- **Comments** for complex logic
- **README** for each major module

### **10. Error Handling**
- **Try-catch** blocks for all external API calls
- **Logging** for all errors
- **User-friendly** error messages
- **Graceful degradation** when possible

### **11. Testing**
- **Unit tests** for all services
- **Integration tests** for API calls
- **Mock external dependencies**
- **Test coverage** > 80%

## 🚀 **Migration Strategy**

### **Phase 1: Split Large Files**
1. **Split `nation.py` (2,922 LoC)** into:
   - `cogs/nation/info.py` - Nation info commands
   - `cogs/nation/raid.py` - Raid commands  
   - `cogs/nation/search.py` - Search commands
   - `services/nation_service.py` - Nation business logic

2. **Split `data.py` (964 LoC)** into:
   - `api/politics_war_api.py` - API client
   - `services/cache_service.py` - Caching logic
   - `models/` - Data models

### **Phase 2: Create Service Layer**
- Extract business logic from cogs
- Create dedicated service classes
- Implement dependency injection

### **Phase 3: Reorganize Structure**
- Move files to new directory structure
- Update all imports
- Test functionality

## ⚠️ **Current Violations**

### **Files Over 3,000 LoC:**
- `bot/cogs/nation.py` - **2,922 LoC** ❌

### **Files Over 1,500 LoC:**
- `bot/data.py` - **964 LoC** ⚠️

### **Mixed Responsibilities:**
- `bot/main.py` - Contains both bot setup and utility functions
- `bot/cogs/nation.py` - Contains multiple command types

## 📊 **Success Metrics**

### **Before Reorganization:**
- 1 file over 3,000 LoC
- 1 file over 1,500 LoC
- Mixed responsibilities in multiple files
- No clear service layer

### **After Reorganization:**
- 0 files over 3,000 LoC
- 0 files over 1,500 LoC
- Clear separation of concerns
- Proper service layer architecture
- Improved maintainability and testability

## 🔑 **API Key Management System**

### **API Key Rotation & Scoping**

**1. Key Pool Management:**
- **Rotation Strategy**: Round-robin cycling through available keys
- **Load Balancing**: Distribute API calls across multiple keys
- **Rate Limit Avoidance**: Prevent single-key throttling
- **Scope Enforcement**: Use appropriate keys for specific operations

**2. Key Configuration:**
```python
API_KEYS = {
    "everything_scope": [
        "1adc0368729abdbba56c",  # Everything Scope
        "29cc5d1b8aca3b02fe75"   # Everything Scope
    ],
    "alliance_scope": [
        "39c40d62a96e5e2fff86",  # Alliance Scope
        "ada85c10c9fe0944cbb1",  # Alliance Scope
        "8986a7e3c790d574a561",  # Alliance Scope
        "631fef9d485f7090dbfa"   # Alliance Scope
    ],
    "personal_scope": [
        "d26fe3dacf8ea09032b0"   # Personal (Nation 590508 only)
    ],
    "messaging_scope": [
        "2457ef98256e4256bd81"   # Send messages to nations
    ]
}
```

**3. Key Usage Rules:**
- **Everything Scope**: Nation data, war data, alliance data, city data
- **Alliance Scope**: Alliance members, alliance bank, alliance operations
- **Personal Scope**: Personal nation data only (Nation 590508)
- **Messaging Scope**: Send messages to nations (future feature)

**4. Rotation Implementation:**
```python
class APIKeyManager:
    def __init__(self):
        self.key_pools = API_KEYS
        self.current_indices = {scope: 0 for scope in API_KEYS.keys()}
        self.rate_limits = {key: {"calls": 0, "reset_time": 0} for key in self._get_all_keys()}
    
    def get_key(self, scope: str) -> str:
        """Get next available key for specified scope."""
        if scope not in self.key_pools:
            raise ValueError(f"Invalid scope: {scope}")
        
        keys = self.key_pools[scope]
        if not keys:
            raise ValueError(f"No keys available for scope: {scope}")
        
        # Round-robin selection
        key = keys[self.current_indices[scope]]
        self.current_indices[scope] = (self.current_indices[scope] + 1) % len(keys)
        
        return key
    
    def check_rate_limit(self, key: str) -> bool:
        """Check if key is within rate limits."""
        current_time = time.time()
        rate_data = self.rate_limits[key]
        
        # Reset if past reset time
        if current_time >= rate_data["reset_time"]:
            rate_data["calls"] = 0
            rate_data["reset_time"] = current_time + 3600  # 1 hour reset
        
        return rate_data["calls"] < 1000  # 1000 calls per hour limit
```

**5. File Organization for API Management:**
```
bot/
├── api/
│   ├── __init__.py
│   ├── key_manager.py          # API key rotation and management
│   ├── rate_limiter.py         # Rate limiting logic
│   ├── scope_validator.py      # Scope validation
│   └── politics_war_api.py     # Main API client with key rotation
```

**6. Integration Points:**
- **Data Fetching**: All `GET_*` functions use appropriate scoped keys
- **Cache Updates**: CSV downloads use everything scope keys
- **Audit Operations**: Alliance scope keys for member data
- **Personal Commands**: Personal scope key for user's nation
- **Future Messaging**: Messaging scope key for notifications

## 🔄 **Maintenance Rules**

### **Ongoing:**
- **Monitor file sizes** during development
- **Refactor** when files approach limits
- **Review** code organization monthly
- **Update** this document as needed
- **Monitor API key usage** and rotation
- **Track rate limit compliance** across all keys

### **Code Reviews:**
- Check file size compliance
- Verify single responsibility
- Ensure proper layer separation
- Validate naming conventions
- **Verify API key scoping** is correct
- **Check rate limiting** implementation

### **API Key Maintenance:**
- **Daily**: Monitor key usage and rate limits
- **Weekly**: Review key rotation effectiveness
- **Monthly**: Audit key permissions and scope usage
- **Quarterly**: Evaluate key pool size and distribution

---

**Last Updated:** 2024-09-30
**Version:** 1.1
**Maintainer:** Development Team
