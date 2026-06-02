const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const apiOrigin = window.location.origin && window.location.origin !== "null"
    ? window.location.origin
    : "http://127.0.0.1:8000";

function getApiUrl(path) {
    return new URL(path, apiOrigin).href;
}

async function parseErrorBody(response) {
    try {
        const data = await response.json();
        return data.detail || data.message || JSON.stringify(data);
    } catch {
        return response.statusText || `Request failed with status ${response.status}`;
    }
}

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();
        const messageNode = document.getElementById("login-message");

        if (!messageNode) return;
        messageNode.style.color = "#dc2626";

        try {
            const response = await fetch(getApiUrl("/api/login"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
                messageNode.textContent = await parseErrorBody(response);
                return;
            }

            const data = await response.json();
            localStorage.setItem("aiTutorUser", JSON.stringify(data.user));
            window.location.href = "/tutor";
        } catch (error) {
            console.error("Login request failed", error);
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

        if (!messageNode) return;
        messageNode.style.color = "#dc2626";

        try {
            const response = await fetch(getApiUrl("/api/register"), {
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

            if (!response.ok) {
                messageNode.textContent = await parseErrorBody(response);
                return;
            }

            messageNode.style.color = "#16a34a";
            messageNode.textContent = "Registration complete. Redirecting to login...";
            setTimeout(() => {
                window.location.href = "/login";
            }, 1000);
        } catch (error) {
            console.error("Registration request failed", error);
            messageNode.textContent = "Unable to connect. Please try again.";
        }
    });
}
