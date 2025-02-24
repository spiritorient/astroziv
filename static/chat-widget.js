(function () {
    document.head.insertAdjacentHTML('beforeend', '<link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.16/tailwind.min.css" rel="stylesheet">');
  
    const style = document.createElement('style');
    style.innerHTML = `
      .hidden { display: none; }
      #chat-widget-container { position: fixed; bottom: 40px; right: 30px; flex-direction: column; }
      .chatbot__arrow--left { border-top: 6px solid transparent; border-bottom: 6px solid transparent; border-right: 6px solid #f0f0f0; }
      .chatbot__arrow { width: 0; height: 0; margin-top: 18px; }
      .chatbot__arrow--right { border-top: 6px solid transparent; border-bottom: 6px solid transparent; border-left: 6px solid #1a181e; }
      #chat-popup { height: 70vh; max-height: 70vh; transition: all 0.3s; overflow: hidden; position:relative; }
      .content-loader { display: none; padding: 12px 20px; position: absolute; z-index: 1; right: 50px; bottom: 100px; }
      .typing-loader::after { color: #ffdead; content: "ASTROŽIV™ is typing....."; animation: typing 2.639s steps(1) infinite, blink .75s step-end infinite; font-size:10px; }
      @keyframes typing { from,to { width: 0; } 50% { width: 15px; } }
      @keyframes blink { 50% { color: transparent; } }
      @media (max-width: 768px) { #chat-popup { position: fixed; top: 0; right: 0; bottom: 0; left: 0; width: 100%; height: 100%; max-height: 100%; border-radius: 0; } }
      .icon {
        width: 125px;
        height: 125px;
        background-image: url('/static/astrzicon.png'); /* Adjusted for Flask static serving */
        background-size: cover;
        background-position: center;
      }
    `;
    document.head.appendChild(style);
  
    const chatWidgetContainer = document.createElement('div');
    chatWidgetContainer.id = 'chat-widget-container';
    document.body.appendChild(chatWidgetContainer);
  
    chatWidgetContainer.innerHTML = `
      <div id="chat-bubble" class="w-32 h-32 rounded-full flex items-center justify-center cursor-pointer text-3xl">
        <div class="icon"></div>
      </div>
      <div id="chat-popup" class="hidden bg-gray-900 border border-purple-800 absolute bottom-20 right-0 w-96 rounded-md shadow-md flex flex-col transition-all text-sm">
        <div id="chat-header" class="flex justify-between items-center p-4 bg-gray-900 text-white border border-purple-800 rounded-md">
          <h3 class="m-0 text-lg">| assistant·ASTROŽIV·AI |</h3>
          <button id="close-popup" class="bg-transparent border-none text-white cursor-pointer">✕</button>
        </div>
        <div class="content-loader"><div class="typing-loader"></div></div>
        <div id="chat-messages" class="flex-1 p-4 overflow-y-auto"></div>
        <div id="chat-input-container" class="p-4 border-t border-purple-200">
          <div class="flex space-x-4 items-center">
            <input type="text" id="chat-input" class="flex-1 rounded-md px-4 py-2 outline-none w-3/4" placeholder="Message ASTROŽIV™">
            <button id="chat-submit" class="bg-gray-800 text-white rounded-md px-4 py-2 cursor-pointer">Send</button>
          </div>
        </div>
      </div>`;
  
    const chatInput = document.getElementById('chat-input');
    const chatSubmit = document.getElementById('chat-submit');
    const chatBubble = document.getElementById('chat-bubble');
    const chatPopup = document.getElementById('chat-popup');
    const chatMessages = document.getElementById('chat-messages');
    const loader = document.querySelector('.content-loader');
    const closePopup = document.getElementById('close-popup');
  
    let threadId = null;
    let ASSISTANT_ID = null;
  
    // Fetch assistant ID from Flask config endpoint
    async function fetchConfig() {
      try {
        const response = await fetch('/config'); // Relative path for Flask
        if (!response.ok) throw new Error("Failed to fetch config");
        const data = await response.json();
        ASSISTANT_ID = data.assistant_id;
        console.log("·· Welcome to the ASTROŽIV™ Traveler ··");
      } catch (error) {
        console.error("Error fetching config:", error);
      }
    }
  
    // Send message to Flask backend and get response
    async function sendMessage(message) {
      try {
        const response = await fetch('/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message,
            thread_id: threadId, // Maintain conversation continuity
          }),
        });
        if (!response.ok) throw new Error("Failed to send message");
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        threadId = data.thread_id; // Update thread ID
        return data.reply;
      } catch (error) {
        console.error("Error in chat request:", error);
        return "Sorry, something went wrong.";
      }
    }
  
    // Handle user message request
    async function onUserRequest(message) {
      if (!message.trim()) return;
      chatMessages.innerHTML += `<div class='flex justify-end mb-3'><div class='bg-gray-900 text-gray-300 rounded-lg py-2 px-4 max-w-[70%]'>${message}</div></div>`;
      chatMessages.scrollTop = chatMessages.scrollHeight;
      chatInput.value = '';
      loader.style.display = 'inline-block';
  
      const replyMessage = await sendMessage(message);
  
      loader.style.display = 'none';
      chatMessages.innerHTML += `<div class='flex mb-3'><div class='bg-gray-900 text-gray-200 rounded-lg py-2 px-4 max-w-[70%]'>${replyMessage}</div></div>`;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  
    // Event Listeners
    chatSubmit.addEventListener('click', () => onUserRequest(chatInput.value));
    chatInput.addEventListener('keyup', event => { if (event.key === 'Enter') chatSubmit.click(); });
    chatBubble.addEventListener('click', () => chatPopup.classList.toggle('hidden'));
    closePopup.addEventListener('click', () => chatPopup.classList.toggle('hidden'));
  
    // Initialize config on load
    fetchConfig();
  })();