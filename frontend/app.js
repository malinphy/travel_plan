// API Configuration
const API_BASE = "http://127.0.0.1:8001";

// Identify User and Thread
let userId = localStorage.getItem("travel_user_id");
if (!userId) {
    userId = "u_" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem("travel_user_id", userId);
}
let threadId = localStorage.getItem("travel_active_thread_id") || createThreadId();
localStorage.setItem("travel_active_thread_id", threadId);

// State
let chatHistory = [];
let basketItems = [];
let currentTheme = "light";

// Track how many carousel items we've already shown so we only add new ones
let shownCounts = { flights: 0, hotels: 0, yelp: 0 };

// DOM Elements
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const messagesContainer = document.getElementById("messagesContainer");
const welcomeMessage = document.getElementById("welcomeMessage");
const loadingIndicator = document.getElementById("loadingIndicator");
const chatContainer = document.getElementById("chatContainer");
const chatHistoryList = document.getElementById("chatHistoryList");
const basketModal = document.getElementById("basketModal");
const basketContent = document.getElementById("basketContent");
const basketBadge = document.getElementById("basketBadge");

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
    initTheme();
    checkInput();
    await initializeApp();
});

function createThreadId() {
    return "t_" + Math.random().toString(36).substr(2, 9);
}

function setActiveThread(nextThreadId) {
    threadId = nextThreadId;
    localStorage.setItem("travel_active_thread_id", threadId);
}

async function initializeApp() {
    await loadChatHistory();

    if (chatHistory.length === 0) {
        startNewChat(true);
        return;
    }

    const hasCurrentThread = chatHistory.some((chat) => chat.thread_id === threadId);
    if (!hasCurrentThread) {
        setActiveThread(chatHistory[0].thread_id);
    }

    try {
        await loadChat(threadId);
    } catch {
        startNewChat(true);
    }
}

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem("travel-agent-theme");
    if (savedTheme === "dark") {
        document.documentElement.classList.add("dark");
        currentTheme = "dark";
        updateThemeUI();
    }
}

function toggleTheme() {
    currentTheme = currentTheme === "light" ? "dark" : "light";
    if (currentTheme === "dark") {
        document.documentElement.classList.add("dark");
    } else {
        document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("travel-agent-theme", currentTheme);
    updateThemeUI();
}

function updateThemeUI() {
    const themeIcon = document.getElementById("themeIcon");
    const themeText = document.getElementById("themeText");
    if (currentTheme === "dark") {
        themeIcon.innerHTML = '<path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path><circle cx="12" cy="12" r="4"></circle>';
        themeText.textContent = "Light Mode";
    } else {
        themeIcon.innerHTML = '<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"></path>';
        themeText.textContent = "Dark Mode";
    }
}

// Input Handling
function checkInput() {
    messageInput.addEventListener("input", () => {
        const hasText = messageInput.value.trim().length > 0;
        sendBtn.disabled = !hasText;
    });
}

function autoResize(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 192) + "px";
}

function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        if (!sendBtn.disabled) {
            sendMessage();
        }
    }
}

function sendSuggestion(text) {
    messageInput.value = text;
    sendBtn.disabled = false;
    sendMessage();
}

// Message Handling
function sendMessage() {
    const query = messageInput.value.trim();
    if (!query) return;

    // Hide welcome message, show messages container
    welcomeMessage.classList.add("hidden");
    messagesContainer.classList.remove("hidden");

    // Add user message
    addMessage(query, "user");

    // Clear input
    messageInput.value = "";
    sendBtn.disabled = true;
    messageInput.style.height = "52px";

    // Show loading
    loadingIndicator.classList.remove("hidden");
    scrollToBottom();

    // Send to API
    sendQuery(query);
}

