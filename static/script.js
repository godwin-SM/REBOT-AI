// ========================
// AUTHENTICATION & STORAGE
// ========================

function getToken() {
  return localStorage.getItem("accessToken");
}

function setToken(accessToken) {
  localStorage.setItem("accessToken", accessToken);
}

function clearTokens() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("userEmail");
  localStorage.removeItem("userName");
  localStorage.removeItem("userPicture");
}

function isAuthenticated() {
  return !!getToken();
}

// ========================
// GOOGLE SIGN-IN
// ========================

let googleTokenResponse = null;

function onSuccess(credentialResponse) {
  // credentialResponse.credential is the JWT token from Google
  googleTokenResponse = credentialResponse;
  
  // Decode the token to get user info including picture
  const decoded = jwtDecode(credentialResponse.credential);
  console.log("[DEBUG] Decoded JWT from Google:", decoded);
  
  sendGoogleTokenToBackend(credentialResponse.credential, decoded);
}

// Simple JWT decoder function
function jwtDecode(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Error decoding JWT:", e);
    return {};
  }
}

function onError() {
  alert("Google Sign-In failed. Please try again.");
}

async function sendGoogleTokenToBackend(googleToken, decodedPayload = {}) {
  try {
    // Show loading state
    disableGoogleButton();
    
    // Extract picture from decoded JWT
    const frontendPicture = decodedPayload.picture || null;
    
    const response = await fetch("/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        token: googleToken,
        picture: frontendPicture  // Send picture from decoded JWT
      })
    });

    const data = await response.json();
    
    console.log("[DEBUG] Auth response from backend:", data);

    if (data.success) {
      // Save token and user info
      setToken(data.tokens.access_token);
      localStorage.setItem("userEmail", data.email);
      localStorage.setItem("userName", data.name);
      
      // Use picture from backend if available, otherwise use decoded payload
      let picture = data.picture || decodedPayload.picture || "";
      localStorage.setItem("userPicture", picture);
      
      console.log("[DEBUG] Using picture from:", data.picture ? "backend" : (decodedPayload.picture ? "decoded JWT" : "none"));
      console.log("[DEBUG] Picture URL:", picture);

      // Show main content
      document.getElementById("authModal").classList.remove("active");
      document.getElementById("main-content").classList.add("active");
      document.getElementById("userEmail").textContent = data.email;
      document.getElementById("userName").textContent = data.name;
      
      // Set avatar with fallback
      console.log("[DEBUG] Calling setUserAvatar with picture:", picture);
      setUserAvatar(picture, data.name);

      // Load chat history
      loadChatHistory();
    } else {
      alert("Authentication error: " + (data.error || "Unknown error"));
      enableGoogleButton();
    }
  } catch (err) {
    alert("Connection error. Please try again.");
    console.error(err);
    enableGoogleButton();
  }
}

function disableGoogleButton() {
  const button = document.querySelector('[data-callback="onSuccess"]');
  if (button) button.style.opacity = "0.5";
}

function enableGoogleButton() {
  const button = document.querySelector('[data-callback="onSuccess"]');
  if (button) button.style.opacity = "1";
}

function setUserAvatar(pictureUrl, userName) {
  const avatarImg = document.getElementById("user-avatar");
  
  if (!avatarImg) {
    console.warn("[DEBUG] Avatar image element not found");
    return;
  }
  
  console.log("[DEBUG] setUserAvatar called with:", {
    pictureUrl: pictureUrl,
    pictureUrlLength: pictureUrl ? pictureUrl.length : 0,
    pictureUrlTrimmed: pictureUrl ? pictureUrl.trim().length : 0,
    userName: userName
  });
  
  // If we have a picture URL, try to load it
  if (pictureUrl && pictureUrl.trim().length > 0) {
    console.log("[DEBUG] Picture URL is valid, attempting to load");
    
    // Create a new Image object to preload and test
    const testImg = new Image();
    
    // Set a timeout - if image doesn't load in 3 seconds, use fallback
    const timeoutId = setTimeout(() => {
      console.warn("[DEBUG] Picture load timeout (3s), using fallback");
      createFallbackAvatar(avatarImg, userName);
    }, 3000);
    
    testImg.onload = function() {
      clearTimeout(timeoutId);
      console.log("[DEBUG] ✅ Picture loaded successfully!");
      avatarImg.src = pictureUrl;
      avatarImg.style.display = "block";
    };
    
    testImg.onerror = function(e) {
      clearTimeout(timeoutId);
      console.warn("[DEBUG] ❌ Picture load failed. Error:", e);
      console.warn("[DEBUG] URL attempted:", pictureUrl);
      createFallbackAvatar(avatarImg, userName);
    };
    
    // Start loading with CORS headers
    testImg.crossOrigin = "anonymous";
    testImg.referrerPolicy = "no-referrer";
    testImg.src = pictureUrl;
    
  } else {
    console.log("[DEBUG] No picture URL provided (empty or null), using fallback");
    createFallbackAvatar(avatarImg, userName);
  }
}

