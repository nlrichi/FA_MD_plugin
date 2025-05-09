const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const snap = document.getElementById('snap');
const snapSecond = document.getElementById('snap-second');
const close = document.getElementById('close');
const status = document.getElementById('status');
const firstCapture = document.getElementById('first-capture');
const result = document.getElementById('result');

let firstImageData = null;
let secondImageData = null;
let currentGifUrl = null;

// Initialise camera
function initCamera() {
  if (navigator.mediaDevices?.getUserMedia) {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'user' } })
      .then(stream => { 
        video.srcObject = stream; 
        status.textContent = 'Camera ready! Please capture your neutral expression first.'; 
      })
      .catch(e => { status.textContent = 'Camera error: ' + e.message; });
  } else {
    status.textContent = 'No camera support.';
  }
}

// Reset the capture process
function resetCapture() {
  firstImageData = null;
  secondImageData = null;
  currentGifUrl = null;
  result.innerHTML = '';
  firstCapture.style.display = 'none';
  firstCapture.innerHTML = '';
  snapSecond.style.display = 'none';
  snapSecond.disabled = false;
  snap.style.display = 'inline-block';
  snap.disabled = false;
  status.textContent = 'Camera ready! Please capture your neutral expression first.';
}

function showNotification(message) {
  const notificationDiv = document.createElement('div');
  notificationDiv.className = 'notification';
  notificationDiv.textContent = message;
  document.body.appendChild(notificationDiv);
  
  setTimeout(() => {
    notificationDiv.style.opacity = '0';
    setTimeout(() => notificationDiv.remove(), 500);
  }, 3000);
}

// Download GIF
function downloadGif(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || 'mood_animation.gif';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  
  showNotification('Animation downloaded!');
}

initCamera();

// First image capture
snap.addEventListener('click', () => {
  status.textContent = 'Processing first image...';
  snap.disabled = true;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  
  firstImageData = canvas.toDataURL('image/jpeg');
  
  firstCapture.style.display = 'none';
  
  // Show second capture button
  status.textContent = 'Now prepare to express an emotion!';
  snapSecond.style.display = 'inline-block';
  snap.style.display = 'none';
  snap.disabled = false;
});

// Second image capture
snapSecond.addEventListener('click', () => {
  status.textContent = 'Processing...';
  snapSecond.disabled = true;
  snapSecond.style.display = 'none';
  
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  
  secondImageData = canvas.toDataURL('image/jpeg');
  
  // Show preview of second capture (the expression image)
  firstCapture.innerHTML = `
    <h3>Expression Captured:</h3>
    <img src="${secondImageData}" style="max-width:150px;">
  `;
  firstCapture.style.display = 'inline-block';
  
  // Send both images to the backend
  fetch('https://localhost:5000/process_images', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      first_image: firstImageData,
      second_image: secondImageData
    })
  })
  .then(res => {
    if (!res.ok) {
      resetCapture();
      throw new Error('Failed to process images, Please try again.');
    }
    return res.json();
  })
  .then(data => {
    if (data.error) {
      status.textContent = data.error;
      snapSecond.style.display = 'inline-block';
      snapSecond.disabled = false;
      return;
    }
    
    status.textContent = `The ${data.dominant_emotion} mood was detected!`;
    currentGifUrl = `https://localhost:5000/download?gif_path=${encodeURIComponent(data.gif_path)}&t=${Date.now()}`;
    
    result.innerHTML = `
      <img id="result-gif" src="${currentGifUrl}" style="max-width:200px;">
      <br>
      <div class="button-group">
        <button id="use-mood">Use This Animation</button>
        <button id="regenerate">Regenerate</button>
      </div>
    `;
    
    // Use This Animation - sends to email and downloads
    document.getElementById('use-mood').onclick = () => {
      // Send data to parent window for email
      window.opener.postMessage({ type: 'mood-selected', data }, '*');
      downloadGif(currentGifUrl, `mood_${data.dominant_emotion}.gif`);
      close.style.display = 'inline-block';
    };
    
    // Regenerate button - resets the capture
    document.getElementById('regenerate').onclick = () => {
      resetCapture();
    };
  })
  .catch(e => { 
    status.textContent = 'Error: '+e.message;
    snapSecond.style.display = 'inline-block';
    snapSecond.disabled = false;
  });
});

close.addEventListener('click', () => window.close());