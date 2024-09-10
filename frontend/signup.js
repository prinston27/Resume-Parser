document.getElementById('signup-form').addEventListener('submit', function (event) {
    event.preventDefault();  // Preventing the form from submitting in the default way
    
    // Get the form values
    const firstname = document.getElementById('firstname').value.trim();
    const lastname = document.getElementById('lastname').value.trim();
    const countryCode = document.getElementById('country-code').value.trim();
    const phoneno = document.getElementById('phoneno').value.trim();
    const email_id = document.getElementById('email_id').value.trim();
    const password = document.getElementById('password').value.trim();
    
    // Combine country code and phone number
    const fullPhoneNumber = countryCode + phoneno;

    // Simple validation 
    if (!firstname || !lastname || !phoneno || !email_id || !password) {
        displayMessage('Please fill out all fields', 'error');
        return;
    }
    
    // Basic email format validation
    const emailPattern = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailPattern.test(email_id)) {
        displayMessage('Please enter a valid email address', 'error');
        return;
    }
    
    // Basic phone number validation (numeric check)
    if (isNaN(phoneno)) {
        displayMessage('Please enter a valid phone number', 'error');
        return;
    }

    // Prepare the data to send
    const formData = {
        firstname: firstname,
        lastname: lastname,
        phoneno: fullPhoneNumber,
        email_id: email_id,
        password: password
    };
    document.getElementById("message").innerText = "Signing up... Please wait."
   
    // Make the AJAX request
    fetch('/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),  // Sending the form data as JSON
    })
    .then(response => {
        if (response.ok) {
            return response.json();  // Parse the JSON response
        } else if (response.status === 409) {
            throw new Error('A user with this email already exists.');
        } else {
            throw new Error('A user with this email already exists. Please go to the login page!');
        }
    })
    .then(data => {
        if (data.success) {
            displayMessage('Sign up successful!', 'success');
            // Redirect to login after 1.5 seconds
            setTimeout(() => {
                window.location.href = "/login";
            }, 1500);
        } else {
            displayMessage(data.message || 'Sign up failed. Please try again.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage(error.message || 'An error occurred during sign up. Please try again.', 'error');
    });
});

// Function to display messages to the user
function displayMessage(message, type) {
    const messageElement = document.getElementById('message');
    messageElement.textContent = message;

    // Set appropriate CSS class based on the type ('error', 'success', 'loading')
    messageElement.className = type;

    // Optionally, hide the message after a few seconds for non-loading types
    if (type !== 'loading') {
        setTimeout(() => {
            messageElement.textContent = '';
            messageElement.className = ''; 
        }, 3000);
    }
}
