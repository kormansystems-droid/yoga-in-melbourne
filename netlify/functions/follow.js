// netlify/functions/follow.js
// Teacher-agnostic follow handler. Reusable across ALL teacher pages.
// Receives { name, email, teacher } and upserts the contact into a single
// Brevo "Followers" list, tagging which teacher(s) they follow.
//
// Setup required (once):
//   - Netlify env var BREVO_API_KEY  (your Brevo API v3 key)
//   - Netlify env var BREVO_LIST_ID  (numeric id of your "Followers" list)
// No per-teacher code changes needed — the teacher is read from the request.

export async function handler(event) {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method not allowed" };
  }

  let data;
  try {
    data = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: "Bad request" };
  }

  const name = (data.name || "").trim();
  const email = (data.email || "").trim().toLowerCase();
  const teacher = (data.teacher || "").trim();

  // Basic validation
  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return { statusCode: 422, body: JSON.stringify({ error: "Valid email required." }) };
  }

  const API_KEY = process.env.BREVO_API_KEY;
  const LIST_ID = Number(process.env.BREVO_LIST_ID);
  if (!API_KEY || !LIST_ID) {
    return { statusCode: 500, body: JSON.stringify({ error: "Server not configured." }) };
  }

  // Split a single name field into first/last for Brevo attributes
  const [firstName, ...rest] = name.split(" ");
  const lastName = rest.join(" ");

  // Brevo "create or update contact" — updateEnabled:true makes it an upsert,
  // so an existing follower simply gains the new teacher tag rather than erroring.
  const payload = {
    email,
    updateEnabled: true,
    listIds: [LIST_ID],
    attributes: {
      FIRSTNAME: firstName || "",
      LASTNAME: lastName || "",
      // FOLLOWS is a comma-separated list of teacher slugs/names.
      // Brevo overwrites the attribute, so to truly append across multiple
      // follows you'd read-then-merge; for v1 we store the latest teacher.
      FOLLOWS: teacher || "",
    },
  };

  try {
    const res = await fetch("https://api.brevo.com/v3/contacts", {
      method: "POST",
      headers: {
        "api-key": API_KEY,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (res.status === 201 || res.status === 204) {
      return { statusCode: 200, body: JSON.stringify({ ok: true }) };
    }
    // 400 "Contact already exists" is benign with updateEnabled, but surface others.
    const detail = await res.text();
    return { statusCode: 502, body: JSON.stringify({ error: "Brevo error", detail }) };
  } catch (err) {
    return { statusCode: 502, body: JSON.stringify({ error: "Network error" }) };
  }
}