function addMessage(text, role, isHtml = false) {
    const div = document.createElement("div");
    div.className = "flex gap-4 message-animate";

    if (role === "user") {
        div.innerHTML = `
            <div class="flex-1 flex justify-end">
                <div class="bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-2xl rounded-tr-none max-w-[80%]">
                    <p class="text-sm">${escapeHtml(text)}</p>
                </div>
            </div>
        `;
    } else {
        // Format the text response with better markdown-like support
        const formattedText = formatTextResponse(text);
        div.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0110 0v4"></path><circle cx="9" cy="16" r="1" fill="currentColor"></circle><circle cx="15" cy="16" r="1" fill="currentColor"></circle></svg>
            </div>
            <div class="flex-1 space-y-3">
                <div class="text-gray-800 dark:text-gray-200 prose prose-sm dark:prose-invert max-w-none">
                    ${isHtml ? text : formattedText}
                </div>
            </div>
        `;
    }

    messagesContainer.appendChild(div);
    scrollToBottom();
}

function formatTextResponse(text) {
    if (!text) return "";

    let formatted = escapeHtml(text);

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Convert bullet points
    formatted = formatted.replace(/^[\-\*•]\s+(.+)$/gm, '<li>$1</li>');

    // Wrap consecutive <li> elements in <ul>
    formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="list-disc pl-4 my-2">$&</ul>');

    // Convert numbered lists
    formatted = formatted.replace(/^\d+\.\s+(.+)$/gm, '<li class="list-decimal">$1</li>');

    // Convert line breaks to paragraphs
    const paragraphs = formatted.split(/\n\n+/);
    formatted = paragraphs
        .map(p => p.trim())
        .filter(p => p && !p.startsWith('<ul>') && !p.startsWith('<li>'))
        .map(p => `<p class="mb-2">${p}</p>`)
        .join('');

    return formatted;
}

function addToolResponse(type, data) {
    const div = document.createElement("div");
    div.className = "message-animate w-full";

    const SVG_BOT = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0110 0v4"></path><circle cx="9" cy="16" r="1" fill="currentColor"></circle><circle cx="15" cy="16" r="1" fill="currentColor"></circle></svg>';
    const SVG_FLIGHT = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="none" class="text-white"><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>';
    const SVG_HOTEL = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>';
    const SVG_RESTAURANT = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><path d="M18 8h1a4 4 0 010 8h-1"></path><path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"></path><line x1="6" y1="1" x2="6" y2="4"></line><line x1="10" y1="1" x2="10" y2="4"></line><line x1="14" y1="1" x2="14" y2="4"></line></svg>';

    let iconSvg = SVG_BOT;
    let name = "Travel Agent";

    if (type === "flights") {
        iconSvg = SVG_FLIGHT;
        name = "FlightFinder";
    } else if (type === "hotels") {
        iconSvg = SVG_HOTEL;
        name = "HotelFinder";
    } else if (type === "restaurants") {
        iconSvg = SVG_RESTAURANT;
        name = "RestaurantFinder";
    }

    div.innerHTML = `
        <div class="w-full space-y-3">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                    ${iconSvg}
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-bold text-sm">${name}</span>
                    <span class="text-xs text-gray-400">• tool call</span>
                </div>
            </div>
            <div class="w-full">
                ${data}
            </div>
        </div>
    `;

    messagesContainer.appendChild(div);
    scrollToBottom();
}

// API Calls
async function sendQuery(query) {
    try {
        const res = await fetch(`${API_BASE}/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                query,
                user_id: userId,
                thread_id: threadId
            }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Request failed (${res.status})`);
        }

        const data = await res.json();

        // Hide loading
        loadingIndicator.classList.add("hidden");

        // Add bot response
        addMessage(data.response, "bot");

        // Fetch and display tool results
        await fetchToolResults();

        // Refresh persisted thread list after the thread is saved
        await loadChatHistory();

    } catch (error) {
        loadingIndicator.classList.add("hidden");
        addMessage(`Error: ${error.message}`, "bot");
    }
}

async function fetchToolResults() {
    const results = await Promise.allSettled([
        fetchToolResult("flights"),
        fetchToolResult("hotels"),
        fetchToolResult("yelp"),
    ]);

    const [flights, hotels, yelp] = results;

    if (flights.status === "fulfilled" && Array.isArray(flights.value)) {
        const newItems = flights.value.slice(shownCounts.flights);
        if (newItems.length > 0) {
            const html = renderFlights(newItems);
            if (html) addToolResponse("flights", html);
            shownCounts.flights = flights.value.length;
        }
    }

    if (hotels.status === "fulfilled" && Array.isArray(hotels.value)) {
        const newItems = hotels.value.slice(shownCounts.hotels);
        if (newItems.length > 0) {
            const html = renderHotels(newItems);
            if (html) addToolResponse("hotels", html);
            shownCounts.hotels = hotels.value.length;
        }
    }

    if (yelp.status === "fulfilled" && Array.isArray(yelp.value)) {
        const newItems = yelp.value.slice(shownCounts.yelp);
        if (newItems.length > 0) {
            const html = renderRestaurants(newItems);
            if (html) addToolResponse("restaurants", html);
            shownCounts.yelp = yelp.value.length;
        }
    }
}

async function fetchToolResult(type) {
    try {
        const res = await fetch(`${API_BASE}/${type}?user_id=${userId}&thread_id=${threadId}`);
        if (!res.ok) {
            return null;
        }
        const data = await res.json();
        return data.result;
    } catch {
        return null;
    }
}

async function getBasket(openModal = true) {
    try {
        const res = await fetch(`${API_BASE}/basket?user_id=${userId}&thread_id=${threadId}`);
        if (!res.ok) {
            return;
        }
        const data = await res.json();
        basketItems = data.items || [];
        displayBasket(basketItems);
        updateBasketBadge();
        if (openModal) {
            openBasketModal();
        }
    } catch (error) {
        console.error("Error fetching basket:", error);
    }
}

function updateBasketBadge() {
    if (basketItems.length > 0) {
        basketBadge.textContent = basketItems.length;
        basketBadge.classList.remove("hidden");
    } else {
        basketBadge.classList.add("hidden");
    }
}

function clearThreadView() {
    messagesContainer.innerHTML = "";
    welcomeMessage.classList.remove("hidden");
    messagesContainer.classList.add("hidden");
    shownCounts = { flights: 0, hotels: 0, yelp: 0 };
    basketItems = [];
    updateBasketBadge();
}

async function loadThreadToolResults() {
    shownCounts = { flights: 0, hotels: 0, yelp: 0 };
    await fetchToolResults();
}

async function loadChat(targetThreadId) {
    setActiveThread(targetThreadId);
    const res = await fetch(`${API_BASE}/threads/${encodeURIComponent(targetThreadId)}?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) {
        throw new Error("Unable to load thread");
    }

    const data = await res.json();
    const messages = Array.isArray(data.messages) ? data.messages : [];

    messagesContainer.innerHTML = "";

    if (messages.length === 0) {
        clearThreadView();
        renderChatHistory();
        return;
    }

    welcomeMessage.classList.add("hidden");
    messagesContainer.classList.remove("hidden");

    for (const message of messages) {
        addMessage(message.content, message.role === "assistant" ? "bot" : "user");
    }

    await loadThreadToolResults();
    await getBasket(false);
    renderChatHistory();
}

