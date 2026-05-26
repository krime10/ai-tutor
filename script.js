const userName =
    prompt("Enter your name:") || "Student";

async function sendMessage() {

    

    const questionInput =
        document.getElementById("question");

    const chatContainer =
        document.getElementById("chat-container");

    const question =
        questionInput.value;

    if (!question.trim()) {
        return;
    }

    // Add user message
    chatContainer.innerHTML += `
        <div class="user-message">
            ${question}
        </div>
    `;

    questionInput.value = "";

    // Scroll down
    chatContainer.scrollTop =
        chatContainer.scrollHeight;

    try {

        const response = await fetch("/chat", {
            method: "POST",  

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
            name: userName,
            text: question
            })
        });

        const data = await response.json();

        // Add bot message
        chatContainer.innerHTML += `
            <div class="bot-message">
                ${data.reply}
            </div>
        `;

        // Scroll again
        chatContainer.scrollTop =
            chatContainer.scrollHeight;

    } catch (error) {

        chatContainer.innerHTML += `
            <div class="bot-message">
                Error connecting to tutor.
            </div>
        `;
    }
}
document
    .getElementById("question")
    .addEventListener("keydown", function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    });