# Contributing Guidelines

## Code Quality Standards

This project uses **Ruff** with ALL rules enabled by default. This ensures maximum code quality and catches potential issues early.

### Using Inline Disables

When you need to disable a specific rule, use inline comments with explanations:

```python
# Good - explains why the rule is disabled
result = complex_function(a, b, c, d, e, f, g, h)  # noqa: PLR0913 - API requires all parameters

# Bad - no explanation
result = complex_function(a, b, c, d, e, f, g, h)  # noqa: PLR0913
```

### Common Inline Disables

```python
# For unavoidable print statements in CLI tools
print(f"Processing {filename}...")  # noqa: T201 - CLI output needed

# For necessary use of Any in generic functions
def process_data(data: Any) -> dict:  # noqa: ANN401 - accepts multiple types by design
    ...

# For intentionally catching broad exceptions
try:
    risky_operation()
except Exception as e:  # noqa: BLE001 - need to catch all errors for graceful degradation
    logger.error(f"Operation failed: {e}")
```

### Philosophy

1. **Start strict**: Enable all rules by default
2. **Disable locally**: Use inline comments for specific exceptions
3. **Document why**: Always explain why a rule is disabled
4. **Review regularly**: Periodically review disabled rules to see if they can be re-enabled

This approach ensures we maintain high code quality while allowing flexibility where needed.