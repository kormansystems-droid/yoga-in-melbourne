// netlify/functions/contact.js
// Typed-intent inbound contact handler.
// Receives { intent, name, email, org, links, message, website } where
// `website` is a honeypot (real users never fill it).
//
// Does two things, in order of importance:
//   1. Emails the submission to CONTACT_TO via Brevo transactional (BREVO_API_KEY reused).
//   2. Logs a row to Supabase table `inbound` (status 'new') — the pipeline record.
// Either leg failing alone does not fail the submission; both failing does.
//
// Netlify env vars required:
//   BREVO_API_KEY        (already set for follow.js)
//   CONTACT_TO           e.g. hello@yogainmelbourne.com.au
//   CONTACT_FROM         a Brevo-validated sender, e.g. hello@yogainmelbourne.com.au
//   SUPABASE_URL         https://<project-ref>.supabase.co
//   SUPABASE_SERVICE_KEY service-role key (server-side only — never in client code)

export async function handler(event) {
  if (event.httpMethod !== "POST") return { statusCode: 405, body: "Method not allowed" };

  let d;
  try { d = JSON.parse(event.body || "{}"); }
  catch { return { statusCode: 400, body: "Bad request" }; }

  if ((d.website || "").trim() !== "") {           // honeypot tripped — pretend success
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  }

  const intent = ["feature", "correction", "general"].includes(d.intent) ? d.intent : "general";
  const name = (d.name || "").trim().slice(0, 200);
  const email = (d.email || "").trim().toLowerCase().slice(0, 200);
  const org = (d.org || "").trim().slice(0, 300);
  const links = (d.links || "").trim().slice(0, 500);
  const message = (d.message || "").trim().slice(0, 5000);

  if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email))
    return { statusCode: 422, body: JSON.stringify({ error: "Valid email required." }) };
  if (!message && intent !== "feature")
    return { statusCode: 422, body: JSON.stringify({ error: "A message is required." }) };

  const results = { mail: false, log: false };

  // --- 1. Email to the editor ---
  const API_KEY = process.env.BREVO_API_KEY, TO = process.env.CONTACT_TO, FROM = process.env.CONTACT_FROM;
  if (API_KEY && TO && FROM) {
    const label = { feature: "FEATURE REQUEST", correction: "CORRECTION", general: "CONTACT" }[intent];
    const lines = [
      `Intent: ${intent}`, `Name: ${name}`, `Email: ${email}`,
      org ? `Teacher/Studio: ${org}` : null, links ? `Links: ${links}` : null,
      "", message,
    ].filter(x => x !== null).join("\n");
    try {
      const r = await fetch("https://api.brevo.com/v3/smtp/email", {
        method: "POST",
        headers: { "api-key": API_KEY, "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          sender: { email: FROM, name: "Yoga in Melbourne" },
          to: [{ email: TO }],
          replyTo: { email, name: name || email },
          subject: `[YIM ${label}] ${name || email}${org ? " — " + org : ""}`,
          textContent: lines,
        }),
      });
      results.mail = r.status === 201;
    } catch { /* fall through to log */ }
  }

  // --- 2. Supabase pipeline row ---
  const SB_URL = process.env.SUPABASE_URL, SB_KEY = process.env.SUPABASE_SERVICE_KEY;
  if (SB_URL && SB_KEY) {
    const row = JSON.stringify({ intent, name, email, org, links, message, status: "new" });
    // New-style sb_secret keys authenticate via the apikey header alone;
    // legacy JWT keys want Authorization: Bearer too. Try apikey-only first,
    // fall back to Bearer so either key style works.
    const attempts = [
      { apikey: SB_KEY, "Content-Type": "application/json", Prefer: "return=minimal" },
      { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}`, "Content-Type": "application/json", Prefer: "return=minimal" },
    ];
    for (const headers of attempts) {
      try {
        const r = await fetch(`${SB_URL}/rest/v1/inbound`, { method: "POST", headers, body: row });
        if (r.status === 201) { results.log = true; break; }
        console.log("supabase insert failed", r.status, (await r.text()).slice(0, 200));
      } catch (e) { console.log("supabase insert error", String(e).slice(0, 200)); }
    }
  }

  if (results.mail || results.log) return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  return { statusCode: 502, body: JSON.stringify({ error: "Could not record your message. Please email hello@yogainmelbourne.com.au directly." }) };
}
