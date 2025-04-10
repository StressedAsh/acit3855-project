const PROCESSING_STATS_API_URL =
  "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8100/stats";
const ANALYZER_API_URL = {
  stats: "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8110/stats",
  rainfall:
    "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8100/event1?index=0",
  flooding:
    "http://ec2-44-233-69-167.us-west-2.compute.amazonaws.com:8100/event2?index=0",
};

const makeReq = (url, cb) => {
  fetch(url)
    .then((res) => res.json())
    .then((result) => {
      console.log("Received data: ", result);
      cb(result);
    })
    .catch((error) => {
      updateErrorMessages(error.message);
    });
};

const updateCodeDiv = (result, elemId) =>
  (document.getElementById(elemId).innerText = JSON.stringify(result));

const getLocaleDateStr = () => new Date().toLocaleString();

const getStats = () => {
  document.getElementById("last-updated-value").innerText = getLocaleDateStr();

  makeReq(PROCESSING_STATS_API_URL, (result) =>
    updateCodeDiv(result, "processing-stats")
  );
  makeReq(ANALYZER_API_URL.stats, (result) =>
    updateCodeDiv(result, "analyzer-stats")
  );
  makeReq(ANALYZER_API_URL.rainfall, (result) =>
    updateCodeDiv(result, "event-rainfall")
  );
  makeReq(ANALYZER_API_URL.flooding, (result) =>
    updateCodeDiv(result, "event-flooding")
  );
};

const updateErrorMessages = (message) => {
  const id = Date.now();
  console.log("Creation", id);
  msg = document.createElement("div");
  msg.id = `error-${id}`;
  msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`;
  document.getElementById("messages").style.display = "block";
  document.getElementById("messages").prepend(msg);
  setTimeout(() => {
    const elem = document.getElementById(`error-${id}`);
    if (elem) {
      elem.remove();
    }
  }, 7000);
};

const setup = () => {
  getStats();
  setInterval(() => getStats(), 4000); // Update every 4 seconds
};

document.addEventListener("DOMContentLoaded", setup);
