// Waits until the Django development server answers, then exits.
//
// `make dev` starts Django and Vite together. Vite is ready first, so a page opened in that
// first second would reach the API before it is up, and the Vite proxy would log a connection
// error. Procfile.dev runs this script before Vite to start the two in order.
const url = process.env.FABRISEE_API_HEALTH_URL ?? "http://127.0.0.1:8000/api/health/";
const deadline = Date.now() + 60_000;

while (Date.now() < deadline) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1500) });
    if (response.ok) process.exit(0);
  } catch {
    // Not up yet: try again.
  }
  await new Promise((resolve) => setTimeout(resolve, 250));
}

console.warn("The API did not answer within 60 seconds. Starting the frontend anyway.");
