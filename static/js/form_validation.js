document.addEventListener("DOMContentLoaded", () => {
    // Utility function to show error messages
    function showError(input, message) {
        const errorElement = document.createElement("small");
        errorElement.className = "error-message";
        errorElement.style.color = "red";
        errorElement.innerText = message;
        input.parentNode.appendChild(errorElement);
    }

    // Utility function to clear error messages
    function clearErrors(form) {
        const errors = form.querySelectorAll(".error-message");
        errors.forEach(error => error.remove());
    }

    // Validation rules for forms
    const formValidations = {
        "registerForm": (form) => {
            const email = form.querySelector("input[name='email']");
            const password = form.querySelector("input[name='password']");
            let valid = true;

            if (!email.value || !email.value.includes("@")) {
                showError(email, "Please enter a valid email.");
                valid = false;
            }

            if (!password.value || password.value.length < 6) {
                showError(password, "Password must be at least 6 characters long.");
                valid = false;
            }

            return valid;
        },
        "loginForm": (form) => {
            const email = form.querySelector("input[name='email']");
            const password = form.querySelector("input[name='password']");
            let valid = true;

            if (!email.value || !email.value.includes("@")) {
                showError(email, "Please enter a valid email.");
                valid = false;
            }

            if (!password.value) {
                showError(password, "Password is required.");
                valid = false;
            }

            return valid;
        },
        "feedbackForm": (form) => {
            const feedback = form.querySelector("textarea[name='feedback']");
            let valid = true;

            if (!feedback.value || feedback.value.trim() === "") {
                showError(feedback, "Feedback cannot be empty.");
                valid = false;
            }

            return valid;
        },
        // Add more form-specific validations here
    };

    // Attach validation to forms
    Object.keys(formValidations).forEach(formId => {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener("submit", (event) => {
                clearErrors(form);
                const isValid = formValidations[formId](form);
                if (!isValid) {
                    event.preventDefault();
                }
            });
        }
    });
});