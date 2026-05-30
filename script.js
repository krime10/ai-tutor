const user = JSON.parse(localStorage.getItem("aiTutorUser"));

if (!user) {
    window.location.href = "/login";
}

const welcomeText = document.getElementById("welcome-text");
const profileText = document.getElementById("student-profile");
const logoutButton = document.getElementById("logout-button");
const chatContainer = document.getElementById("chat-container");
const sendButton = document.getElementById("send-button");
const questionInput = document.getElementById("question");

if (welcomeText && user) {
    welcomeText.textContent = `Hello, ${user.fullName}. Ask a question about Electricity.`;
}

if (profileText && user) {
    const interests = Array.isArray(user.interests) && user.interests.length
        ? user.interests.join(", ")
        : "No interests selected";
    profileText.textContent = `Favorite subjects: ${user.favoriteSubjects}. Interests: ${interests}.`;
}

if (logoutButton) {
    logoutButton.addEventListener("click", () => {
        localStorage.removeItem("aiTutorUser");
        window.location.href = "/login";
    });
}

async function sendMessage() {
    if (!questionInput) return;
    const question = questionInput.value.trim();
    if (!question) return;

    if (chatContainer) {
        chatContainer.innerHTML += `\n            <div class="user-message">${escapeHtml(question)}</div>`;
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    questionInput.value = "";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: user.username,
                text: question,
                profile: user,
            }),
        });

        const data = await response.json();
        const reply = data.reply || data.detail || "Sorry, I couldn't get a response.";

        if (chatContainer) {
            chatContainer.innerHTML += `\n            <div class="bot-message">${escapeHtml(reply)}</div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (error) {
        if (chatContainer) {
            chatContainer.innerHTML += `\n            <div class="bot-message">Error connecting to the tutor.</div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

if (sendButton) {
    sendButton.addEventListener("click", sendMessage);
}

if (questionInput) {
    questionInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
}
