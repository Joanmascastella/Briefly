document.addEventListener("DOMContentLoaded", () => {
    const steps = document.querySelectorAll(".step");
    const nextButtons = document.querySelectorAll(".next-btn");
    const prevButtons = document.querySelectorAll(".prev-btn");
    const submitButton = document.querySelector(".submit-btn");

    let currentStep = 0;

    // Function to get the language prefix dynamically from the URL
    function getLanguagePrefix() {
        const pathSegments = window.location.pathname.split("/");
        return pathSegments[1]; // Assumes the language prefix is the first segment after the domain
    }

    // Function to show/hide steps based on the current step index
    function showStep(index) {
        steps.forEach((step, i) => {
            step.classList.toggle("d-none", i !== index); // Show the current step and hide others
        });

        // Enable/disable navigation buttons based on the step
        if (index === 0) {
            prevButtons.forEach((btn) => btn.classList.add("d-none"));
        } else {
            prevButtons.forEach((btn) => btn.classList.remove("d-none"));
        }

        if (index === steps.length - 1) {
            submitButton.classList.remove("d-none");
            nextButtons.forEach((btn) => btn.classList.add("d-none"));
        } else {
            submitButton.classList.add("d-none");
            nextButtons.forEach((btn) => btn.classList.remove("d-none"));
        }
    }

    // Event listeners for the "Next" buttons
    nextButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (currentStep < steps.length - 1) {
                currentStep++;
                showStep(currentStep);
            }
        });
    });

    // Event listeners for the "Previous" buttons
    prevButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (currentStep > 0) {
                currentStep--;
                showStep(currentStep);
            }
        });
    });

    // Function to submit the form data via an AJAX POST request
    async function submitForm() {
        const formData = {};
        const languagePrefix = getLanguagePrefix();

        // Collect all form data from input fields
        steps.forEach((step) => {
            const inputs = step.querySelectorAll(".form-control");
            inputs.forEach((input) => {
                formData[input.name] = input.value;
            });
        });

        try {
            const response = await fetch(`/${languagePrefix}/account/new/user/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (response.ok && !data.error) {
                showMessage("Account setup successful! Redirecting...", "success");
                setTimeout(() => {
                    window.location.href = "/";
                }, 1500);
            } else {
                showMessage(data.error || "An error occurred during setup.", "danger");
            }
        } catch (error) {
            showMessage("Network error: " + error, "danger");
        }
    }

    // Event listener for the "Submit" button
    submitButton.addEventListener("click", (e) => {
        e.preventDefault(); // Prevent form submission
        submitForm();
    });

    // Initialize the form by showing the first step
    showStep(currentStep);
});

// Function to show a temporary message (success or error)
function showMessage(message, type = "success") {
    const messageBox = document.getElementById("messageBox") || document.createElement("div");
    if (!messageBox.id) {
        messageBox.id = "messageBox";
        document.body.appendChild(messageBox);
    }

    messageBox.className = "alert alert-" + type;
    messageBox.textContent = message;
    messageBox.classList.remove("d-none");

    setTimeout(() => {
        messageBox.classList.add("d-none");
    }, 3000);
}