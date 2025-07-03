document.getElementById("video-upload-form").addEventListener("submit", function (e) {
    e.preventDefault();

    const fileInput = document.getElementById("video-upload");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a video file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append("video", file);

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("✅ Server Response:", data);

        if (data.video_url) {
            const processedVideoURL = `http://127.0.0.1:5000${data.video_url}`;
            document.getElementById("video-preview-source").src = processedVideoURL;
            document.getElementById("video-player").load();
        } else {
            alert("Error processing video.");
        }
    })
    .catch(error => {
        console.error("❌ Fetch Error:", error);
        alert("Network error. Please check your Flask server and try again.");
    });
});