function createFallbackAvatar(avatarImg, userName) {
  // Create an SVG avatar with initials
  const initials = (userName || "U")
    .split(" ")
    .map(word => word.charAt(0).toUpperCase())
    .join("")
    .substring(0, 2) || "U";
  
  const colors = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", 
    "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
  ];
  
  // Use a consistent color based on name
  const colorIndex = (userName || "").charCodeAt(0) % colors.length;
  const bgColor = colors[colorIndex];
  
  const svgString = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="40" height="40">
      <rect width="100" height="100" fill="${bgColor}"/>
      <text x="50" y="50" font-size="40" font-weight="bold" fill="white" 
            text-anchor="middle" dominant-baseline="middle">${initials}</text>
    </svg>
  `;
  
  const blob = new Blob([svgString], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  
  avatarImg.src = url;
  avatarImg.style.display = "block";
}


function handleLogout() {
  clearTokens();
  localStorage.removeItem("chat");
  chat.innerHTML = "";
  document.getElementById("main-content").classList.remove("active");
  document.getElementById("authModal").classList.add("active");
  
  // Reset Google Sign-In and re-render the button
  if (window.google && window.google.accounts && window.google.accounts.id) {
    window.google.accounts.id.disableAutoSelect();
  }
  
  // Clear button container and re-render
  const buttonContainer = document.getElementById("googleSignInButton");
  if (buttonContainer) {
    buttonContainer.innerHTML = "";
  }
  
  // Re-initialize Google Sign-In
  initGoogleSignIn();
}

// ========================
// MAIN CHAT FUNCTIONS
// ========================

let chat;
let msgInput;

window.onload = function() {
  chat = document.getElementById("chat");
  msgInput = document.getElementById("msg");

  // Hide loader
  const loader = document.getElementById("loader");
  loader.style.display = "none";

  // Check if user is already authenticated
  if (isAuthenticated()) {
    document.getElementById("authModal").classList.remove("active");
    document.getElementById("main-content").classList.add("active");
    document.getElementById("userEmail").textContent = localStorage.getItem("userEmail");
    document.getElementById("userName").textContent = localStorage.getItem("userName");
    const picture = localStorage.getItem("userPicture");
    const name = localStorage.getItem("userName");
    setUserAvatar(picture, name);
    loadChatHistory();
  } else {
    // Initialize Google Sign-In
    initGoogleSignIn();
  }

  // Enter key to send
  msgInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
      send();
    }
  });
};

function initGoogleSignIn() {
  // Initialize Google Sign-In
  window.google.accounts.id.initialize({
    client_id: "221315512951-tqereujnih43r3q5vedvg28dieojk18d.apps.googleusercontent.com", // REPLACE with your Google Client ID
    callback: onSuccess,
    auto_select: false
  });

  // Render the button
  window.google.accounts.id.renderButton(
    document.getElementById('googleSignInButton'),
    {
      theme: 'filled_black',
      size: 'large',
      text: 'signin_with'
    }
  );
}

function loadChatHistory() {
  console.log("[DEBUG] Loading chat history...");
  console.log("[DEBUG] Token:", getToken());
  
  // Try to fetch from server first
  fetch("/chat-history", {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${getToken()}`,
      "Content-Type": "application/json"
    }
  })
  .then(response => {
    console.log("[DEBUG] Response status:", response.status);
    return response.json();
  })
  .then(data => {
    console.log("[DEBUG] Response data:", data);
    let history = [];
    
    if (data.success && data.history && data.history.length > 0) {
      console.log("[DEBUG] Loading", data.history.length, "messages from server");
      history = data.history;
      chat.innerHTML = "";
      history.forEach(item => {
        addMessage(item.role, item.content);
      });
      // Update localStorage with fresh server data
      localStorage.setItem("chat", JSON.stringify(history));
    } else {
      console.log("[DEBUG] No history from server, trying localStorage fallback");
      // Fallback to localStorage if server returns empty
      let localHistory = JSON.parse(localStorage.getItem("chat")) || [];
      if (localHistory.length > 0) {
        console.log("[DEBUG] Loading", localHistory.length, "messages from localStorage");
        chat.innerHTML = "";
        localHistory.forEach(item => {
          addMessage(item.role, item.content);
        });
        history = localHistory;
      } else {
        console.log("[DEBUG] No chat history found anywhere");
        chat.innerHTML = "";
      }
    }
    
    chat.scrollTop = chat.scrollHeight;
  })
  .catch(err => {
    // Fallback to localStorage if server request fails
    console.warn("[DEBUG] Could not fetch server history:", err);
    let history = JSON.parse(localStorage.getItem("chat")) || [];
    chat.innerHTML = "";
    if (history.length > 0) {
      console.log("[DEBUG] Loading", history.length, "messages from localStorage (network error fallback)");
      history.forEach(item => {
        addMessage(item.role, item.content);
      });
    }
    chat.scrollTop = chat.scrollHeight;
  });
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function addMessage(role, content) {
  let className = role === "user" ? "user" : "bot";

  // Format AI text
  content = content
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>")
    .replace(/- /g, "<br>• ");

  chat.innerHTML += `
    <div class="message ${className}">
      ${content}
    </div>
  `;

  scrollToBottom();
}

