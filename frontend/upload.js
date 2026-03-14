uploadBtn.onclick = async () => {
  const file = fileInput.files[0];
  if (!file) {
    alert("Please select a file");
    return;
  }

  asrText.textContent = "Transcribing…";
  englishText.textContent = "Translating…";
  czechText.textContent = "Translating…";

  const form = new FormData();
  form.append("file", file);

  const res = await fetch("http://127.0.0.1:8000/translate-file", {
    method: "POST",
    body: form
  });

  if (!res.ok) {
    asrText.textContent = "Error occurred";
    return;
  }

  const data = await res.json();

  asrText.textContent = data.hindi || "";
  englishText.textContent = data.english || "";
  czechText.textContent = data.czech || "";
};
