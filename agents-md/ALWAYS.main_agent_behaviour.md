# IDE/Agent behaviour

## TODO.md file

- Maintain a TODO.md file listing items to implement; check items as completed
- Add new items as needed to track pending changes
- Continue until all items are completed

## On each agent task completion

- Run tests with test data if implemented; repair any failures before continuing

- Increment the RELEASE version (third level) of modified components in their respective `version.txt` files after each task. Format: MAJOR.MINOR.RELEASE (e.g., "1.0.3"), no linefeeds

- If using Git, commit with message format: "v" + new version of each modified component (e.g., "frontend v1.0.3, backend v1.0.2") followed by a brief description (max 100 words) of all changes. Do NOT push to origin; a human will handle that.

[rev. 2]