// Parsing and Rendering
function parseAndRenderFlights(text) {
    if (!text) return null;
    if (Array.isArray(text)) return renderFlights(text);
    if (typeof text !== "string") return null;

    const flights = [];

    // Pattern 1: Look for JSON-like structured data first
    const jsonMatch = text.match(/\[\s*\{[\s\S]*?\}\s*\]/);
    if (jsonMatch) {
        try {
            const data = JSON.parse(jsonMatch[0]);
            if (Array.isArray(data) && data.length > 0 && data[0].price !== undefined) {
                return renderFlights(data);
            }
        } catch (e) {
            // Continue to text parsing
        }
    }

    // Pattern 2: Parse structured text format (common LLM output)
    // Look for patterns like:
    // - Airline: XXX, Price: $XXX
    // - $XXX - Airline Name
    // - Flight: XXX at $XXX

    const lines = text.split("\n").filter(l => l.trim().length > 0);
    let currentFlight = null;

    for (const line of lines) {
        // Skip header/intro lines
        if (line.toLowerCase().includes("search_id") ||
            line.toLowerCase().includes("here are") ||
            line.toLowerCase().includes("found") && line.toLowerCase().includes("flight")) {
            continue;
        }

        // Try to extract price
        const priceMatch = line.match(/\$([0-9]{2,4}(?:,[0-9]{3})*(?:\.[0-9]{2})?)/);
        const airlineMatch = line.match(/(?:airline|carrier|flight)[:\s]+([A-Za-z\s]+?)(?:,|$|\.)/i);
        const durationMatch = line.match(/([0-9]+(?:h|m)+)/i);
        const stopsMatch = line.match(/([0-9])\s*stops?/i);

        // Check if this line contains flight info
        if (priceMatch && (airlineMatch || line.toLowerCase().includes("flight"))) {
            if (currentFlight) flights.push(currentFlight);
            currentFlight = {
                price: `$${priceMatch[1]}`,
                airline: airlineMatch ? airlineMatch[1].trim() : "Flight Option",
                duration: durationMatch ? durationMatch[1] : null,
                stops: stopsMatch ? `${stopsMatch[1]} stop${stopsMatch[1] !== '1' ? 's' : ''}` : "Non-stop",
            };
        } else if (currentFlight) {
            // Add additional info to current flight
            if (!currentFlight.duration && durationMatch) {
                currentFlight.duration = durationMatch[1];
            }
            if (!currentFlight.stops && stopsMatch) {
                currentFlight.stops = `${stopsMatch[1]} stop${stopsMatch[1] !== '1' ? 's' : ''}`;
            }
        }
    }

    if (currentFlight) flights.push(currentFlight);

    if (flights.length === 0) return null;

    return renderFlights(flights);
}

