import playwright_mcp

# Look at all attributes
print(dir(playwright_mcp))

# Check for classes specifically
classes = [attr for attr in dir(playwright_mcp) if isinstance(getattr(playwright_mcp, attr), type)]
print(classes)
