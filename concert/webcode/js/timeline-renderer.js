// Multi-user timeline renderer component
// Usage: const timeline = new MultiUserTimelineRenderer(containerId, options)

class MultiUserTimelineRenderer {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.options = {
      onSegmentClick: options.onSegmentClick || null,
      ticksSelector: options.ticksSelector || null,
      ...options
    };
    
    this.users = [];
    this.masterData = null;
    this.currentSelectedSeg = null;
    this.timelineEl = null;
    
    console.log('MultiUserTimelineRenderer created for:', containerId);
  }

  async loadMasterManifest(manifestPath) {
    console.log('Loading master manifest:', manifestPath);
    try {
      const res = await fetch(encodeURI(manifestPath));
      if (!res.ok) throw new Error(`Master manifest not found: ${res.status}`);
      const masterData = await res.json();
      
      console.log('Master manifest data loaded:', masterData);
      
      if (!masterData.users || !Array.isArray(masterData.users)) {
        throw new Error('Invalid master manifest - missing users array');
      }
      
      this.masterData = masterData;
      
      // Load each user's individual manifest
      const manifestDir = manifestPath.substring(0, manifestPath.lastIndexOf('/') + 1);
      console.log('Manifest directory:', manifestDir);
      
      this.users = [];
      for (const userInfo of masterData.users) {
        console.log('Loading user manifest for:', userInfo.username);
        try {
          const userManifestPath = manifestDir + userInfo.manifestPath;
          console.log('User manifest path:', userManifestPath);
          
          const userRes = await fetch(encodeURI(userManifestPath));
          if (!userRes.ok) {
            console.warn(`User manifest not found for ${userInfo.username}: ${userRes.status}`);
            continue;
          }
          
          const userData = await userRes.json();
          console.log(`User data loaded for ${userInfo.username}:`, userData);
          
          const videos = (userData.videos || []).filter(v => v.duration != null);
          const videoBase = userManifestPath.replace(/\/index\.json$/, '/');
          
          this.users.push({
            username: userInfo.username,
            displayName: userInfo.displayName,
            videos: videos,
            videoBase: videoBase,
            color: await this.getUserColor(userInfo.username)
          });
          
          console.log(`Loaded ${videos.length} videos for user ${userInfo.username}`);
        } catch (err) {
          console.warn(`Failed to load manifest for user ${userInfo.username}:`, err);
        }
      }
      
      console.log(`Loaded ${this.users.length} users with video data`);
      return true;
    } catch (err) {
      console.error('Failed to load master manifest:', err);
      throw err;
    }
  }

  async getUserColor(username) {
    try {
      // Fetch user colors from CSV file
      const response = await fetch('../users/users.csv');
      if (!response.ok) {
        console.warn('Could not fetch users.csv, using default colors');
        return this.getDefaultUserColor(username);
      }
      
      const csvText = await response.text();
      const lines = csvText.trim().split('\n');
      const headers = lines[0].split(',').map(h => h.replace(/"/g, '').toLowerCase());
      
      const usernameIndex = headers.indexOf('username');
      const colorIndex = headers.indexOf('color');
      
      if (usernameIndex === -1 || colorIndex === -1) {
        console.warn('Username or Color column not found in users.csv');
        return this.getDefaultUserColor(username);
      }
      
      // Find user row
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.replace(/"/g, ''));
        if (values[usernameIndex] === username.toLowerCase()) {
          const color = values[colorIndex];
          if (color && color.startsWith('#')) {
            return color;
          }
        }
      }
      
      console.warn(`User ${username} not found in users.csv`);
      return this.getDefaultUserColor(username);
    } catch (err) {
      console.warn('Error loading user colors from CSV:', err);
      return this.getDefaultUserColor(username);
    }
  }

  getDefaultUserColor(username) {
    // Fallback colors if CSV is unavailable
    const colors = {
      'pelham': '#ff5f6d',
      'sophia': '#84fab0', 
      'ethan': '#8fd3f4',
      'future': '#ffc371',
      'default': '#a18cd1'
    };
    return colors[username.toLowerCase()] || colors.default;
  }

  render() {
    this.timelineEl = document.querySelector(this.containerId);
    if (!this.timelineEl) {
      throw new Error(`Timeline container not found: ${this.containerId}`);
    }

    if (this.users.length === 0) {
      this.timelineEl.textContent = 'No user data available';
      return;
    }

    // Add multi-user class for proper styling
    this.timelineEl.classList.add('multi-user');

    // Clear timeline
    this.timelineEl.innerHTML = '';

    // Add coverage display at the top
    if (this.masterData && this.masterData.coverage) {
      const coverageEl = document.createElement('div');
      coverageEl.className = 'timeline-coverage';
      coverageEl.style.cssText = `
        text-align: center;
        margin-bottom: 15px;
        padding: 8px;
        font-size: 16px;
        background-color: transparent;
        border-radius: 4px;
      `;
      
      const coverage = this.masterData.coverage;
      coverageEl.innerHTML = `
        <span style="color: white;">Video Coverage: </span>
        <span style="color: #4CAF50; font-weight: bold;">${coverage.coverage_percentage}%</span>
        <span style="color: white; opacity: 0.8; font-size: 14px; margin-left: 10px;">
          (${coverage.video_content_formatted} of ${coverage.show_duration_formatted})
        </span>
      `;
      
      this.timelineEl.appendChild(coverageEl);
    }

    // Compute overall time range across all users
    let allVideos = [];
    this.users.forEach(user => {
      user.videos.forEach(video => {
        allVideos.push({
          ...video,
          username: user.username,
          displayName: user.displayName,
          videoBase: user.videoBase,
          color: user.color
        });
      });
    });

    if (allVideos.length === 0) {
      this.timelineEl.textContent = 'No video data available';
      return;
    }

    const starts = allVideos.map(v => v.mtime);
    const ends = allVideos.map(v => v.mtime + v.duration);
    const minStart = Math.min(...starts);
    const maxEnd = Math.max(...ends);
    const total = maxEnd - minStart;

    // Create user timeline rows
    this.users.forEach((user, userIndex) => {
      if (user.videos.length === 0) return;

      // Create user timeline container
      const userTimeline = document.createElement('div');
      userTimeline.className = 'user-timeline';

      // Add user label (before timeline track)
      const userLabel = document.createElement('div');
      userLabel.className = 'timeline-user-label';
      userLabel.textContent = user.username;
      userLabel.style.color = user.color;
      userTimeline.appendChild(userLabel);

      // Create timeline track for this user
      const timelineTrack = document.createElement('div');
      timelineTrack.className = 'timeline-track';

      // Add segments for this user
      user.videos.forEach((video, videoIndex) => {
        const left = ((video.mtime - minStart) / total) * 100;
        const width = (video.duration / total) * 100;
        const seg = document.createElement('div');
        
        seg.className = 'segment';
        seg.style.left = left + '%';
        seg.style.width = Math.max(width, 0.2) + '%';
        
        // Rainbow coloring by index (original style)
        const grads = ['#ff5f6d', '#ffc371', '#f6d365', '#84fab0', '#8fd3f4', '#a18cd1'];
        seg.style.background = `linear-gradient(90deg,${grads[videoIndex % grads.length]}, rgba(255,255,255,0.06))`;
        
        seg.title = `${user.displayName}: ${video.filename} — ${new Date(video.mtime * 1000).toLocaleString()} (${Math.round(video.duration)}s)`;

        // Store video data on the segment
        seg._videoData = {
          ...video,
          username: user.username,
          displayName: user.displayName,
          videoBase: user.videoBase,
          color: user.color
        };
        seg._userIndex = userIndex;
        seg._videoIndex = videoIndex;

        // Click handler
        seg.onclick = () => {
          this.selectSegment(seg);
          
          if (this.options.onSegmentClick) {
            const videoPath = this.getVideoPath(seg._videoData);
            const displayName = this.getDisplayName(seg._videoData);
            this.options.onSegmentClick(videoPath, displayName, seg, seg._videoData, videoIndex);
          }
        };

        timelineTrack.appendChild(seg);
      });

      userTimeline.appendChild(timelineTrack);
      this.timelineEl.appendChild(userTimeline);
    });

    // Render ticks if selector provided
    if (this.options.ticksSelector) {
      this.renderTicks(minStart, maxEnd);
    }

    console.log(`Multi-user timeline rendered: ${this.users.length} users, ${allVideos.length} total segments`);
  }

  renderTicks(minStart, maxEnd) {
    const ticksEl = document.querySelector(this.options.ticksSelector);
    if (!ticksEl) return;

    ticksEl.innerHTML = '';
    const leftLabel = new Date(minStart * 1000).toLocaleTimeString();
    const rightLabel = new Date(maxEnd * 1000).toLocaleTimeString();
    ticksEl.innerHTML = `<span style="text-align:left">${leftLabel}</span><span style="text-align:right">${rightLabel}</span>`;
  }

  selectSegment(seg) {
    // Clear all previous selections across all user timelines
    const allSegs = this.timelineEl.querySelectorAll('.segment');
    allSegs.forEach(s => {
      s.classList.remove('selected', 'playing');
    });

    this.currentSelectedSeg = seg;
    if (this.currentSelectedSeg) {
      this.currentSelectedSeg.classList.add('selected');
    }
  }

  getVideoPath(videoData) {
    const mp4Candidate = (videoData.videoBase || '') + (videoData.relpath || videoData.filename).replace(/\.mov$/i, '.mp4');
    return encodeURI(mp4Candidate || ((videoData.videoBase || '') + (videoData.relpath || videoData.filename)));
  }

  getDisplayName(videoData) {
    const path = this.getVideoPath(videoData);
    return `${videoData.displayName}: ${decodeURIComponent(path.split('/').pop() || videoData.filename)}`;
  }

  // Get the next segment for sequential playback (across all users, chronologically)
  getNextSegment() {
    if (!this.currentSelectedSeg) return null;
    
    // Get all segments from all user timelines
    const allSegs = Array.from(this.timelineEl.querySelectorAll('.segment'));
    
    // Sort them by time (mtime)
    allSegs.sort((a, b) => a._videoData.mtime - b._videoData.mtime);
    
    const currentIndex = allSegs.indexOf(this.currentSelectedSeg);
    
    if (currentIndex >= 0 && currentIndex < allSegs.length - 1) {
      return allSegs[currentIndex + 1];
    }
    
    return null;
  }

  // Public API for external control
  clearSelection() {
    if (this.currentSelectedSeg) {
      this.currentSelectedSeg.classList.remove('selected');
      this.currentSelectedSeg = null;
    }
  }

  getSelectedSegment() {
    return this.currentSelectedSeg;
  }

  getTotalVideoCount() {
    return this.users.reduce((total, user) => total + user.videos.length, 0);
  }

  getUserCount() {
    return this.users.length;
  }

  // Helper to get video data by user and index
  getVideoByUserAndIndex(username, index) {
    const user = this.users.find(u => u.username === username);
    return user ? (user.videos[index] || null) : null;
  }
}

// Backward compatibility - single user timeline renderer
class TimelineRenderer {
  constructor(containerId, options = {}) {
    this.multiRenderer = new MultiUserTimelineRenderer(containerId, options);
    this.options = options;
    this.vids = [];
    this.videoBase = '';
    this.currentSelectedSeg = null;
    this.timelineEl = null;
    
    console.log('TimelineRenderer (compatibility wrapper) created for:', containerId);
  }

  async loadManifest(manifestPath) {
    console.log('Loading manifest (compatibility mode):', manifestPath);
    try {
      const res = await fetch(encodeURI(manifestPath));
      if (!res.ok) throw new Error(`Manifest not found: ${res.status}`);
      const data = await res.json();
      
      // Check if this is a master manifest (multi-user)
      if (data.users && Array.isArray(data.users)) {
        console.log('Detected master manifest, using MultiUserTimelineRenderer');
        return await this.multiRenderer.loadMasterManifest(manifestPath);
      }
      
      // Single user manifest - create a synthetic master manifest
      console.log('Detected single user manifest, creating synthetic master');
      this.vids = (data.videos || []).filter(v => v.duration != null);
      
      // Set video base directory
      this.videoBase = this.options.videoBase;
      if (!this.videoBase) {
        this.videoBase = manifestPath.replace(/\/index\.json$|\/index.json$/, '/');
        if (!this.videoBase.endsWith('/')) {
          this.videoBase = this.videoBase.replace(/index\.json$/, '');
        }
      }
      
      // Create synthetic master data for single user
      const syntheticMaster = {
        users: [{
          username: 'user',
          displayName: this.options.userDisplayName || 'User',
          manifestPath: manifestPath
        }]
      };
      
      this.multiRenderer.masterData = syntheticMaster;
      this.multiRenderer.users = [{
        username: 'user',
        displayName: this.options.userDisplayName || 'User',
        videos: this.vids,
        videoBase: this.videoBase,
        color: await this.multiRenderer.getUserColor('user')
      }];
      
      console.log(`Timeline loaded (compatibility): ${this.vids.length} videos from ${manifestPath}`);
      return true;
    } catch (err) {
      console.error('Failed to load timeline manifest (compatibility):', err);
      throw err;
    }
  }

  render() {
    this.multiRenderer.render();
    this.timelineEl = this.multiRenderer.timelineEl;
  }

  // Delegate all other methods to the multi-user renderer
  renderTicks(minStart, maxEnd) { return this.multiRenderer.renderTicks(minStart, maxEnd); }
  selectSegment(seg) { return this.multiRenderer.selectSegment(seg); }
  getVideoPath(videoData) { return this.multiRenderer.getVideoPath(videoData); }
  getDisplayName(videoData) { return this.multiRenderer.getDisplayName(videoData); }
  getNextSegment() { return this.multiRenderer.getNextSegment(); }
  clearSelection() { return this.multiRenderer.clearSelection(); }
  getSelectedSegment() { return this.multiRenderer.getSelectedSegment(); }
  getVideoCount() { return this.multiRenderer.getTotalVideoCount(); }
  getVideoByIndex(index) { 
    // For backward compatibility, get videos from first user
    const user = this.multiRenderer.users[0];
    return user ? (user.videos[index] || null) : null;
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TimelineRenderer, MultiUserTimelineRenderer };
}