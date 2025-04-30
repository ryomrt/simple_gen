let mediaRecorder;
let audioChunks = [];

document.addEventListener("DOMContentLoaded", () => {
  const recordBtn = document.getElementById("recordBtn");
  const transcriptEl = document.getElementById("transcript");

  if (recordBtn) {
    recordBtn.addEventListener("click", async () => {
      if (!mediaRecorder || mediaRecorder.state === "inactive") {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        audioChunks = [];

        mediaRecorder.addEventListener("dataavailable", e => audioChunks.push(e.data));
        mediaRecorder.addEventListener("stop", async () => {
          const blob = new Blob(audioChunks, { type: "audio/wav" });
          const formData = new FormData();
          formData.append("file", blob, "recording.wav");

          const resp = await fetch("/upload-audio", { method: "POST", body: formData });
          const data = await resp.json();
          transcriptEl.textContent = data.text || "(no transcript)";
          document.querySelector("textarea[name=text_input]").value = data.text;
        });

        recordBtn.textContent = "■ Stop";
      } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
        recordBtn.textContent = "● Record";
      }
    });
  }
});