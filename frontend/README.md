# Travel Agent Frontend (New)

A modern, ChatGPT-style frontend for the Travel Agent application.

## Features

- **ChatGPT-inspired UI**: Clean, modern interface with sidebar navigation and chat-based interaction
- **Dark/Light Theme**: Toggle between dark and light modes
- **Responsive Design**: Works on desktop and mobile devices
- **Rich Card Carousels**: Display flights, hotels, and restaurants in beautiful interactive cards
- **Smart Parsing**: Automatically extracts structured data from agent responses
- **Basket Management**: View your saved flights, hotels, and restaurants
- **Chat History**: Recent conversations saved locally
- **Markdown Support**: Formatted text responses with bold, lists, etc.

## Quick Start

### 1. Start the Backend API

First, make sure the backend API is running:

```bash
cd E:\PERSONAL_PROJ\ADTECH
python api.py
```

The API will start on `http://127.0.0.1:8000`.

### 2. Serve the Frontend

You can serve the frontend using any static file server. Here are a few options:

**Option A: Python HTTP Server**
```bash
cd new_fe
python -m http.server 3000
```

**Option B: Node.js http-server**
```bash
npm install -g http-server
cd new_fe
http-server -p 3000
```

**Option C: VS Code Live Server**
- Install the "Live Server" extension
- Right-click `index.html` and select "Open with Live Server"

### 3. Open in Browser

Navigate to `http://localhost:3000` in your browser.

## Usage

1. **Start a conversation**: Type a travel-related question in the input box
2. **Use suggestions**: Click on the suggestion chips for quick queries
3. **View results**: 
   - The AI response appears as formatted text
   - If flights/hotels/restaurants are found, they appear as card carousels below
4. **Manage basket**: Click the shopping bag icon to view saved items
5. **Toggle theme**: Click "Dark Mode" / "Light Mode" in the sidebar

## Example Queries

- "Find me flights from Istanbul to Paris"
- "Show me hotels in Paris for tonight"
- "Find restaurants in Soho"
- "Book a flight to London"

## Response Parsing

The frontend automatically parses agent responses to extract structured data:

### Flight Responses
Looks for:
- Price (e.g., `$450`)
- Airline name
- Duration (e.g., `5h 30m`)
- Stops (e.g., `1 stop`)

### Hotel Responses
Looks for:
- Hotel name
- Price per night
- Rating (e.g., `4.5 stars`)
- Hotel class (e.g., `4-star`)
- Location

### Restaurant Responses
Looks for:
- Restaurant name
- Price range (e.g., `$$$`)
- Rating (e.g., `4.8 stars`)
- Review count
- Cuisine type

**Note**: The parsing works best when agents return structured text. For even better results, consider modifying the backend to return JSON alongside the text response.

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Send a query to the travel agent |
| `/flights` | GET | Get flight search results |
| `/hotels` | GET | Get hotel search results |
| `/yelp` | GET | Get restaurant search results |
| `/basket` | GET | Get user's basket items |

## File Structure

```
new_fe/
├── index.html      # Main HTML file with layout
├── app.js          # JavaScript logic and API integration
└── README.md       # This file
```

## Technologies Used

- **Tailwind CSS**: Utility-first CSS framework via CDN
- **Material Icons**: Google Material Symbols for iconography
- **Vanilla JavaScript**: No framework dependencies
- **LocalStorage**: For theme preference and chat history

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Notes

- The frontend connects to the backend at `http://127.0.0.1:8000` by default
- CORS is enabled in the backend to allow frontend connections
- Chat history is stored locally in your browser
- Theme preference persists across sessions
- Images use Picsum placeholders (replace with real images in production)

## Troubleshooting

**No cards appearing?**
- Check browser console for errors
- Verify the backend is running at `http://127.0.0.1:8000`
- The parsing may not recognize the response format - check the agent output format

**CORS errors?**
- The backend already has CORS enabled (`allow_origins=["*"]`)
- Make sure you're accessing via `localhost` not a network IP

**Tool results not loading?**
- The `/flights`, `/hotels`, `/yelp` endpoints return 404 if no data exists yet
- This is expected - first make a query that triggers those agents
