# 🔍 Alliance Audit Guide

## **Who Can Use `/audit`?**
Only members with the **Audit Role** (ID: `1424323461446369340`) can run audit commands.

## **How to Use `/audit`**

### **Basic Command:**
```
/audit type:<audit_type> cities:<max_cities>
```

**Note:** The `cities` parameter is only used for `warchest` and `projects` audits.

### **Available Audit Types:**

#### **1. Activity Audit** (`/audit type:activity`)
- **Purpose**: Check if members are active (logged in within last 7 days)
- **What it checks**: Last login date from nation data
- **Violations**: Members who haven't logged in for 7+ days
- **Example**: `/audit type:activity`

#### **2. Warchest Audit** (`/audit type:warchest cities:50`)
- **Purpose**: Check if members have adequate warchest resources
- **What it checks**: 
  - Food, gasoline, munitions, steel, aluminum requirements
  - Uses 7-day warchest for C15+ nations, 5-day for others
  - Accounts for production and current resources
- **Parameters**: `cities` - Only audit members with ≤ this many cities
- **Violations**: Members with resource deficits
- **Example**: `/audit type:warchest cities:50`

#### **3. Spies Audit** (`/audit type:spies`)
- **Purpose**: Check if members have adequate spy counts
- **What it checks**: 
  - Current spies vs. required spies
  - CIA project detection (3 spies required if CIA, 2 otherwise)
- **Violations**: Members with insufficient spies
- **Example**: `/audit type:spies`

#### **4. Projects Audit** (`/audit type:projects`)
- **Purpose**: Check if raiders (C15 and below) have completed required projects when timer is up
- **What it checks**: 
  - Project timer (120 turns = 10 days)
  - Required projects: Activity Center, Propaganda Bureau, Intelligence Agency, Research & Development, Pirate Economy, Advanced Pirate Economy
- **Parameters**: `cities` - Maximum cities to audit (default: 15)
- **Violations**: Raiders with project timer up who are missing required projects
- **Example**: `/audit type:projects cities:15`

#### **5. Bloc Audit** (`/audit type:bloc`)
- **Purpose**: Check if members are in the correct color bloc
- **What it checks**: Alliance color vs. required bloc color
- **Violations**: Members in wrong color bloc
- **Example**: `/audit type:bloc`

#### **6. Military Audit** (`/audit type:military`)
- **Purpose**: Check if members have adequate military infrastructure
- **What it checks**: 
  - Barracks, hangars, drydocks, factories
  - Military unit capacity (79% threshold)
- **Violations**: Members below 79% military capacity
- **Example**: `/audit type:military`

#### **7. MMR Audit** (`/audit type:mmr`)
- **Purpose**: Check if members meet MMR (Military Management Rating) requirements
- **What it checks**: Role-specific military infrastructure requirements
- **Violations**: Members not meeting role requirements
- **Example**: `/audit type:mmr`

#### **8. Deposit Audit** (`/audit type:deposit`)
- **Purpose**: Check for resource excess or deficit in alliance bank
- **What it checks**: 
  - 120% excess threshold (too much in bank)
  - 80% deficit threshold (too little in bank)
- **Violations**: Members with improper bank deposits
- **Example**: `/audit type:deposit`

## **Command Examples:**

### **Check All Members' Activity:**
```
/audit type:activity
```

### **Check Warchest for Members with ≤30 Cities:**
```
/audit type:warchest cities:30
```

### **Check Spies for All Members:**
```
/audit type:spies
```

### **Check Military Infrastructure:**
```
/audit type:military
```

## **Understanding Results:**

### **✅ No Violations:**
- Shows "All Good! No violations found."
- Members are compliant with requirements

### **⚠️ Violations Found:**
- Lists specific members with issues
- Shows detailed violation information
- Uses pagination for large results

### **📊 Violation Details:**
- **Activity**: Shows last login date
- **Warchest**: Shows specific resource deficits
- **Spies**: Shows current vs. required spy count
- **Projects**: Shows missing projects
- **Bloc**: Shows current vs. required color
- **Military**: Shows capacity percentages
- **MMR**: Shows role-specific requirements
- **Deposit**: Shows excess/deficit amounts

## **Tips for Effective Auditing:**

1. **Use City Filters**: For warchest audits, filter by city count to focus on relevant members
2. **Regular Checks**: Run activity audits weekly, warchest audits before wars
3. **Follow Up**: Contact members with violations to resolve issues
4. **Document Results**: Keep track of repeat violators for disciplinary action

## **Troubleshooting:**

- **No Results**: Check if alliance has members registered
- **API Errors**: Bot will retry automatically, wait a moment
- **Missing Data**: Some members may not have complete data in API
- **Role Issues**: Ensure you have the Audit Role (ID: 1424323461446369340)

## **Best Practices:**

1. **Run audits during low-activity periods** to avoid API rate limits
2. **Use specific city filters** for warchest audits to focus on relevant members
3. **Follow up with violators** to ensure compliance
4. **Keep audit logs** for tracking member compliance over time