document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("video-upload-form");
  const videoPreview = document.getElementById("video-preview-source");
  const videoPlayer = document.getElementById("video-player");
  const resultInfo = document.getElementById("result-info");

  form.addEventListener("submit", async function (event) {
      event.preventDefault();

      const formData = new FormData(form);
      const response = await fetch("/upload", {
          method: "POST",
          body: formData
      });

      const data = await response.json();  // Expecting JSON response with `processed_video_url`

      if (response.ok) {
          const videoUrl = data.processed_video_url; // Get URL from response

          // Update Video Preview
          videoPreview.src = videoUrl;
          videoPlayer.load();

          // Show Analysis Result Section
          resultInfo.innerHTML = `<p>Analysis complete! Watch the processed video below:</p>`;
      } else {
          resultInfo.innerHTML = `<p>Error processing video. Please try again.</p>`;
      }
  });
});
