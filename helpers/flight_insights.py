from serpapi import GoogleSearch
import matplotlib.pyplot as plt 
import numpy as np 
from datetime import datetime
plt.style.use('ggplot')
params = {
  "engine": "google_flights",
  "departure_id": "CDG",
  "arrival_id": "AUS",
  "outbound_date": "2025-05-28",
  "return_date": "2025-05-31",
  "currency": "EUR",
  "hl": "en",
  "api_key": os.environ['SERPAPI_API_KEY']
}

search = GoogleSearch(params)
results = search.get_dict()
price_insights = results["price_insights"]


start_date = datetime.strptime("2025-05-23", "%Y-%m-%d")
end_date = datetime.strptime("2025-05-26", "%Y-%m-%d")

x_axis = []
y_axis = []
for i in price_insights['price_history']:
    date_obj = datetime.utcfromtimestamp(i[0])
    if start_date <= date_obj <= end_date:
        x_axis.append(date_obj.strftime('%Y-%m-%d'))
        y_axis.append(i[1])

plt.plot(x_axis, y_axis, marker='o')
plt.xlabel('Date')
plt.ylabel('Price (Euro)')
plt.title('Flight Price History (Filtered)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