function parseAndRenderHotels(text) {
    if (!text) return null;
    if (Array.isArray(text)) return renderHotels(text);
    if (typeof text !== "string") return null;

    const hotels = [];

    // Pattern 1: Look for JSON-like structured data first
    const jsonMatch = text.match(/\[\s*\{[\s\S]*?\}\s*\]/);
    if (jsonMatch) {
        try {
            const data = JSON.parse(jsonMatch[0]);
            if (Array.isArray(data) && data.length > 0 && data[0].name !== undefined) {
                return renderHotels(data);
            }
        } catch (e) {
            // Continue to text parsing
        }
    }

    // Pattern 2: Parse structured text format
    const lines = text.split("\n").filter(l => l.trim().length > 0);
    let currentHotel = null;

    for (const line of lines) {
        // Skip header/intro lines and search_id references
        if (line.toLowerCase().includes("search_id") ||
            line.toLowerCase().includes("here are") ||
            line.toLowerCase().includes("found") && line.toLowerCase().includes("hotel")) {
            continue;
        }

        // Extract hotel info
        const priceMatch = line.match(/\$([0-9]{2,4}(?:,[0-9]{3})*(?:\.[0-9]{2})?)(?:\s*per night|\s*\/night)?/i);
        const ratingMatch = line.match(/([0-9](?:\.[0-9])?)\s*(?:stars?|rating|★|out of 5)/i);
        const classMatch = line.match(/([1-5])\s*(?:star|class)/i);
        const nameMatch = line.match(/^(?:[-•*]\s*)?([A-Z][A-Za-z\s&]+?)(?:\s*[-•|]|$)/);
        const locationMatch = line.match(/(?:location|area|in)[:\s]+([^\n,]+)/i);

        // Check if this line contains hotel info
        if ((priceMatch || nameMatch) && !line.toLowerCase().includes("search")) {
            if (currentHotel) hotels.push(currentHotel);
            currentHotel = {
                name: nameMatch ? nameMatch[1].trim() : (currentHotel?.name || "Hotel"),
                price: priceMatch ? `$${priceMatch[1]}` : (currentHotel?.price || "TBD"),
                rating: ratingMatch ? ratingMatch[1] : null,
                hotelClass: classMatch ? classMatch[1] : null,
                location: locationMatch ? locationMatch[1].trim() : null,
            };
        } else if (currentHotel) {
            // Add additional info
            if (!currentHotel.rating && ratingMatch) currentHotel.rating = ratingMatch[1];
            if (!currentHotel.hotelClass && classMatch) currentHotel.hotelClass = classMatch[1];
            if (!currentHotel.location && locationMatch) currentHotel.location = locationMatch[1].trim();
        }
    }

    if (currentHotel) hotels.push(currentHotel);

    if (hotels.length === 0) return null;

    return renderHotels(hotels);
}

