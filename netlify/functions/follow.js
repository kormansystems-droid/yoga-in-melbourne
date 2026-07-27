// netlify/functions/follow.js
// Teacher-agnostic follow handler. Stores followers in Supabase — the list
// stays with YIM (per the privacy policy), one datastore alongside members
// and inbound. Receives { name, email, teacher }.
//
// Table: public.followers (see followers-table.sql). One row per
// (email, teacher) pair — following a second teacher adds a second row;
// re-following the same teacher is a no-op, never an error.
//
// Netlify env vars (already set): SUPABASE_URL, SUPABASE_SERVICE_KEY.

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

  const name = (data.name || "").trim().slice(0, 200);
  const email = (data.email || "").trim().toLowerCase().slice(0, 200);
  const teacher = (data.teacher || "").trim().slice(0, 200);

  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return { statusCode: 422, body: JSON.stringify({ error: "Valid email required." }) };
  }

  const SB_URL = process.env.SUPABASE_URL;
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;
  if (!SB_URL || !SB_KEY) {
    return { statusCode: 500, body: JSON.stringify({ error: "Server not configured." }) };
  }

  try {
    // Upsert on (email, teacher): merge-duplicates makes a repeat follow a no-op.
    const res = await fetch(`${SB_URL}/rest/v1/followers?on_conflict=email,teacher`, {
      method: "POST",
      headers: {
        apikey: SB_KEY,
        Authorization: `Bearer ${SB_KEY}`,
        "Content-Type": "application/json",
        Prefer: "resolution=merge-duplicates,return=minimal",
      },
      body: JSON.stringify({ name, email, teacher }),
    });
    if (res.status === 201 || res.status === 200 || res.status === 204) {
      return { statusCode: 200, body: JSON.stringify({ ok: true }) };
    }
    const detail = await res.text();
    return { statusCode: 502, body: JSON.stringify({ error: "Store error", detail: detail.slice(0, 300) }) };
  } catch {
    return { statusCode: 502, body: JSON.stringify({ error: "Network error" }) };
  }
}
