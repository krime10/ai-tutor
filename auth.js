const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();
        const messageNode = document.getElementById("login-message");

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();
            if (!response.ok) {
                messageNode.textContent = data.detail || "Login failed.";
                return;
            }

            localStorage.setItem("aiTutorUser", JSON.stringify(data.user));
            window.location.href = "/tutor";
        } catch (error) {
            messageNode.textContent = "Unable to connect. Please try again.";
        }
    });
}

if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const fullName = document.getElementById("fullName").value.trim();
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();
        const academicClass = document.getElementById("academicClass").value.trim();
        const age = parseInt(document.getElementById("age").value, 10);
        const favoriteSubjects = document.getElementById("favoriteSubjects").value.trim();
        const interests = Array.from(document.querySelectorAll('input[name="interests"]:checked')).map((input) => input.value);
        const messageNode = document.getElementById("register-message");

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    fullName,
                    username,
                    password,
                    academicClass,
                    age,
                    favoriteSubjects,
                    interests,
                }),
            });

            const data = await response.json();
            if (!response.ok) {
                messageNode.textContent = data.detail || "Registration failed.";
                return;
            }

            messageNode.style.color = "#16a34a";
            messageNode.textContent = "Registration complete. Redirecting to login...";
            setTimeout(() => {
                window.location.href = "/login";
            }, 1000);
        } catch (error) {
            messageNode.textContent = "Unable to connect. Please try again.";
        }
    });
}