function parseAndRenderRestaurants(text) {
    if (!text) return null;
    if (Array.isArray(text)) return renderRestaurants(text);
    if (typeof text !== "string") return null;

    const restaurants = [];

    // Pattern 1: Look for JSON-like structured data first
    const jsonMatch = text.match(/\[\s*\{[\s\S]*?\}\s*\]/);
    if (jsonMatch) {
        try {
            const data = JSON.parse(jsonMatch[0]);
            if (Array.isArray(data) && data.length > 0 && data[0].title !== undefined) {
                return renderRestaurants(data);
            }
        } catch (e) {
            // Continue to text parsing
        }
    }

    // Pattern 2: Parse structured text format (Yelp-style output)
    const lines = text.split("\n").filter(l => l.trim().length > 0);
    let currentRest = null;

    for (const line of lines) {
        // Skip header/intro lines
        if (line.toLowerCase().includes("search_id") ||
            line.toLowerCase().includes("here are") ||
            line.toLowerCase().includes("found") && line.toLowerCase().includes("restaurant")) {
            continue;
        }

        // Extract restaurant info
        // Common patterns: "Name - $$$ - 4.5 stars" or "Name | Cuisine | Price"
        const priceMatch = line.match(/(\$+\$?|\$\d+)/);
        const ratingMatch = line.match(/([0-9](?:\.[0-9])?)\s*(?:stars?|rating|★|out of 5)/i);
        const reviewsMatch = line.match(/([0-9,]+)\s*reviews?/i);

        // Name is usually at the start, followed by price/rating indicators
        const nameMatch = line.match(/^(?:[-•*]\s*)?([A-Z][A-Za-z\s&.,'-]+?)(?:\s*[-•|]|$|\s+\$)/);
        const cuisineMatch = line.match(/(?:cuisine|type|style|serves)[:\s]+([^\n,]+)/i);

        // Check if this looks like a restaurant line (has name + price or rating)
        if ((nameMatch || (priceMatch && ratingMatch)) && !line.toLowerCase().includes("search")) {
            if (currentRest) restaurants.push(currentRest);
            currentRest = {
                name: nameMatch ? nameMatch[1].trim() : (currentRest?.name || "Restaurant"),
                price: priceMatch ? priceMatch[0] : "$$",
                rating: ratingMatch ? ratingMatch[1] : null,
                reviews: reviewsMatch ? reviewsMatch[1] : null,
                cuisine: cuisineMatch ? cuisineMatch[1].trim() : null,
            };
        } else if (currentRest) {
            // Add additional info
            if (!currentRest.price && priceMatch) currentRest.price = priceMatch[0];
            if (!currentRest.rating && ratingMatch) currentRest.rating = ratingMatch[1];
            if (!currentRest.reviews && reviewsMatch) currentRest.reviews = reviewsMatch[1];
            if (!currentRest.cuisine && cuisineMatch) currentRest.cuisine = cuisineMatch[1].trim();
        }
    }

    if (currentRest) restaurants.push(currentRest);

    if (restaurants.length === 0) return null;

    return renderRestaurants(restaurants);
}

// Render Functions
function renderFlights(flights) {
    if (!flights || flights.length === 0) return null;

    const cards = flights.slice(0, 8).map((flight, idx) => {
        const image = flight.airline_logo || `https://picsum.photos/seed/flight${idx}/400/225`;
        const objectStyle = flight.airline_logo ? "object-contain bg-white dark:bg-gray-100 p-4" : "object-cover";
        return `
            <div class="flex-none w-72 bg-white dark:bg-gray-900 rounded-xl border border-border-light dark:border-border-dark overflow-hidden shadow-sm hover:shadow-md transition-shadow hotel-card">
                <div class="h-40 bg-gray-200 dark:bg-gray-800 relative flex items-center justify-center">
                    <img src="${image}" alt="Flight" class="w-full h-full ${objectStyle}" />
                    <div class="absolute top-2 right-2 bg-white/90 dark:bg-gray-900/90 backdrop-blur px-2 py-1 rounded-lg text-xs font-semibold text-primary">
                        ${flight.price || "TBD"}
                    </div>
                </div>
                <div class="p-4 space-y-2">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-gray-100">${escapeHtml(flight.primary_airline || flight.airline || "Flight")}</h3>
                        ${flight.duration ? `<p class="text-xs text-gray-500 dark:text-gray-400">${flight.duration} • ${flight.stops || "Non-stop"}</p>` : ''}
                    </div>
                    ${flight.is_best_flight ? '<span class="inline-block px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-xs rounded-full">Best Value</span>' : ''}
                </div>
            </div>
        `;
    }).join("");

    const showArrows = flights.length > 1;

    return `
        <div class="carousel-container group">
            <div class="carousel-track flex overflow-x-auto gap-4 pb-2 no-scrollbar" style="scrollbar-width: none; -ms-overflow-style: none;">
                ${cards}
            </div>
            ${showArrows ? `
                <button class="carousel-nav carousel-nav-left" onclick="scrollCarousel(this, -1)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                </button>
                <button class="carousel-nav carousel-nav-right" onclick="scrollCarousel(this, 1)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </button>
            ` : ''}
            ${flights.length > 1 ? `
                <div class="carousel-indicator flex justify-center gap-2 mt-3">
                    ${flights.map((_, i) => `<span class="w-2 h-2 rounded-full bg-gray-300 dark:bg-gray-600 carousel-dot" data-index="${i}"></span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

function scrollCarousel(button, direction) {
    const track = button.closest('.carousel-container').querySelector('.carousel-track');
    const scrollAmount = 300;
    track.scrollBy({
        left: direction * scrollAmount,
        behavior: 'smooth'
    });
}

// Update carousel dot indicators based on scroll position
function initCarouselIndicators() {
    document.querySelectorAll('.carousel-track').forEach(track => {
        const container = track.closest('.carousel-container');
        const dots = container.querySelectorAll('.carousel-dot');
        const cards = track.querySelectorAll('.carousel-container, .flex-none');

        if (dots.length === 0) return;

        const updateActiveDot = () => {
            const scrollLeft = track.scrollLeft;
            const cardWidth = 304; // 288px card + 16px gap
            const activeIndex = Math.round(scrollLeft / cardWidth);

            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === activeIndex);
            });
        };

        track.addEventListener('scroll', updateActiveDot);
        updateActiveDot();
    });
}

// Call this after messages are added
const originalAddToolResponse = addToolResponse;
addToolResponse = function (type, data) {
    originalAddToolResponse(type, data);
    setTimeout(() => initCarouselIndicators(), 100);
};

function renderHotels(hotels) {
    if (!hotels || hotels.length === 0) return null;

    const cards = hotels.slice(0, 8).map((hotel, idx) => {
        let image = `https://picsum.photos/seed/hotel${idx}/400/225`;
        let imgs = hotel.images;
        
        // Sometimes SQLite JSON columns return as strings in the API payload
        if (typeof imgs === 'string' && imgs.trim().startsWith('[')) {
            try {
                imgs = JSON.parse(imgs);
            } catch(e) {}
        }
        
        if (Array.isArray(imgs) && imgs.length > 0) {
            const imgData = imgs[0];
            image = typeof imgData === 'string' ? imgData : (imgData.original_image || imgData.thumbnail || image);
        }
        
        const rating = hotel.overall_rating || hotel.rating;
        const hotelClass = hotel.hotel_class || hotel.hotelClass;
        return `
            <div class="flex-none w-72 bg-white dark:bg-gray-900 rounded-xl border border-border-light dark:border-border-dark overflow-hidden shadow-sm hover:shadow-md transition-shadow hotel-card">
                <div class="h-40 bg-gray-200 dark:bg-gray-800 relative">
                    <img src="${image}" alt="${escapeHtml(hotel.name || 'Hotel')}" class="w-full h-full object-cover" />
                    <div class="absolute top-2 right-2 bg-white/90 dark:bg-gray-900/90 backdrop-blur px-2 py-1 rounded-lg text-xs font-semibold text-primary">
                        ${hotel.rate_per_night || hotel.price || "TBD"}
                    </div>
                </div>
                <div class="p-4 space-y-2">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-gray-100">${escapeHtml(hotel.name || "Hotel")}</h3>
                        <div class="flex items-center gap-1 mt-1">
                            ${rating ? `<span class="text-xs font-medium text-yellow-600 dark:text-yellow-400">★ ${rating}</span>` : ''}
                            ${hotelClass ? `<span class="text-xs text-gray-400">• ${hotelClass}★</span>` : ''}
                            ${hotel.reviews ? `<span class="text-xs text-gray-500">(${hotel.reviews})</span>` : ''}
                        </div>
                        ${hotel.location ? `<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${escapeHtml(hotel.location)}</p>` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join("");

    const showArrows = hotels.length > 1;

    return `
        <div class="carousel-container group">
            <div class="carousel-track flex overflow-x-auto gap-4 pb-2 no-scrollbar" style="scrollbar-width: none; -ms-overflow-style: none;">
                ${cards}
            </div>
            ${showArrows ? `
                <button class="carousel-nav carousel-nav-left" onclick="scrollCarousel(this, -1)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                </button>
                <button class="carousel-nav carousel-nav-right" onclick="scrollCarousel(this, 1)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </button>
            ` : ''}
            ${hotels.length > 1 ? `
                <div class="carousel-indicator flex justify-center gap-2 mt-3">
                    ${hotels.map((_, i) => `<span class="w-2 h-2 rounded-full bg-gray-300 dark:bg-gray-600 carousel-dot" data-index="${i}"></span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

function renderRestaurants(restaurants) {
    if (!restaurants || restaurants.length === 0) return null;

    const cards = restaurants.slice(0, 8).map((restaurant, idx) => {
        const image = restaurant.thumbnail || `https://picsum.photos/seed/restaurant${idx}/400/225`;
        const rating = restaurant.rating;
        const reviews = restaurant.reviews;
        return `
            <div class="flex-none w-72 bg-white dark:bg-gray-900 rounded-xl border border-border-light dark:border-border-dark overflow-hidden shadow-sm hover:shadow-md transition-shadow restaurant-card">
                <div class="h-40 bg-gray-200 dark:bg-gray-800 relative">
                    <img src="${image}" alt="${escapeHtml(restaurant.name || 'Restaurant')}" class="w-full h-full object-cover" />
                    <div class="absolute top-2 left-2 bg-white/90 dark:bg-gray-900/90 backdrop-blur px-2 py-1 rounded-lg text-xs font-semibold">
                        ${restaurant.price || "$$"}
                    </div>
                </div>
                <div class="p-4 space-y-2">
                    <div>
                        <h3 class="font-bold text-gray-900 dark:text-gray-100">${escapeHtml(restaurant.title || restaurant.name || "Restaurant")}</h3>
                        <div class="flex items-center gap-1 mt-1">
                            ${rating ? `<span class="text-xs font-medium text-yellow-600 dark:text-yellow-400">★ ${rating}</span>` : ''}
                            ${reviews ? `<span class="text-xs text-gray-500">(${reviews})</span>` : ''}
                            ${restaurant.cuisine ? `<span class="text-xs text-gray-400">• ${escapeHtml(restaurant.cuisine)}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    const showArrows = restaurants.length > 1;

    return `
        <div class="carousel-container group">
            <div class="carousel-track flex overflow-x-auto gap-4 pb-2 no-scrollbar" style="scrollbar-width: none; -ms-overflow-style: none;">
                ${cards}
            </div>
            ${showArrows ? `
                <button class="carousel-nav carousel-nav-left" onclick="scrollCarousel(this, -1)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                </button>
                <button class="carousel-nav carousel-nav-right" onclick="scrollCarousel(this, 1)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </button>
            ` : ''}
            ${restaurants.length > 1 ? `
                <div class="carousel-indicator flex justify-center gap-2 mt-3">
                    ${restaurants.map((_, i) => `<span class="w-2 h-2 rounded-full bg-gray-300 dark:bg-gray-600 carousel-dot" data-index="${i}"></span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// Chat History
async function loadChatHistory() {
    try {
        const res = await fetch(`${API_BASE}/threads?user_id=${encodeURIComponent(userId)}`);
        if (!res.ok) {
            chatHistory = [];
            renderChatHistory();
            return;
        }

        const data = await res.json();
        chatHistory = Array.isArray(data.threads) ? data.threads : [];
        renderChatHistory();
    } catch {
        chatHistory = [];
        renderChatHistory();
    }
}

function renderChatHistory() {
    if (chatHistory.length === 0) {
        chatHistoryList.innerHTML = '<p class="px-3 text-sm text-gray-400 italic">No recent chats</p>';
        return;
    }

    chatHistoryList.innerHTML = chatHistory.map((chat) => `
        <div onclick="loadChat('${chat.thread_id}')" class="flex items-center gap-3 px-3 py-2 rounded-lg ${chat.thread_id === threadId ? 'bg-gray-200 dark:bg-gray-800' : 'hover:bg-gray-200 dark:hover:bg-gray-800'} text-gray-700 dark:text-gray-300 cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"></path></svg>
            <span class="text-sm truncate flex-1">${escapeHtml(chat.title || "Untitled chat")}</span>
        </div>
    `).join("");
}

function startNewChat(skipHistoryRefresh = false) {
    setActiveThread(createThreadId());
    clearThreadView();
    messageInput.value = "";
    sendBtn.disabled = true;
    if (!skipHistoryRefresh) {
        renderChatHistory();
    }
}

// Basket Modal
function openBasketModal() {
    basketModal.classList.remove("hidden");
}

function closeBasketModal() {
    basketModal.classList.add("hidden");
}

function displayBasket(items) {
    if (!items || items.length === 0) {
        basketContent.innerHTML = `
            <div class="text-center py-12">
                <span class="material-symbols-outlined text-6xl text-gray-300 dark:text-gray-600">shopping_bag</span>
                <p class="mt-4 text-gray-500 dark:text-gray-400">Your basket is empty</p>
                <p class="text-sm text-gray-400 dark:text-gray-500">Add flights, hotels, or restaurants to your basket</p>
            </div>
        `;
        return;
    }

    basketContent.innerHTML = items.map((item) => {
        const summary = item.summary || {};
        let content = "";

        if (item.item_type === "flight") {
            content = `
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                        <span class="material-symbols-outlined text-blue-600 dark:text-blue-400">flight</span>
                    </div>
                    <div class="flex-1">
                        <p class="font-medium text-sm">${summary.airline || "Flight"}</p>
                        <p class="text-xs text-gray-500">${summary.trip_type || "One-way"}</p>
                    </div>
                    <span class="font-bold text-primary">${summary.price || "TBD"}</span>
                </div>
            `;
        } else if (item.item_type === "hotel") {
            content = `
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900 flex items-center justify-center">
                        <span class="material-symbols-outlined text-green-600 dark:text-green-400">hotel</span>
                    </div>
                    <div class="flex-1">
                        <p class="font-medium text-sm">${summary.name || "Hotel"}</p>
                        <p class="text-xs text-gray-500">${summary.hotel_class ? `${summary.hotel_class} ★` : ""}</p>
                    </div>
                    <span class="font-bold text-primary">${summary.rate_per_night || "TBD"}</span>
                </div>
            `;
        } else if (item.item_type === "restaurant") {
            content = `
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
                        <span class="material-symbols-outlined text-orange-600 dark:text-orange-400">restaurant</span>
                    </div>
                    <div class="flex-1">
                        <p class="font-medium text-sm">${summary.name || "Restaurant"}</p>
                        <p class="text-xs text-gray-500">${summary.rating ? `${summary.rating} ★` : ""}</p>
                    </div>
                    <span class="font-bold text-primary">${summary.price || "$$"}</span>
                </div>
            `;
        }

        return `
            <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-border-light dark:border-border-dark">
                ${content}
            </div>
        `;
    }).join("");
}

// Utilities
function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);
}

function toggleSidebar() {
    const sidebar = document.querySelector("aside");
    sidebar.classList.toggle("hidden");
    sidebar.classList.toggle("absolute");
    sidebar.classList.toggle("z-50");
    sidebar.classList.toggle("h-full");
}