// SEND MESSAGE
async function send() {
  let msg = msgInput.value.trim();

  if (msg === "") return;

  addMessage("user", msg);
  msgInput.value = "";
  chat.scrollTop = chat.scrollHeight;

  // typing indicator
  let typing = document.createElement("div");
  typing.className = "message bot";
  typing.id = "typing";
  typing.innerHTML = '<div class="loading-spinner"></div>REBOT is thinking...';
  chat.appendChild(typing);
  chat.scrollTop = chat.scrollHeight;

  let history = JSON.parse(localStorage.getItem("chat")) || [];
  
  // Save user message to localStorage immediately (for offline support)
  history.push({
    role: "user",
    content: msg
  });
  localStorage.setItem("chat", JSON.stringify(history));

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        message: msg,
        history: history
      })
    });

    const data = await response.json();

    // remove typing
    let typingEl = document.getElementById("typing");
    if (typingEl) typingEl.remove();

    let botReply = "";
    if (data.success) {
      botReply = data.reply;
      addMessage("bot", botReply);
    } else {
      botReply = "⚠️ " + (data.error || "Error: Could not get response");
      addMessage("bot", botReply);
      if (response.status === 401) {
        handleLogout();
      }
    }

    chat.scrollTop = chat.scrollHeight;

    // Save bot reply to history and localStorage
    history.push({
      role: "bot",
      content: botReply
    });
    localStorage.setItem("chat", JSON.stringify(history));

  } catch (err) {
    let typingEl = document.getElementById("typing");
    if (typingEl) typingEl.remove();

    const errorMsg = "⚠️ Error connecting to server.";
    chat.innerHTML += `<div class="message bot">${errorMsg}</div>`;
    
    // Save error message to localStorage
    history.push({
      role: "bot",
      content: errorMsg
    });
    localStorage.setItem("chat", JSON.stringify(history));
  }
}

// FILE UPLOAD
async function uploadFile() {
  let file = document.getElementById("fileUpload").files[0];

  if (!file) {
    alert("Please select a file");
    return;
  }

  let formData = new FormData();
  formData.append("file", file);

  addMessage("user", `📎 Uploading: ${file.name}`);
  chat.scrollTop = chat.scrollHeight;

  try {
    const res = await fetch("/upload", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${getToken()}`
      },
      body: formData
    });

    const data = await res.json();

    if (data.success) {
      addMessage("bot", data.reply);
    } else {
      addMessage("bot", "⚠️ " + (data.error || "Upload failed"));
      if (res.status === 401) {
        handleLogout();
      }
    }

    chat.scrollTop = chat.scrollHeight;

    let history = JSON.parse(localStorage.getItem("chat")) || [];

    history.push({
      role: "user",
      content: `📎 Uploaded: ${file.name}`
    });

    history.push({
      role: "bot",
      content: data.reply || data.error
    });

    localStorage.setItem("chat", JSON.stringify(history));
    
    // Reset file input
    document.getElementById("fileUpload").value = "";

  } catch (err) {
    chat.innerHTML += `<div class="message bot">⚠️ Upload failed.</div>`;
  }
}