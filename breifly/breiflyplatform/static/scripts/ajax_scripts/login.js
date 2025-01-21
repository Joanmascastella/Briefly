 function showMessage(message, type = "success") {
    const messageBox = document.getElementById("messageBox");
    messageBox.className = "alert alert-" + type;
    messageBox.textContent = message;
    messageBox.classList.remove("d-none");
    setTimeout(() => {
      messageBox.classList.add("d-none");
    }, 3000);
  }

  async function loginViaJSON() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    try {
      const response = await fetch("/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        showMessage("Login successful!", "success");
        setTimeout(() => {
          window.location.href = data.redirect_url || "/";
        }, 1000);
      } else {
        const err = data.error || "Invalid credentials.";
        showMessage(err, "danger");
      }
    } catch (error) {
      showMessage("Network error: " + error, "danger");
    }
  }