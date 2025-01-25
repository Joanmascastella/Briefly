// Function to get the CSRF token from cookies
function getCSRFToken() {
  const cookies = document.cookie.split("; ");
  for (let i = 0; i < cookies.length; i++) {
    const [key, value] = cookies[i].split("=");
    if (key === "csrftoken") {
      return value; // Return the CSRF token if found
    }
  }
  return null; // Return null if CSRF token is not found
}

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

// Function to dynamically get the language prefix from the URL
function getLanguagePrefix() {
  const pathSegments = window.location.pathname.split("/");
  return pathSegments[1]; // Assumes the language prefix is the first segment after the domain
}

// Async function to save user settings
// async function saveSettings() {
//   try {
//     const emailReports = document.getElementById("emailReports")?.value;
//     const timezone = document.getElementById("timezone")?.value;
//     const csrfToken = getCSRFToken();
//     const languagePrefix = getLanguagePrefix();
//
//     // Check if the required fields and CSRF token exist
//     if (!csrfToken || !emailReports || !timezone) {
//       console.error("Error: Missing required fields or CSRF token");
//       showMessage("Error: Missing required fields or CSRF token", "danger");
//       return;
//     }
//
//     // POST to /settings/modify/ with dynamic language prefix
//     const response = await fetch(`/${languagePrefix}/settings/modify/`, {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//         "X-CSRFToken": csrfToken,
//       },
//       body: JSON.stringify({
//         emailReports,
//         timezone,
//       }),
//     });
//
//     const data = await response.json();
//     if (response.ok) {
//       showMessage(data.message || "Settings updated successfully", "success");
//     } else {
//       showMessage(data.error || "Something went wrong updating settings", "danger");
//     }
//   } catch (error) {
//     console.error("Error saving settings:", error);
//     showMessage("Error saving settings", "danger");
//   }
// }

// Async function to save account information
async function saveAccountInfo() {
  try {
    const csrfToken = getCSRFToken();
    const accountData = {
      fullName: document.getElementById("fullName")?.value,
      position: document.getElementById("position")?.value,
      // reportEmail: document.getElementById("reportEmail")?.value,
      // phonenr: document.getElementById("phonenr")?.value,
      // targetAudience: document.getElementById("targetAudience")?.value,
      // contentSentiment: document.getElementById("contentSentiment")?.value,
      company: document.getElementById("company")?.value,
      industry: document.getElementById("industry")?.value,
      companyBrief: document.getElementById("companyBrief")?.value,
      // recentVentures: document.getElementById("recentVentures")?.value,
    };
    const languagePrefix = getLanguagePrefix();

    // Check if CSRF token exists
    if (!csrfToken) {
      console.error("Error: Missing CSRF token");
      showMessage("Error: Missing CSRF token", "danger");
      return;
    }

    // POST to /settings/modify/account with dynamic language prefix
    const response = await fetch(`/${languagePrefix}/settings/modify/account/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(accountData),
    });

    const data = await response.json();
    if (response.ok) {
      showMessage(data.message || "Account information updated successfully", "success");
    } else {
      showMessage(data.error || "Something went wrong updating account info", "danger");
    }
  } catch (error) {
    console.error("Error saving account info:", error);
    showMessage("Error saving account info", "danger");
  }
}

// Add event listeners for the Save Settings and Save Account Info buttons
document.addEventListener("DOMContentLoaded", () => {
  // const saveSettingsBtn = document.getElementById("saveSettingsBtn");
  const saveAccountInfoBtn = document.getElementById("saveAccountInfoBtn");

  // if (saveSettingsBtn) {
  //   saveSettingsBtn.addEventListener("click", (e) => {
  //     e.preventDefault();
  //     saveSettings();
  //   });
  // }

  if (saveAccountInfoBtn) {
    saveAccountInfoBtn.addEventListener("click", (e) => {
      e.preventDefault();
      saveAccountInfo();
    });
  }
});