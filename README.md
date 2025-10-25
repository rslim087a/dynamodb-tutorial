# DynamoDB Lab - Part 2: Python Application

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials:**
   ```bash
   aws configure
   # Enter your Access Key, Secret Key, and region (us-east-1)
   ```

3. **Update config.py** if your table name or region differs

4. **Run the demo:**
   ```bash
   python dynamo_app.py
   ```

## DynamoDB Best Practices Demonstrated

### 1. **Use Correct Operation Types**
- `put_item` - Create/replace entire item
- `get_item` - Retrieve by primary key (most efficient)
- `query` - Efficient retrieval within partition
- `update_item` - Partial updates only
- `delete_item` - Remove item

### 2. **Always Use Conditions**
- `ConditionExpression` prevents race conditions
- Prevents accidental overwrites
- Ensures item exists before operations

### 3. **Efficient Queries**
- Use `query` (not `scan`) whenever possible
- Query on partition key + sort key ranges
- Use GSI for alternate access patterns
- Never scan unless absolutely necessary

### 4. **Projection Expressions**
- Fetch only needed attributes
- Reduces data transfer and costs
- Improves performance

### 5. **Update Expressions**
- Use `SET`, `ADD`, `REMOVE` operations
- Atomic counter updates with `ADD`
- Update nested attributes with dot notation
- Send only changed data

### 6. **Expression Attribute Names**
- Use `#` placeholders for reserved words
- Required for: timestamp, status, data, etc.

### 7. **Batch Operations**
- `batch_get_item` for multiple reads (up to 100)
- `batch_write_item` for multiple writes (up to 25)
- More efficient than individual operations

### 8. **Error Handling**
- Catch `ConditionalCheckFailedException`
- Handle `ClientError` appropriately
- Use `ReturnValues` to get updated/deleted items

## Key Methods

| Method | Purpose | Best Practice |
|--------|---------|---------------|
| `put_user_profile()` | Create item | Use condition to prevent overwrites |
| `get_user_profile()` | Retrieve item | Use ProjectionExpression |
| `query_user_activity()` | Query by key | Use sort key conditions |
| `update_login_count()` | Atomic update | Use ADD for counters |
| `update_preferences()` | Nested update | Use dot notation |
| `query_by_email()` | GSI query | Use GSI for non-key queries |
| `delete_user_profile()` | Delete item | Use condition for safety |
| `batch_get_profiles()` | Batch read | Retrieve multiple items efficiently |

## Anti-Patterns to Avoid

❌ Using `scan` instead of `query`  
❌ Fetching entire item when only need few attributes  
❌ Replacing entire item for small updates  
❌ No condition expressions on writes  
❌ Not using batch operations  
❌ Ignoring GSI for alternate queries  
❌ Not handling conditional check failures
