document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("file-input");
  const fileNameDisplay = document.getElementById("file-name");

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
      fileNameDisplay.textContent = `${fileInput.files.length} file(s) selected`;
    } else {
      fileNameDisplay.textContent = "No file chosen";
    }
  });

  document
    .getElementById("upload-form")
    .addEventListener("submit", async function (event) {
      event.preventDefault();

      let files = fileInput.files;
      if (files.length === 0) {
        alert("Please select files to upload!");
        return;
      }

      let formData = new FormData();
      for (let file of files) {
        formData.append("files", file);
      }

      let progressText = document.getElementById("progress-text");
      let progressBar = document.querySelector(".progress-bar");
      let resultsDiv = document.getElementById("results");
      let loader = document.getElementById("loader");

      // Reset UI
      resultsDiv.innerHTML = "";
      progressBar.style.width = "0%";
      progressText.textContent = "Uploading...";
      loader.style.display = "block";

      try {
        let response = await fetch("/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Error uploading files.");
        }

        progressText.textContent = "Processing...";
        progressBar.style.width = "50%";

        let reader = response.body.getReader();
        let decoder = new TextDecoder();
        let receivedText = "";

        while (true) {
          let { done, value } = await reader.read();
          if (done) break;

          receivedText += decoder.decode(value);
          progressBar.style.width = "80%";
        }

        try {
          let resultData = JSON.parse(receivedText);
          console.log("Received Data:", resultData);

          progressBar.style.width = "100%";
          progressText.textContent = "Completed!";
          loader.style.display = "none";

          if (
            !resultData.plagiarism_results ||
            resultData.plagiarism_results.length === 0
          ) {
            resultsDiv.innerHTML = "<p>No plagiarism detected.</p>";
          } else {
            displayResults(resultData);
          }
        } catch (error) {
          console.error("Error parsing JSON:", error);
          progressText.textContent = "Error processing results.";
        }
      } catch (error) {
        console.error("Fetch Error:", error);
        progressText.textContent = "Failed to upload files.";
      }
    });

  function displayResults(data) {
    let resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "<h3>Plagiarism Results:</h3>";

    data.plagiarism_results.forEach((result) => {
      let resultCard = document.createElement("div");
      resultCard.classList.add("result-card");
      resultCard.innerHTML = `<p><b>${result.file1}</b> vs <b>${result.file2}</b></p>
                                    <p>Cosine Similarity: <b>${result.cosine_similarity}%</b></p>
                                    <p>Jaccard Similarity: <b>${result.jaccard_similarity}%</b></p>`;
      resultsDiv.appendChild(resultCard);
    });
  }
});
