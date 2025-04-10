// Define the API URLs properly
const API_URLS = {
  processingStats:
    "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8100/stats",
  analyzerStats:
    "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8110/stats",
  rainfallEvent:
    "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8110/event1?index=0",
  floodingEvent:
    "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8110/event2?index=0",
};

// Generic fetch function
const fetchData = async (url) => {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    console.log(`Fetched from ${url}:`, data);
    return data;
  } catch (error) {
    console.error(`Error fetching from ${url}:`, error);
    showError(error.message);
    return null;
  }
};

// Update the displayed data in the dashboard
const updateDashboard = async () => {
  updateLastUpdated();

  // Processing stats
  const processingStats = await fetchData(API_URLS.processingStats);
  if (processingStats) {
    document.getElementById("processing-stats").innerText = JSON.stringify(
      processingStats,
      null,
      2
    );
  }

  // Analyzer stats
  const analyzerStats = await fetchData(API_URLS.analyzerStats);
  if (analyzerStats) {
    document.getElementById("analyzer-stats").innerText = JSON.stringify(
      analyzerStats,
      null,
      2
    );
  }

  // Random Rainfall event
  const rainfallEvent = await fetchData(API_URLS.rainfallEvent);
  if (rainfallEvent) {
    document.getElementById("event-rainfall").innerText = JSON.stringify(
      rainfallEvent,
      null,
      2
    );
  }

  // Random Flooding event
  const floodingEvent = await fetchData(API_URLS.floodingEvent);
  if (floodingEvent) {
    document.getElementById("event-flooding").innerText = JSON.stringify(
      floodingEvent,
      null,
      2
    );
  }
};

// Update last updated timestamp
const updateLastUpdated = () => {
  const now = new Date().toLocaleString();
  document.getElementById("last-updated-value").innerText = now;
};

// Show error messages dynamically
const showError = (message) => {
  const id = `error-${Date.now()}`;
  const container = document.getElementById("messages");

  const errorDiv = document.createElement("div");
  errorDiv.id = id;
  errorDiv.innerHTML = `<p><strong>Error at ${new Date().toLocaleString()}:</strong> ${message}</p>`;

  container.style.display = "block";
  container.prepend(errorDiv);

  // Auto-remove after 7 seconds
  setTimeout(() => {
    const elem = document.getElementById(id);
    if (elem) elem.remove();
  }, 7000);
};

// Set up auto-refresh
const setupDashboard = () => {
  updateDashboard();
  setInterval(updateDashboard, 4000); // Refresh every 4 seconds
};

// Wait until DOM is fully loaded
document.addEventListener("DOMContentLoaded", setupDashboard);
