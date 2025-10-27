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
  let playerNote = null;
  let playBtn = null;

  async function draw(){
    try{
      console.log('Concert player starting, manifestPath:', manifestPath);
      
      const res = await fetch(encodeURI(manifestPath));
      if(!res.ok) throw new Error('Manifest not found');
      const data = await res.json();
      
      let pelhamManifestPath;
      
      // Check if this is a master manifest (has 'users' property) or individual user manifest
      if(data.users && Array.isArray(data.users)) {
        console.log('Master manifest detected with users:', data.users.map(u => u.username));
        
        // For now, default to pelham's timeline (backward compatibility)
        const pelhamUser = data.users.find(u => u.username === 'pelham');
        if(!pelhamUser) {
          throw new Error('Pelham user not found in master manifest');
        }
        
        console.log('Loading pelham user timeline:', pelhamUser.manifestPath);
        
        // Construct the full path to pelham's manifest
        const manifestDir = manifestPath.substring(0, manifestPath.lastIndexOf('/') + 1);
        pelhamManifestPath = manifestDir + pelhamUser.manifestPath.replace('./', '');
        
        console.log('Master manifest directory:', manifestDir);
        console.log('Pelham manifest path:', pelhamManifestPath);
        
      } else {
        // This is an individual user manifest (original behavior)
        console.log('Individual user manifest detected');
        pelhamManifestPath = manifestPath;
      }
      
      // Get DOM elements
      player = document.querySelector(playerSelector);
      playerNote = document.querySelector(playerNoteSelector);
      if(!player) throw new Error('Player element not found: ' + playerSelector);
      if(!playerNote) throw new Error('Player note element not found: ' + playerNoteSelector);

      // Prepare player early so click handlers can call play() synchronously
      player.style.width = '100%';
      player.style.height = '100%';

      // Check if TimelineRenderer is available
      if (typeof TimelineRenderer === 'undefined') {
        throw new Error('TimelineRenderer class not found - make sure timeline-renderer.js is loaded first');
      }

      // Create timeline renderer
      console.log('Creating TimelineRenderer...');
      timeline = new TimelineRenderer(timelineSelector, {
        ticksSelector: ticksSelector,
        onSegmentClick: handleSegmentClick
      });

      // Load and render timeline
      console.log('Loading timeline manifest...');
      await timeline.loadManifest(pelhamManifestPath);
      
      console.log('Rendering timeline...');
      timeline.render();

      if(timeline.getVideoCount() === 0) {
        const timelineEl = document.querySelector(timelineSelector);
        if(timelineEl) timelineEl.textContent = 'No duration data found. Run the generator script.';
        return;
      }

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

      vids.forEach((v, i)=>{
        const left = ((v.mtime - minStart) / total) * 100;
        const width = (v.duration / total) * 100;
        const seg = document.createElement('div');
        seg.className='segment';
        seg.style.left = left + '%';
        seg.style.width = Math.max(width, 0.2) + '%';
        // rainbow coloring by index
        const grads = ['#ff5f6d','#ffc371','#f6d365','#84fab0','#8fd3f4','#a18cd1'];
        seg.style.background = 'linear-gradient(90deg,'+grads[i%grads.length]+', rgba(255,255,255,0.06))';
        seg.title = `${v.filename} — ${new Date(v.mtime*1000).toLocaleString()} (${Math.round(v.duration)}s)`;

        // prefer MP4 sibling immediately to preserve user gesture for play()
        const mp4Candidate = (videoBase || '') + (v.relpath || v.filename).replace(/\.mov$/i, '.mp4');
        seg.onclick = ()=>{
          selectSegment(seg);
          const preferred = encodeURI(mp4Candidate || ((videoBase||'') + (v.relpath || v.filename)));
          const displayName = decodeURIComponent(preferred.split('/').pop() || v.filename);
          console.log('Segment clicked', { preferred, displayName, title: seg.title });
          setSrcAndPlay(preferred, displayName, seg);
        };
        timelineEl.appendChild(seg);
      });

      // instrument player events for debugging (exclude 'error' here; attach a
      // dedicated global error handler below so clicks that call setSrcAndPlay
      // surface a helpful UI message)
      ['loadedmetadata','loadeddata','canplay','canplaythrough','playing','pause','stalled','waiting','ended'].forEach(ev=>{
        player.addEventListener(ev, (e)=>{
          console.log('video event', ev, 'readyState', player.readyState, 'networkState', player.networkState, 'currentSrc', player.currentSrc, 'videoSize', player.videoWidth, player.videoHeight);
        });
      });

      // Global error handler for the player. This ensures any errors that occur
      // when we call setSrcAndPlay are shown to the user and the Play button is
      // made visible.
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

      async function loadIntoPlayer(url, filename, mp4Candidate){
        let displayName = decodeURIComponent((url || '').split('/').pop() || filename);
        playerNote.innerHTML = `Loaded ${displayName}. Attempting playback...`;
        if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
        playBtn.style.display = 'none';

        let preferred = url;
        if(mp4Candidate){
          preferred = mp4Candidate;
          displayName = decodeURIComponent(preferred.split('/').pop() || filename);
          playerNote.textContent = `Loaded ${displayName}. Attempting playback...`;
        } else {
          try{
            const lower = url.toLowerCase();
            if(lower.endsWith('.mov')){
              const mp4 = url.slice(0, -4) + '.mp4';
              const h = await fetch(mp4, { method: 'HEAD' });
              if(h.ok){ preferred = mp4; displayName = decodeURIComponent(preferred.split('/').pop() || filename); }
            }
          }catch(e){ /* ignore */ }
        }

        player.pause();
        player.removeAttribute('src');
        console.log('Setting player.src =', preferred);
        player.src = preferred;
        player.load();

        const onError = (ev)=>{
          const err = player.error;
          console.warn('Video error', err, 'readyState', player.readyState, 'networkState', player.networkState);
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
          msg += `<br>You can <a href="${preferred}" download>download the file</a> and open it in VLC/QuickTime.`;
          msg += `<br><br>If you see errors referencing a browser extension (background.js) try disabling extensions or open the page in an Incognito window to rule out extension interference.`;
          playerNote.innerHTML = msg;
          if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
          playBtn.style.display = 'inline-block';
        };
        player.removeEventListener('error', onError);
        player.addEventListener('error', onError);

        try{
          const playPromise = player.play();
          if(playPromise && playPromise.then){
            playPromise.then(()=>{
              console.log('player.play() resolved');
              playerNote.textContent = `Playing ${displayName}`;
              if(!currentSelectedSeg){
                const segs = Array.from(timelineEl.querySelectorAll('.segment'));
                const match = segs.find(s=>s.title && s.title.indexOf(displayName)!==-1);
                if(match) selectSegment(match);
              }
            }).catch(err=>{
              console.warn('player.play() rejected', err);
              playerNote.innerHTML = `Playback requires user interaction. Press Play to start or <a href="${preferred}" download>download</a>.`;
              if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
              playBtn.style.display = 'inline-block';
            });
          } else {
            playerNote.textContent = `Playing ${displayName}`;
          }
        }catch(e){
          console.warn('Autoplay failed or playback error', e);
          playerNote.innerHTML = `Playback requires user interaction. Press Play to start or <a href="${preferred}" download>download</a>.`;
          if(!playerNote.contains(playBtn)) playerNote.appendChild(playBtn);
          playBtn.style.display = 'inline-block';
        }
      }

      // Auto-play next video when current one ends
      player.addEventListener('ended', ()=>{
        if(currentSelectedSeg) {
          // Find all segments and get the current one's index
          const allSegs = Array.from(timelineEl.querySelectorAll('.segment'));
          const currentIndex = allSegs.indexOf(currentSelectedSeg);
          
          // Check if there's a next segment
          if(currentIndex >= 0 && currentIndex < allSegs.length - 1) {
            const nextSeg = allSegs[currentIndex + 1];
            console.log('Auto-playing next segment:', nextSeg.title);
            
            // Select the next segment
            selectSegment(nextSeg);
            
            // Get the video data for the next segment
            const nextVideo = vids[currentIndex + 1];
            if(nextVideo) {
              const mp4Candidate = (videoBase || '') + (nextVideo.relpath || nextVideo.filename).replace(/\.mov$/i, '.mp4');
              const preferred = encodeURI(mp4Candidate || ((videoBase||'') + (nextVideo.relpath || nextVideo.filename)));
              const displayName = decodeURIComponent(preferred.split('/').pop() || nextVideo.filename);
              
              console.log('Loading next video:', { preferred, displayName });
              setSrcAndPlay(preferred, displayName, nextSeg);
            }
          } else {
            // No more segments, clear selection
            console.log('Reached end of playlist');
            currentSelectedSeg.classList.remove('selected');
            currentSelectedSeg = null;
            playerNote.textContent = 'Playlist completed';
          }
        }
      });

      // Since we're combining selected/playing states, no need for separate playing class
      // The selected class will handle both visual states

      // ticks
      if(ticksEl){
        ticksEl.innerHTML = '';
        const leftLabel = new Date(minStart*1000).toLocaleTimeString();
        const rightLabel = new Date(maxEnd*1000).toLocaleTimeString();
        ticksEl.innerHTML = `<span style="text-align:left">${leftLabel}</span><span style="text-align:right">${rightLabel}</span>`;
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
