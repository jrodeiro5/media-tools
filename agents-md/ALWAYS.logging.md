# logging

## main configuration

- Create global logging configuration supporting text and JSON formats; JSON for production
- Use INFO level for all backend REST endpoint calls and results
- Output audit lines (who, what, which object) as INFO with "AUDIT" in message
- Include DEBUG, WARN, ERROR, and FATAL levels as appropriate
- Log messages with actual data (object IDs) for differentiation; no generic placeholder output
- Docker: emit all component logs to stdout via container default logging
- Non-Docker: configure maximum file count, daily rotation, gzip compression; use Docker volumes for storage

## logging format

### One-line JSON with ISO 8601 date, level, then JSON data

Pattern (no newlines/carriage returns):
```YYYY-MM-dd hh:mm:ss.ms+TZ LEVEL { one line json data }```

Example:
```2025-03-12 12:32:12.123+02:00 INFO {"msg": "Sending data", "version": "12.3", "trs_id": "-", "fps": 12, "key": "logs", "location_geo": {"latitude": 40.441, "longitude": -3.707}}```

### Required fields

- **msg**: Plain text describing what happened with identifying information (IDs, etc.)
- **version**: Software version from version.txt

### Optional fields

- **trs_id**: Transaction ID for API call traversal; propagate downward to track related calls
- **thread**: Thread ID executing the process
- **code_line**: File name and code line generating exception (if available)
- Additional debugging fields (username, etc.)

### Level values

LEVEL: DEBUG | INFO | WARN | ERROR | FATAL

### PII masking

Never output PII or passwords in plain text. Mask with asterisks: `DNI: ***323***`

[rev. 1]
