const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const chatMessages = document.getElementById("chatMessages");
const sendButton = document.getElementById("sendButton");

function addMessage(text, sender) {
  const row = document.createElement("div");
  row.className = `message-row ${sender === "user" ? "user-row" : "bot-row"}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${sender === "user" ? "user-avatar" : "bot-avatar"}`;
  avatar.textContent = sender === "user" ? "You" : "✦";

  const content = document.createElement("div");
  content.className = "message-content";

  const bubble = document.createElement("div");
  bubble.className = `message-bubble ${sender === "user" ? "user-bubble" : "bot-bubble"}`;
  // textContent prevents user input from being interpreted as HTML.
  bubble.textContent = text;

  const time = document.createElement("span");
  time.className = "message-time";
  time.textContent = sender === "user" ? "You" : "Assistant";

  content.append(bubble, time);
  row.append(avatar, content);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage(message) {
  const cleanMessage = message.trim();
  if (!cleanMessage) return;

  addMessage(cleanMessage, "user");
  messageInput.value = "";
  sendButton.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: cleanMessage })
    });

    if (!response.ok) throw new Error("Server returned an error.");

    const data = await response.json();
    (data.messages || ["Sorry, something went wrong."]).forEach(
      text => addMessage(text, "bot")
    );

    if (data.exit) {
      messageInput.disabled = true;
      document.querySelectorAll(".quick-prompts button").forEach(
        button => button.disabled = true
      );
    }
  } catch (error) {
    addMessage("Unable to connect to the chatbot. Please make sure the Python server is running and try again.", "bot");
  } finally {
    sendButton.disabled = false;
    if (!messageInput.disabled) messageInput.focus();
  }
}

chatForm.addEventListener("submit", event => {
  event.preventDefault();
  sendMessage(messageInput.value);
});

document.querySelectorAll(".quick-prompts button").forEach(button => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});
