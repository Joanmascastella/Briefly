  /**
   * Displays a Bootstrap alert inside #messageBox with the specified message & type.
   * type can be "success", "danger", "warning", "info", etc.
   */
  function showMessage(message, type = "success") {
    const messageBox = document.getElementById("messageBox");
    // Reset classes
    messageBox.className = "alert alert-" + type;
    // Set text
    messageBox.textContent = message;
    // Make sure it's visible
    messageBox.classList.remove("d-none");

    // Optionally auto-hide after 3 seconds
    setTimeout(() => {
      messageBox.classList.add("d-none");
    }, 3000);
  }