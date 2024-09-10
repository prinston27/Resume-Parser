document.getElementById("login-form").addEventListener("submit", function(e) {
    e.preventDefault();
    
    // Get form data
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    
    // Basic client-side validation
    if (username === "" || password === "") {
        document.getElementById("message").innerText = "Both fields are required.";
        return;
    }

    // Display a loading message
    document.getElementById("message").innerText = "Logging in...";

    // Send login request to the server (example with fetch API)
    fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            // Handle HTTP errors
            throw new Error('Invalid username or password.');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Redirecting to the dashboard on successful login
            window.location.href = "/dashboard";
        } else {
            // Show error message
            document.getElementById("message").innerText = data.message || "Invalid username or password.";
        }
    })
    .catch(error => {
        document.getElementById("message").innerText = "An error occurred during login: " + error.message;
        console.error("Error:", error);
    });
});
