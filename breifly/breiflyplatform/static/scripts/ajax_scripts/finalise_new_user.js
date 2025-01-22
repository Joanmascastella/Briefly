document.addEventListener("DOMContentLoaded", () => {
    const steps = document.querySelectorAll(".step");
    const nextButtons = document.querySelectorAll(".next-btn");
    const prevButtons = document.querySelectorAll(".prev-btn");
    const submitButton = document.querySelector(".submit-btn");

    let currentStep = 0;

    function showStep(index) {
        steps.forEach((step, i) => {
            step.classList.toggle("d-none", i !== index);
        });
    }

    nextButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (currentStep < steps.length - 1) {
                currentStep++;
                showStep(currentStep);
            }
        });
    });

    prevButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            if (currentStep > 0) {
                currentStep--;
                showStep(currentStep);
            }
        });
    });

    async function submitForm() {
        const formData = {};

        // Collect all form data
        steps.forEach((step) => {
            const inputs = step.querySelectorAll(".form-control");
            inputs.forEach((input) => {
                formData[input.name] = input.value;
            });
        });

        try {
            const response = await fetch("/account/new/user/", {
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

    submitButton.addEventListener("click", (e) => {
        e.preventDefault();
        submitForm();
    });

    showStep(currentStep);
});

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
