document.addEventListener("DOMContentLoaded", function () {
    fetchImages();
    fetchStats();
});

// Handle user login
async function loginUser(event) {
    event.preventDefault();
    
    let username = document.getElementById("userId").value.trim();
    let password = document.getElementById("password").value.trim();
    let errorMessage = document.getElementById("error-message");

    const response = await fetch("http://127.0.0.1:5000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.ok) {
        localStorage.setItem("authToken", data.token);
        alert("Login successful!");
        window.location.href = "dashboard.html";
    } else {
        errorMessage.textContent = data.error || "Invalid username or password.";
        errorMessage.style.display = "block";
    }
}

document.querySelector(".form")?.addEventListener("submit", loginUser);

// Handle image upload
async function uploadImage(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById("imageUpload");
    if (fileInput.files.length === 0) {
        alert("Please select an image to upload.");
        return;
    }
    
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    
    const token = localStorage.getItem("authToken");
    if (!token) {
        alert("Please login first.");
        return;
    }
    
    const response = await fetch("http://127.0.0.1:5000/api/upload", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
    });
    
    const data = await response.json();
    if (response.ok) {
        alert(`Image uploaded successfully!\nCategory: ${data.category}\nConfidence: ${(data.confidence * 100).toFixed(2)}%`);
        fetchImages();
    } else {
        alert("Error: " + (data.error || "Failed to upload image."));
    }
}

document.getElementById("uploadForm")?.addEventListener("submit", uploadImage);

// Fetch and display uploaded images
async function fetchImages() {
    const response = await fetch("http://127.0.0.1:5000/api/images");
    const data = await response.json();
    
    const imageContainer = document.getElementById("imageContainer");
    imageContainer.innerHTML = "";
    
    data.forEach(img => {
        const imgWrapper = document.createElement("div");
        imgWrapper.classList.add("image-box");
        
        const imgElement = document.createElement("img");
        imgElement.src = `http://127.0.0.1:5000/uploads/${img.filename}`;
        imgElement.alt = img.category;
        imgElement.width = 200;
        
        const label = document.createElement("p");
        label.innerHTML = `<strong>Classification:</strong> ${img.category} (${(img.confidence * 100).toFixed(2)}%)`;
        
        imgWrapper.appendChild(imgElement);
        imgWrapper.appendChild(label);
        imageContainer.appendChild(imgWrapper);
    });
}

// Fetch stats for dashboard
async function fetchStats() {
    const response = await fetch("http://127.0.0.1:5000/api/stats");
    const data = await response.json();
    document.getElementById("totalImages").innerText = `Total Images: ${data.total}`;
}

// Logout function
function logout() {
    localStorage.removeItem("authToken");
    window.location.href = "index.html";
}

document.getElementById("logout")?.addEventListener("click", logout);
