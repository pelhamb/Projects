// Shared timeline + inline player code extracted from Chris Stussy page.
// Usage: initConcertPage(manifestPath, opts)

function initConcertPage(manifestPath, opts = {}){
  const timelineSelector = opts.timelineSelector || '#timeline';
  const ticksSelector = opts.ticksSelector || '#timeline-ticks';
  const inlinePlayerSelector = opts.inlinePlayerSelector || '#inline-player';
  const playerSelector = opts.playerSelector || '#concert-video';
  const playerNoteSelector = opts.playerNoteSelector || '#player-note';

  let timeline = null;
  let player = null;
  let backgroundPlayer = null; // For seamless cutover
  let playerNote = null;
  let playBtn = null;
  let cutoverTimer = null;

  async function draw(){
    try{
      console.log('Concert player starting, manifestPath:', manifestPath);
      
      const res = await fetch(encodeURI(manifestPath));
      if(!res.ok) throw new Error('Manifest not found');
      const data = await res.json();
      
      // Get DOM elements
      player = document.querySelector(playerSelector);
      playerNote = document.querySelector(playerNoteSelector);
      if(!player) throw new Error('Player element not found: ' + playerSelector);
      if(!playerNote) throw new Error('Player note element not found: ' + playerNoteSelector);

      // Create background video element for seamless cutover
      backgroundPlayer = document.createElement('video');
      backgroundPlayer.style.display = 'none';
      backgroundPlayer.preload = 'metadata';
      backgroundPlayer.muted = true; // Start muted to avoid audio conflicts
      player.parentNode.appendChild(backgroundPlayer);

      // Prepare player early so click handlers can call play() synchronously
      player.style.width = '100%';
      player.style.height = '100%';

      // Check if TimelineRenderer is available
      if (typeof TimelineRenderer === 'undefined') {
        throw new Error('TimelineRenderer class not found - make sure timeline-renderer.js is loaded first');
      }

      // For master manifests, use the TimelineRenderer (which now auto-detects and uses multi-user)
      if(data.users && Array.isArray(data.users)) {
        console.log('Master manifest detected, creating multi-user timeline for users:', data.users.map(u => u.username));
      } else {
        console.log('Individual user manifest detected, using single-user timeline');
      }
      
      // Create timeline renderer (it will auto-detect single vs multi-user)
      timeline = new TimelineRenderer(timelineSelector, {
        ticksSelector: ticksSelector,
        onSegmentClick: handleSegmentClick
      });

      // Load and render timeline
      await timeline.loadManifest(manifestPath);
      timeline.render();

      if(timeline.getVideoCount() === 0) {
        const timelineEl = document.querySelector(timelineSelector);
        if(timelineEl) timelineEl.textContent = 'No duration data found. Run the generator script.';
        return;
      }

      console.log(`Timeline loaded: ${timeline.getUserCount ? timeline.getUserCount() : 1} users, ${timeline.getVideoCount()} total videos`);

      // Setup player components
      setupPlayer();
      setupPlayerEvents();

    }catch(err){
      console.error('Concert player error:', err);
      const timelineEl = document.querySelector(timelineSelector);
      if(timelineEl) timelineEl.textContent = 'Timeline not available: ' + (err && err.message ? err.message : String(err));
      else console.error('Timeline initialization failed', err);
    }
  }

  function handleSegmentClick(videoPath, displayName, segmentEl, videoData, videoIndex) {
    console.log('Segment clicked', { videoPath, displayName, videoIndex });
    setSrcAndPlay(videoPath, displayName, segmentEl);
  }

  function setupPlayer() {
    // Create play control button (for when autoplay is blocked)
    playBtn = document.createElement('button');
    playBtn.textContent = 'Play';
    playBtn.style.display = 'none';
    playBtn.style.marginTop = '8px';
    playBtn.onclick = () => {
      console.log('Play button clicked');
      // If no src is currently loaded, instruct the user to select a clip first.
      if(!player.currentSrc){
        console.log('Play button pressed but no source loaded');
        playerNote.innerHTML = 'Select a clip from the timeline first, then press Play if needed.';
        return;
      }
      console.log('Calling play() from Play button for', player.currentSrc);
      const p = player.play();
      if(p && p.then){
        p.then(()=>console.log('play() resolved from playBtn')).catch(err=>{
          console.warn('play() rejected from playBtn', err);
          playerNote.innerHTML = `Playback failed to start: ${err?.message || err}. Try downloading the file.`;
        });
      }
    };
    if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
  }

  function setupPlayerEvents() {
    // Instrument player events for debugging
    ['loadedmetadata','loadeddata','canplay','canplaythrough','playing','pause','stalled','waiting','ended'].forEach(ev=>{
      player.addEventListener(ev, (e)=>{
        console.log('video event', ev, 'readyState', player.readyState, 'networkState', player.networkState, 'currentSrc', player.currentSrc, 'videoSize', player.videoWidth, player.videoHeight);
      });
    });

    // Global error handler for the player
    function onErrorGlobal(ev){
      const err = player.error;
      console.warn('Video error (global)', err, 'readyState', player.readyState, 'networkState', player.networkState, 'currentSrc', player.currentSrc);
      let msg = 'Playback failed.';
      if(err){
        const code = err.code;
        const codes = {
          1: 'MEDIA_ERR_ABORTED',
          2: 'MEDIA_ERR_NETWORK',
          3: 'MEDIA_ERR_DECODE',
          4: 'MEDIA_ERR_SRC_NOT_SUPPORTED'
        };
        msg += ` (${codes[code] || ('code:'+code)})`;
      }
      msg += `<br>readyState=${player.readyState} networkState=${player.networkState}`;
      msg += `<br>Video dimensions: ${player.videoWidth}x${player.videoHeight}`;
      msg += `<br>You can <a href="${player.currentSrc}" download>download the file</a> and open it in VLC/QuickTime.`;
      playerNote.innerHTML = msg;
      if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
      playBtn.style.display = 'inline-block';
    }
    player.removeEventListener('error', onErrorGlobal);
    player.addEventListener('error', onErrorGlobal);

    // Auto-play next video when current one ends
    player.addEventListener('ended', ()=>{
      const nextSeg = timeline.getNextSegment();
      if(nextSeg) {
        console.log('Auto-playing next segment:', nextSeg.title);
        
        // Get video data from the segment
        const videoData = nextSeg._videoData;
        const videoIndex = nextSeg._videoIndex;
        
        if(videoData) {
          const videoPath = timeline.getVideoPath(videoData);
          const displayName = timeline.getDisplayName(videoData);
          
          // Select the next segment
          timeline.selectSegment(nextSeg);
          
          console.log('Loading next video:', { videoPath, displayName });
          setSrcAndPlay(videoPath, displayName, nextSeg);
        }
      } else {
        // No more segments, clear selection
        console.log('Reached end of playlist');
        timeline.clearSelection();
        playerNote.textContent = 'Playlist completed';
      }
    });
  }

  function setSrcAndPlay(preferred, displayName, seg){
    console.log('setSrcAndPlay', preferred, displayName);
    try{
      player.pause();
      player.removeAttribute('src');
      player.src = preferred;
      player.load();
      console.log('Before play(): readyState=', player.readyState, 'networkState=', player.networkState, 'currentSrc=', player.currentSrc);
      const playPromise = player.play();

      // detect stalled play attempts: if there's no 'playing' event within
      // a short timeout, show the Play button and a helpful message.
      let playStallTimer = null;
      const stallTimeoutMs = 3000;
      const clearStall = ()=>{ if(playStallTimer){ clearTimeout(playStallTimer); playStallTimer = null; } };

      if(!playPromise){
        console.log('player.play() did not return a promise (legacy browser). Assuming playing state.');
        playerNote.textContent = `Playing ${displayName}`;
        return;
      }

      playStallTimer = setTimeout(()=>{
        console.warn('play() appears stalled (no playing event within timeout)');
        playerNote.innerHTML = `Playback did not start automatically. Press Play to try again or <a href="${preferred}" download>download</a>.`;
        if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
        playBtn.style.display = 'inline-block';
      }, stallTimeoutMs);

      playPromise.then(()=>{
        console.log('player.play() resolved (setSrcAndPlay)');
        clearStall();
        playerNote.textContent = `Playing ${displayName}`;
      }).catch(err=>{
        console.warn('player.play() rejected (setSrcAndPlay)', err);
        clearStall();
        playerNote.innerHTML = `Playback requires user interaction. Press Play to start or <a href="${preferred}" download>download</a>.`;
        if(typeof playBtn !== 'undefined' && playBtn && !playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
        if(typeof playBtn !== 'undefined' && playBtn) playBtn.style.display = 'inline-block';
      });

      player.addEventListener('playing', ()=>{ clearStall(); });
    }catch(e){
      console.warn('Autoplay failed or playback error', e);
      playerNote.innerHTML = `Playback requires user interaction. Press Play to start or <a href="${preferred}" download>download</a>.`;
      if(typeof playBtn !== 'undefined' && playBtn && !playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
      if(typeof playBtn !== 'undefined' && playBtn) playBtn.style.display = 'inline-block';
    }
  }

  // start drawing
  draw();
  // return a small API for tests or manual redraw
  return { draw, timeline };
}