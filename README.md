
# Projects

## concerts
Trying to get concert videos from different parties synced up on a timeline & on beat.

### Current organization
- Put concert videos in user-specific folder in concert-specific folder
- Run convert_and_index on concert videos folder to create **Index** and **Manifest**
- Start serving website from simple_http_server
- Access concert view page at the html page in webcode folder

Or, as copilot put it in instructions to itself:

**Data Flow**:
1. Users upload MOV files to `concerts/[concert]/videos/[username]/`
2. `convert_and_index.py` converts to MP4, extracts timestamps, generates `index.json` per user
3. Script generates master `manifest.json` linking all user manifests
4. Web interface loads manifest, renders timeline, enables synchronized multi-user playback

**File Patterns**:
- `manifest.json`: Concert-level metadata with user list and manifest paths
- `videos/[user]/index.json`: User's video list with timestamps and durations
- `videos/[user]/processed/`: Original MOV files moved here after conversion
- `webcode/[concert-slug].html`: Hard-coded concert-specific pages