 // Show message function
  function showMessage(message, type = "success") {
    const messageBox = document.getElementById("messageBox") || document.createElement("div");

    if (!messageBox.id) {
      messageBox.id = "messageBox";
      document.body.appendChild(messageBox);
    }

    // Update alert classes and text (Bootstrap style)
    messageBox.className = "alert alert-" + type;
    messageBox.textContent = message;
    messageBox.classList.remove("d-none");

    // Auto-hide after 3 seconds
    setTimeout(() => {
      messageBox.classList.add("d-none");
    }, 3000);
  }

  // Async function to save user settings
  async function saveSettings() {
    try {
      const emailReports = document.getElementById('emailReports').value;
      const timezone = document.getElementById('timezone').value;

      // POST to /settings/modify/
      // The Django view expects { "emailReports": "...", "timezone": "..." }
      const response = await fetch('/settings/modify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          emailReports,
          timezone
        }),
      });

      const data = await response.json();
      if (response.ok) {
        showMessage(data.message || 'Settings updated successfully', 'success');
      } else {
        showMessage(data.error || 'Something went wrong updating settings', 'danger');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      showMessage('Error saving settings', 'danger');
    }
  }

  // Async function to save account information
  async function saveAccountInfo() {
    try {
      const accountData = {
        fullName: document.getElementById('fullName').value,
        position: document.getElementById('position').value,
        reportEmail: document.getElementById('reportEmail').value,
        phonenr: document.getElementById('phonenr').value,
        targetAudience: document.getElementById('targetAudience').value,
        contentSentiment: document.getElementById('contentSentiment').value,
        company: document.getElementById('company').value,
        industry: document.getElementById('industry').value,
        companyBrief: document.getElementById('companyBrief').value,
        recentVentures: document.getElementById('recentVentures').value,
      };

      // POST to /settings/modify/account
      // The Django view expects these exact keys (e.g. "fullName", "reportEmail", etc.)
      const response = await fetch('/settings/modify/account', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(accountData),
      });

      const data = await response.json();
      if (response.ok) {
        showMessage(data.message || 'Account information updated successfully', 'success');
      } else {
        showMessage(data.error || 'Something went wrong updating account info', 'danger');
      }
    } catch (error) {
      console.error('Error saving account info:', error);
      showMessage('Error saving account info', 'danger');
    }
  }