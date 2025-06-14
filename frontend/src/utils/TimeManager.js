/**
 * TimeManager - Manages time-based calculations for natal and transit charts
 * Supports real-time updates, animation, and custom date selection
 */
class TimeManager {
  constructor() {
    this.currentTime = new Date();
    this.natalTime = null;
    this.timeZone = null;
    this.coordinates = null;
    this.listeners = new Set();
      // Animation system
    this.isAnimating = false;
    this.animationSpeed = 1; // Days per second (default: 1 day)
    this.animationDirection = 1; // 1 for forward, -1 for backward
    this.animationInterval = null;
    this.lastAnimationTime = Date.now();
      // Buffering system for smooth animation
    this.isBuffering = false;
    this.bufferFrames = [];
    this.bufferFrameCount = 48; // Default: 48 frames for 1 day at 30-minute intervals
    this.bufferFrameInterval = 30; // 30 minutes per frame
    this.bufferProgress = 0;
    this.currentFrameIndex = 0;
    this.playbackFPS = 2; // 2 frames per second (0.5 seconds per frame)
    this.loopPlayback = true;// Time range for slider
    this.timeRange = {
      start: new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000), // 2 years ago
      end: new Date(Date.now() + 2 * 365 * 24 * 60 * 60 * 1000)    // 2 years ahead
    };
  }

  /**
   * Set natal birth time and location
   * @param {Object} birthData - Birth information
   */
  setNatalTime(birthData) {
    this.natalTime = {
      date: birthData.birth_date,
      time: birthData.birth_time,
      timezone: birthData.timezone,
      coordinates: birthData.coordinates
    };
    
    this.timeZone = birthData.timezone;
    this.coordinates = birthData.coordinates;
    
    this.notifyListeners('natalTimeSet', this.natalTime);
    return this;
  }

  /**
   * Set current time for transit calculations
   * @param {Date|string} time - Time to set (defaults to now)
   */
  setCurrentTime(time = new Date()) {
    this.currentTime = new Date(time);
    this.notifyListeners('currentTimeChanged', this.currentTime);
    return this;
  }

  /**
   * Get current time for transit calculations
   */
  getCurrentTime() {
    return this.currentTime;
  }

  /**
   * Get natal time information
   */
  getNatalTime() {
    return this.natalTime;
  }

  /**
   * Format time for API calls
   * @param {Date} date - Date to format
   */
  formatForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return {
      year,
      month: parseInt(month),
      day: parseInt(day),
      hour: parseInt(hours),
      minute: parseInt(minutes),
      birth_date: `${year}-${month}-${day}`,
      birth_time: `${hours}:${minutes}`
    };
  }

  /**
   * Get transit parameters for API calls
   */
  getTransitParams() {
    if (!this.coordinates || !this.timeZone) {
      throw new Error('Natal time and coordinates must be set before generating transits');
    }

    const timeData = this.formatForAPI(this.currentTime);
    
    return {
      ...timeData,
      timezone: this.timeZone,
      coordinates: this.coordinates
    };
  }

  /**
   * Get natal parameters for API calls
   */
  getNatalParams() {
    if (!this.natalTime) {
      throw new Error('Natal time must be set first');
    }

    return {
      birth_date: this.natalTime.date,
      birth_time: this.natalTime.time,
      timezone: this.natalTime.timezone,
      coordinates: this.natalTime.coordinates
    };
  }

  /**
   * Calculate time difference between natal and current time
   */
  getTimeDifference() {
    if (!this.natalTime) return null;

    const natalDate = new Date(`${this.natalTime.date}T${this.natalTime.time}`);
    const diffMs = this.currentTime.getTime() - natalDate.getTime();
    
    const years = diffMs / (1000 * 60 * 60 * 24 * 365.25);
    const days = diffMs / (1000 * 60 * 60 * 24);
    const hours = diffMs / (1000 * 60 * 60);
    
    return {
      milliseconds: diffMs,
      hours: Math.round(hours),
      days: Math.round(days),
      years: parseFloat(years.toFixed(2))
    };
  }

  /**
   * Advance time by specified amount (for future timelapse)
   * @param {Object} duration - Duration to advance { days?, hours?, minutes? }
   */
  advanceTime(duration) {
    const newTime = new Date(this.currentTime);
    
    if (duration.days) newTime.setDate(newTime.getDate() + duration.days);
    if (duration.hours) newTime.setHours(newTime.getHours() + duration.hours);
    if (duration.minutes) newTime.setMinutes(newTime.getMinutes() + duration.minutes);
    
    this.setCurrentTime(newTime);
    return this;
  }

  /**
   * Set time to specific offset from natal time (for future timelapse)
   * @param {Object} offset - Offset from natal time { years?, days?, hours? }
   */
  setTimeOffset(offset) {
    if (!this.natalTime) {
      throw new Error('Natal time must be set before setting offset');
    }

    const natalDate = new Date(`${this.natalTime.date}T${this.natalTime.time}`);
    const newTime = new Date(natalDate);
    
    if (offset.years) newTime.setFullYear(newTime.getFullYear() + offset.years);
    if (offset.days) newTime.setDate(newTime.getDate() + offset.days);
    if (offset.hours) newTime.setHours(newTime.getHours() + offset.hours);
    
    this.setCurrentTime(newTime);
    return this;
  }

  /**
   * Reset current time to now
   */
  resetToNow() {
    this.setCurrentTime(new Date());
    return this;
  }

  /**
   * Add event listener for time changes
   * @param {Function} callback - Callback function
   */
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Notify all listeners of changes
   * @param {string} event - Event type
   * @param {Object} data - Event data
   */
  notifyListeners(event, data) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('TimeManager listener error:', error);
      }
    });
  }
  /**
   * Get formatted display strings for UI
   */
  getDisplayInfo() {
    const timeDiff = this.getTimeDifference();
    
    return {
      currentTime: this.currentTime.toLocaleString(),
      natalTime: this.natalTime ? 
        `${this.natalTime.date} ${this.natalTime.time}` : 
        'Not set',
      timeDifference: timeDiff ? 
        `${timeDiff.years} years (${timeDiff.days} days)` : 
        'N/A',
      isAnimating: this.isAnimating,
      animationSpeed: this.animationSpeed,
      animationDirection: this.animationDirection,
      sliderPosition: this.getSliderPosition()
    };
  }

  /**
   * Check if ready for transit calculations
   */
  isReadyForTransits() {
    return !!(this.natalTime && this.coordinates && this.timeZone);
  }

  /**
   * Animation Controls
   */
    /**
   * Start animating time progression using buffered frames
   * @param {number} speed - Days per second (default: 1)
   * @param {number} direction - 1 for forward, -1 for backward
   */
  startAnimation(speed = 1, direction = 1) {
    // Use frame-based animation if we have buffered frames
    if (this.bufferedFrames && this.bufferedFrames.length > 0) {
      this.startFrameBasedAnimation(speed, direction);
      return;
    }
    
    // Fall back to real-time animation
    if (this.isAnimating) {
      this.stopAnimation();
    }
    
    this.isAnimating = true;
    this.animationSpeed = speed;
    this.animationDirection = direction;
    this.lastAnimationTime = Date.now();
    
    this.animationInterval = setInterval(() => {
      const now = Date.now();
      const deltaMs = now - this.lastAnimationTime;
      this.lastAnimationTime = now;
      
      // Convert speed (days/second) to milliseconds per frame
      const daysToAdvance = (deltaMs / 1000) * this.animationSpeed * this.animationDirection;
      const msToAdvance = daysToAdvance * 24 * 60 * 60 * 1000;
      
      const newTime = new Date(this.currentTime.getTime() + msToAdvance);
      
      // Check bounds
      if (newTime >= this.timeRange.start && newTime <= this.timeRange.end) {
        this.setCurrentTime(newTime);
      } else {
        this.stopAnimation();
      }
    }, 50); // 20 FPS for smooth animation
    
    this.notifyListeners('animationStarted', { speed, direction });
  }
  
  /**
   * Stop time animation
   */
  stopAnimation() {
    if (this.animationInterval) {
      clearInterval(this.animationInterval);
      this.animationInterval = null;
    }
    this.isAnimating = false;
    this.notifyListeners('animationStopped', {});
  }
  
  /**
   * Toggle animation play/pause
   */
  toggleAnimation() {
    if (this.isAnimating) {
      this.stopAnimation();
    } else {
      this.startAnimation(this.animationSpeed, this.animationDirection);
    }
  }
    /**
   * Set animation speed and update frame count accordingly
   * @param {number} speed - Animation speed (0.25 = 6hrs, 0.5 = 12hrs, 1 = 1day)
   */
  setAnimationSpeed(speed) {
    this.animationSpeed = speed;
    // Update frame count based on speed (30-min intervals)
    // 1 day = 48 frames, 12 hours = 24 frames, 6 hours = 12 frames
    this.bufferFrameCount = Math.round(speed * 48);
    console.log(`Animation speed set to ${speed} (${this.bufferFrameCount} frames)`);
    if (this.isAnimating) {
      this.startAnimation(speed, this.animationDirection);
    }
  }
  
  /**
   * Set animation direction
   * @param {number} direction - 1 for forward, -1 for backward
   */
  setAnimationDirection(direction) {
    this.animationDirection = direction;
    if (this.isAnimating) {
      this.startAnimation(this.animationSpeed, direction);
    }
  }
  
  /**
   * Time Range and Slider Controls
   */
  
  /**
   * Set the time range for the slider
   * @param {Date} start - Start date
   * @param {Date} end - End date
   */
  setTimeRange(start, end) {
    this.timeRange = { start: new Date(start), end: new Date(end) };
    
    // Clamp current time to new range
    if (this.currentTime < this.timeRange.start) {
      this.setCurrentTime(this.timeRange.start);
    } else if (this.currentTime > this.timeRange.end) {
      this.setCurrentTime(this.timeRange.end);
    }
    
    this.notifyListeners('timeRangeChanged', this.timeRange);
  }
  
  /**
   * Get time range
   */
  getTimeRange() {
    return { ...this.timeRange };
  }
  
  /**
   * Set time by slider position (0-1)
   * @param {number} position - Position between 0 and 1
   */
  setTimeBySliderPosition(position) {
    const { start, end } = this.timeRange;
    const totalMs = end.getTime() - start.getTime();
    const targetTime = new Date(start.getTime() + (totalMs * position));
    this.setCurrentTime(targetTime);
  }
  
  /**
   * Get current slider position (0-1)
   */
  getSliderPosition() {
    const { start, end } = this.timeRange;
    const totalMs = end.getTime() - start.getTime();
    const currentMs = this.currentTime.getTime() - start.getTime();
    return Math.max(0, Math.min(1, currentMs / totalMs));
  }
  
  /**
   * Jump to specific time offsets
   */
  jumpToNow() {
    this.setCurrentTime(new Date());
  }
  
  jumpToOffset(days) {
    const targetTime = new Date(Date.now() + (days * 24 * 60 * 60 * 1000));
    this.setCurrentTime(targetTime);
  }
  
  jumpRelative(days) {
    const targetTime = new Date(this.currentTime.getTime() + (days * 24 * 60 * 60 * 1000));
    this.setCurrentTime(targetTime);
  }
    /**
   * Buffering System for Smooth Animation
   * Uses fixed frame count (50) with variable time intervals based on speed
   */
  
  /**
   * Pre-calculate transit data for smooth animation with fixed frame count
   * @param {number} animationSpeed - Days per second for animation
   * @param {number} frameCount - Number of frames to buffer (default: 50)
   * @param {Function} calculationCallback - Function to calculate transits for a given time
   */
  async bufferTransitData(animationSpeed = 1, frameCount = 50, calculationCallback) {
    this.isBuffering = true;
    this.bufferProgress = 0;
    this.transitBuffer = new Map();
    this.bufferedFrames = [];
    
    // Calculate time interval between frames based on animation speed
    // For 50 frames at 20 FPS = 2.5 seconds of animation
    const animationDurationSeconds = 2.5;
    const totalTimeSpan = animationSpeed * animationDurationSeconds; // Days to cover
    const timeIntervalDays = totalTimeSpan / frameCount;
    const timeIntervalMs = timeIntervalDays * 24 * 60 * 60 * 1000;
    
    const startTime = this.currentTime.getTime();
    
    this.notifyListeners('bufferingStarted', { 
      frameCount, 
      animationSpeed, 
      timeIntervalDays,
      totalTimeSpan
    });
    
    try {
      for (let i = 0; i < frameCount; i++) {
        const timeMs = startTime + (i * timeIntervalMs);
        const bufferTime = new Date(timeMs);
        
        // Calculate transit data for this time point
        console.log(`Buffering frame ${i + 1}/${frameCount} for time:`, bufferTime.toISOString());
        const transitData = await calculationCallback(bufferTime);
        
        // Store in buffer with timestamp as key
        this.transitBuffer.set(timeMs, transitData);
        this.bufferedFrames.push({
          time: timeMs,
          data: transitData
        });
        
        // Update progress
        this.bufferProgress = ((i + 1) / frameCount) * 100;
        this.notifyListeners('bufferingProgress', { 
          progress: this.bufferProgress, 
          currentFrame: i + 1, 
          frameCount,
          currentTime: bufferTime
        });
        
        // Small delay to prevent overwhelming the backend
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      this.isBuffering = false;
      this.bufferProgress = 100;
      this.notifyListeners('bufferingComplete', { 
        bufferSize: this.transitBuffer.size,
        frameCount: this.bufferedFrames.length,
        timeSpan: totalTimeSpan
      });
      
    } catch (error) {
      this.isBuffering = false;
      this.notifyListeners('bufferingError', { error });
      throw error;
    }
  }
  
  /**
   * Start frame-based animation using buffered data
   * @param {number} speed - Days per second (used to determine frame timing)
   * @param {number} direction - 1 for forward, -1 for backward
   */
  startFrameBasedAnimation(speed = 1, direction = 1) {
    if (this.isAnimating) {
      this.stopAnimation();
    }
    
    if (!this.bufferedFrames || this.bufferedFrames.length === 0) {
      console.warn('No buffered frames available for animation');
      return;
    }
    
    this.isAnimating = true;
    this.animationSpeed = speed;
    this.animationDirection = direction;
    this.currentFrameIndex = direction === 1 ? 0 : this.bufferedFrames.length - 1;
    
    // Calculate frame rate: 50 frames over 2.5 seconds = 20 FPS
    const frameRate = 20; // FPS
    const frameInterval = 1000 / frameRate; // ms between frames
    
    this.animationInterval = setInterval(() => {
      if (this.currentFrameIndex < 0 || this.currentFrameIndex >= this.bufferedFrames.length) {
        this.stopAnimation();
        return;
      }
      
      const frame = this.bufferedFrames[this.currentFrameIndex];
      const frameTime = new Date(frame.time);
      
      // Update current time and notify listeners
      this.currentTime = frameTime;
      this.notifyListeners('currentTimeChanged', frameTime);
      this.notifyListeners('frameDataUpdate', frame.data);
      
      // Move to next frame
      this.currentFrameIndex += direction;
      
    }, frameInterval);
    
    this.notifyListeners('animationStarted', { speed, direction, frameCount: this.bufferedFrames.length });
  }
  
  /**
   * Get buffered transit data for a specific time (with interpolation)
   * @param {Date} time - Target time
   * @returns {Object|null} Transit data or null if not buffered
   */
  getBufferedTransitData(time) {
    if (!this.transitBuffer || this.transitBuffer.size === 0) {
      return null;
    }
    
    const targetMs = time.getTime();
    const bufferTimes = Array.from(this.transitBuffer.keys()).sort((a, b) => a - b);
    
    // Find exact match first
    if (this.transitBuffer.has(targetMs)) {
      return this.transitBuffer.get(targetMs);
    }
    
    // Find closest buffered time
    let closestTime = bufferTimes[0];
    let minDiff = Math.abs(targetMs - closestTime);
    
    for (const bufferTime of bufferTimes) {
      const diff = Math.abs(targetMs - bufferTime);
      if (diff < minDiff) {
        minDiff = diff;
        closestTime = bufferTime;
      }
    }
    
    // Return data if within reasonable range (30 minutes)
    if (minDiff <= 30 * 60 * 1000) {
      return this.transitBuffer.get(closestTime);
    }
    
    return null;
  }
    /**
   * Clear buffered data
   */
  clearBuffer() {
    this.transitBuffer = new Map();
    this.bufferFrames = [];
    this.currentFrameIndex = 0;
    this.bufferProgress = 0;
    this.isBuffering = false;
    this.notifyListeners('bufferCleared', {});
  }
  
  /**
   * Check if currently buffering
   */
  isCurrentlyBuffering() {
    return this.isBuffering || false;
  }
    /**
   * Get buffer status
   */
  getBufferStatus() {
    return {
      isBuffering: this.isBuffering || false,
      progress: this.bufferProgress || 0,
      bufferSize: this.transitBuffer ? this.transitBuffer.size : 0,
      frameCount: this.bufferFrameCount,
      currentFrame: this.currentFrameIndex
    };
  }
  /**
   * Buffer animation frames for smooth playback
   * @param {Function} transitGeneratorCallback - Function to generate transit data for a given time
   */
  async bufferAnimationFrames(transitGeneratorCallback) {
    if (this.isBuffering) return;
    
    this.isBuffering = true;
    this.bufferFrames = [];
    this.bufferProgress = 0;
    this.currentFrameIndex = 0;
    
    // Calculate frame count based on animation speed
    // animationSpeed = 1 (1 day) = 48 frames
    // animationSpeed = 0.5 (12 hours) = 24 frames  
    // animationSpeed = 0.25 (6 hours) = 12 frames
    const totalFrames = Math.round(this.animationSpeed * this.bufferFrameCount);
    
    this.notifyListeners('bufferingStarted', {
      frameCount: totalFrames,
      duration: this.animationSpeed * 24 * 60 // duration in minutes
    });
    
    try {
      const startTime = new Date(this.currentTime);
      
      for (let i = 0; i < totalFrames; i++) {
        // Calculate time for this frame (30-minute intervals)
        const frameTime = new Date(startTime.getTime() + (i * this.bufferFrameInterval * 60 * 1000));
        
        // Generate transit data for this frame
        const frameData = await transitGeneratorCallback(frameTime);
        
        this.bufferFrames.push({
          time: frameTime,
          data: frameData
        });
        
        // Update progress
        this.bufferProgress = ((i + 1) / totalFrames) * 100;
        this.notifyListeners('bufferingProgress', {
          progress: this.bufferProgress,
          currentFrame: i + 1,
          frameCount: totalFrames,
          frameTime: frameTime
        });
      }
      
      this.isBuffering = false;
      this.notifyListeners('bufferingComplete', {
        frameCount: this.bufferFrames.length
      });
      
    } catch (error) {
      this.isBuffering = false;
      this.notifyListeners('bufferingError', { error });
      throw error;
    }
  }

  /**
   * Start buffered animation playback
   */
  startBufferedAnimation() {
    if (this.bufferFrames.length === 0) {
      throw new Error('No buffered frames available. Call bufferAnimationFrames() first.');
    }
    
    if (this.isAnimating) {
      this.stopAnimation();
    }
    
    this.isAnimating = true;
    this.currentFrameIndex = 0;
    this.notifyListeners('animationStarted', {
      mode: 'buffered',
      frameCount: this.bufferFrames.length,
      fps: this.playbackFPS
    });
    
    // Start playback loop
    this.animationInterval = setInterval(() => {
      if (!this.isAnimating || this.bufferFrames.length === 0) {
        this.stopAnimation();
        return;
      }
      
      // Get current frame
      const frame = this.bufferFrames[this.currentFrameIndex];
      
      // Update current time and notify listeners
      this.currentTime = new Date(frame.time);
      this.notifyListeners('currentTimeChanged', this.currentTime);
      this.notifyListeners('frameDataUpdate', frame.data);
      
      // Advance to next frame
      this.currentFrameIndex++;
      
      // Loop back to start if we've reached the end
      if (this.currentFrameIndex >= this.bufferFrames.length) {
        if (this.loopPlayback) {
          this.currentFrameIndex = 0;
        } else {
          this.stopAnimation();
        }
      }
      
    }, 1000 / this.playbackFPS); // 2 FPS = 500ms per frame
  }
}

export default TimeManager;
