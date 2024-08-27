document.getElementById('cv-file').addEventListener('change', function() {
    var fileName = this.files[0].name;
    var fileNameDisplay = document.getElementById('file-name');
    fileNameDisplay.textContent = "Selected file: " + fileName;
    fileNameDisplay.style.display = 'block';
});

document.getElementById('cv-form').addEventListener('submit', function(event) {
    event.preventDefault();

    // Show the spinner and loading bar
    document.getElementById('spinner').style.display = 'block';
    const loadingBar = document.getElementById('loading-bar');
    loadingBar.style.display = 'block';

    // Show the uploading message
    document.getElementById('uploading-message').style.display = 'block';

    var formData = new FormData();
    var fileInput = document.getElementById('cv-file');
    formData.append('file', fileInput.files[0]);

    fetch('/process-cv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Hide the spinner, loading bar, and uploading message after processing
        document.getElementById('spinner').style.display = 'none';
        loadingBar.style.display = 'none';
        document.getElementById('uploading-message').style.display = 'none';

        document.getElementById('message').textContent = data.message || data.error;
        if (data.message && data.message.includes('successfully')) {
            // Show download link if successful
            const link = document.createElement('a');
            link.href = data.file_url; // Link to download the formatted CV
            link.textContent = 'Download Formatted CV';
            link.target = '_blank';
            document.getElementById('message').appendChild(link);
        }
    })
    .catch(error => {
        // Hide the spinner, loading bar, and uploading message if there's an error
        document.getElementById('spinner').style.display = 'none';
        loadingBar.style.display = 'none';
        document.getElementById('uploading-message').style.display = 'none';

        document.getElementById('message').textContent = 'An error occurred: ' + error.message;
    });
});
