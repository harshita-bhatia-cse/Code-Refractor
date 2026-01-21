// frontend/js/auth.js

function getToken() {
  const token = localStorage.getItem("jwt_token");

  if (!token) {
    alert("Session expired. Please login again.");
    window.location.href = "index.html";
    return null;
  }

  return token;
}

function authHeader() {
  return {
    "Authorization": "Bearer " + getToken(),
    "Content-Type": "application/json"
  };
}
  
