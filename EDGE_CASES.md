# Edge Cases for `aggregate_sleep_data()` Function

## Critical Issues (Will Cause Crashes)

### 1. **Missing Required Fields**
- **`sleep.json`**: Missing `'sleep_start'`, `'sleep_quality'`, or `'sleep_duration'` → **KeyError**
- **`workouts.json`**: Missing `'time'`, `'calories_burned'`, `'name'`, `'description'`, `'muscles'`, or `'equipment'` → **KeyError**

### 2. **Type Mismatches in Workout Data**
- **`calories_burned`**: Must be numeric (int/float). If string or None → **TypeError** when using `+=`
- **`muscles`**: Must be a list. If string, dict, or None → **TypeError** when using `+=` (line 121)
- **`equipment`**: Must be a list. If string, dict, or None → **TypeError** when using `+=` (line 122)
- **`name`**: Must be a string. If int, list, or None → **TypeError** when using `+=` (line 119)
- **`description`**: Must be a string. If int, list, or None → **TypeError** when using `+=` (line 120)

### 3. **Unparseable Timestamps**
- Invalid date/time format that `parser.parse()` cannot handle → **ValueError** or **ParserError**
- Examples: `"invalid date"`, `"2023-13-45"`, `"not a timestamp"`

### 4. **Unknown Timezone Abbreviations**
- Timezone abbreviation not in `tzinfos` dictionary → **UnknownTimezoneWarning** or parsing failure
- Examples: `"XXX"`, `"INVALID"`, or abbreviations not covered by `get_comprehensive_tzinfos()`

### 5. **Null/None Values**
- Any field set to `null` in JSON → **TypeError** when trying to use the value
- Example: `{"sleep_start": null, "sleep_quality": 5, "sleep_duration": 8}`

### 6. **Invalid JSON Structure**
- Files not containing arrays `[]` → **TypeError** when iterating
- Example: `{"data": [...]}` instead of `[...]`
- Example: `"string"` or `123` instead of array

## Data Integrity Issues (Silent Failures or Incorrect Results)

### 7. **Multiple Sleep Entries Per Day**
- **Current behavior**: Later entries overwrite earlier ones (line 109)
- **Impact**: Data loss - only the last sleep entry for a day is kept
- **Example**: Two sleep entries for "2023-10-15" → only the second one is stored

### 8. **Empty Lists for `muscles` or `equipment`**
- Empty arrays `[]` will concatenate but may create unexpected data structures
- Example: `[] += []` works but might not be intended behavior

### 9. **Negative or Invalid Numeric Values**
- **`calories_burned`**: Negative values are allowed but may be invalid
- **`sleep_duration`**: Negative values are allowed but invalid (e.g., `-5` hours)
- **`sleep_quality`**: No validation on range (could be 0, negative, or extremely large)

### 10. **Empty JSON Files**
- Empty arrays `[]` → Function completes but produces empty `days.json`
- Not an error, but may not be intended

### 11. **String Concatenation Issues**
- If `name` or `description` contain special characters or are very long, concatenation with `", "` might create unwieldy strings
- No limit on string length

### 12. **List Concatenation Issues**
- `muscles` and `equipment` lists are concatenated with `+=`, which extends the list
- If lists are very large, this could create very long lists
- Example: `[1, 2] += [3, 4]` → `[1, 2, 3, 4]` (works, but may not be intended)

### 13. **Date Boundary Edge Cases**
- Sleep that starts late at night might convert to next day in UTC
- Workout times might span midnight in UTC
- Function handles this correctly, but could be confusing

### 14. **Duplicate Workout Times**
- Multiple workouts at the same time on the same day will all be concatenated
- Example: `"14:30:00, 14:30:00, 14:30:00"` if three workouts at same time

## Potential Runtime Issues

### 15. **Very Large Files**
- If JSON files are extremely large, memory issues could occur
- No streaming/chunking implemented

### 16. **File Permission Issues**
- Cannot write to `days.json` → **PermissionError** or **IOError**
- Read-only filesystem or insufficient permissions

### 17. **Malformed JSON**
- Invalid JSON syntax → **json.JSONDecodeError**
- Example: Missing commas, unclosed brackets, trailing commas (depending on strictness)

### 18. **Timezone Parsing Edge Cases**
- Some timezone abbreviations might be ambiguous (e.g., "CST" could be China Standard Time or Central Standard Time)
- `get_comprehensive_tzinfos()` might not capture all possible abbreviations
- Abbreviations that change over time (historical timezones)

## Recommendations for Robustness

1. **Add field validation**: Check if required fields exist before accessing
2. **Add type checking**: Validate types before operations (especially for `+=` operations)
3. **Handle None/null values**: Check for None before using values
4. **Handle multiple sleep entries**: Decide whether to average, sum, or take first/last
5. **Add try-except blocks**: Catch parsing errors and provide meaningful error messages
6. **Validate numeric ranges**: Check that `sleep_duration` >= 0, `calories_burned` >= 0, etc.
7. **Handle empty files gracefully**: Check if arrays are empty before processing
8. **Add logging**: Log warnings for unexpected data instead of silently failing
