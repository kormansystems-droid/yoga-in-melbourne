/* Yoga in Melbourne — Join the Community
 * One self-contained script. Load it (after the Supabase CDN) on any page and it will:
 *   - inject a "Join the Community" button top-right into the masthead
 *   - render a passwordless sign-up popup (email + explicit consent checkbox)
 *   - send a magic link, and on return record the consent against the account
 *
 * Setup (once):
 *   1. Create a Supabase project, run supabase-schema.sql in its SQL editor.
 *   2. Fill CONFIG below with your project URL + anon (public) key.
 *      The anon key is safe to expose in the page — it is protected by Row-Level Security.
 *   3. In Supabase → Authentication → URL Configuration, add your site URL(s) to
 *      "Redirect URLs" (e.g. https://yogainmelbourne.com.au/* ).
 *
 * Page needs, before </body>:
 *   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
 *   <script src="/community.js"></script>
 */
(function () {
  "use strict";

  var CONFIG = {
    SUPABASE_URL: "https://yxqtvczqbbylgqjhnapd.supabase.co",
    SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl4cXR2Y3pxYmJ5bGdxamhuYXBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMzNDEzNTIsImV4cCI6MjA5ODkxNzM1Mn0.JMixlVhanCJPrbskC_2SXN3LA7t9uDWPs8OCRcsQRU4"
  };

  // Guard: don't ship a broken button before the project is configured.
  if (!window.supabase || CONFIG.SUPABASE_URL.indexOf("REPLACE_") === 0) {
    console.warn("[community] Supabase not configured yet — button not rendered.");
    return;
  }

  var sb = window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

  // ---------- styles (self-contained; uses site vars with on-brand fallbacks) ----------
  var css = `
  .yim-join{font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:11.5px;
    letter-spacing:.06em;text-transform:uppercase;color:var(--henna,#a24b34);
    background:transparent;border:1px solid var(--henna,#a24b34);padding:8px 15px;
    cursor:pointer;white-space:nowrap;line-height:1;border-radius:2px;transition:background .2s,color .2s}
  .yim-join:hover{background:var(--henna,#a24b34);color:var(--paper,#faf6ef)}
  .yim-overlay{position:fixed;inset:0;background:rgba(20,14,10,.55);display:none;
    align-items:center;justify-content:center;z-index:9999;padding:20px}
  .yim-overlay.open{display:flex}
  .yim-modal{background:var(--paper,#faf6ef);color:var(--ink,#2a201a);max-width:420px;width:100%;
    border-radius:6px;padding:32px 30px;box-shadow:0 20px 60px rgba(0,0,0,.3);position:relative;
    font-family:'Hanken Grotesk',system-ui,sans-serif}
  .yim-modal h2{font-family:'Fraunces',Georgia,serif;font-weight:500;font-size:28px;
    line-height:1.05;margin:0 0 8px}
  .yim-modal p.sub{color:var(--ink-soft,#6b5d50);font-size:15px;line-height:1.45;margin:0 0 22px}
  .yim-field{width:100%;box-sizing:border-box;padding:12px 14px;margin-bottom:12px;font-size:15px;
    border:1px solid rgba(42,32,26,.25);border-radius:4px;background:#fff;font-family:inherit}
  .yim-consent{display:flex;gap:10px;align-items:flex-start;font-size:13px;line-height:1.4;
    color:var(--ink-soft,#6b5d50);margin:4px 0 20px;cursor:pointer}
  .yim-consent input{margin-top:2px;flex:0 0 auto}
  .yim-submit{width:100%;font-family:'Spline Sans Mono',monospace;font-size:12px;letter-spacing:.06em;
    text-transform:uppercase;color:var(--paper,#faf6ef);background:var(--henna,#a24b34);
    border:1px solid var(--henna,#a24b34);padding:13px;cursor:pointer;border-radius:3px}
  .yim-submit:disabled{opacity:.5;cursor:default}
  .yim-close{position:absolute;top:14px;right:16px;background:none;border:none;font-size:22px;
    line-height:1;color:var(--ink-soft,#6b5d50);cursor:pointer}
  .yim-msg{font-size:14px;line-height:1.5;color:var(--ink,#2a201a);margin-top:4px}
  .yim-err{color:#b3261e;font-size:13px;margin:-6px 0 12px;min-height:1em}
  .yim-fineprint{font-size:11px;color:var(--ink-soft,#6b5d50);margin-top:16px;line-height:1.4}
  .yim-auth{display:flex;align-items:center;gap:16px;margin-left:auto}
  .yim-login{font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--sage,#7a8a6f);background:none;border:none;cursor:pointer;padding:0;white-space:nowrap}
  .yim-login:hover{color:var(--henna,#a24b34)}
  .yim-switch{margin-top:16px;font-size:13px;color:var(--ink-soft,#6b5d50)}
  .yim-switch a{color:var(--henna,#a24b34);cursor:pointer;text-decoration:underline}
  `;
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // ---------- auth buttons (Log in + Join, grouped and pinned right) ----------
  var loginBtn = document.createElement("button");
  loginBtn.className = "yim-login";
  loginBtn.type = "button";
  loginBtn.textContent = "Log in";

  var btn = document.createElement("button");
  btn.className = "yim-join";
  btn.type = "button";
  btn.textContent = "Join the Community";

  var authWrap = document.createElement("div");
  authWrap.className = "yim-auth";
  authWrap.appendChild(loginBtn);
  authWrap.appendChild(btn);

  var mast = document.querySelector(".masthead") || document.querySelector(".topbar-inner") || document.querySelector("header");
  if (mast) {
    mast.style.display = mast.style.display || "flex";
    mast.style.alignItems = mast.style.alignItems || "center";
    mast.appendChild(authWrap);
  } else {
    authWrap.style.cssText = "position:fixed;top:14px;right:16px;z-index:9998";
    document.body.appendChild(authWrap);
  }

  // ---------- modal ----------
  var overlay = document.createElement("div");
  overlay.className = "yim-overlay";
  overlay.innerHTML =
    '<div class="yim-modal" role="dialog" aria-modal="true" aria-label="Join the Community">' +
      '<button class="yim-close" aria-label="Close">&times;</button>' +
      '<div class="yim-body"></div>' +
    '</div>';
  document.body.appendChild(overlay);
  var body = overlay.querySelector(".yim-body");

  function close() { overlay.classList.remove("open"); }
  overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
  overlay.querySelector(".yim-close").addEventListener("click", close);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });

  function renderSignup() {
    body.innerHTML =
      '<h2>Join the Community</h2>' +
      '<p class="sub">Follow your favourite teachers and studios, and keep up with Melbourne yoga. No password — we\u2019ll email you a link.</p>' +
      '<input class="yim-field" id="yim-name" type="text" placeholder="Your name (optional)" autocomplete="name">' +
      '<input class="yim-field" id="yim-email" type="email" placeholder="Email address" autocomplete="email" required>' +
      '<div class="yim-err" id="yim-err"></div>' +
      '<label class="yim-consent"><input type="checkbox" id="yim-consent">' +
        '<span>Yes, email me updates from Yoga in Melbourne. I can unsubscribe anytime.</span></label>' +
      '<button class="yim-submit" id="yim-submit">Send me a link</button>' +
      '<p class="yim-fineprint">We only use your email to send what you asked for. See our privacy policy.</p>' +
      '<p class="yim-switch">Already joined? <a id="yim-to-login">Log in</a></p>';

    body.querySelector("#yim-to-login").addEventListener("click", renderLogin);
    var submit = body.querySelector("#yim-submit");
    submit.addEventListener("click", function () {
      var email = body.querySelector("#yim-email").value.trim().toLowerCase();
      var name = body.querySelector("#yim-name").value.trim();
      var consent = body.querySelector("#yim-consent").checked;
      var err = body.querySelector("#yim-err");
      err.textContent = "";
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { err.textContent = "Please enter a valid email."; return; }

      submit.disabled = true; submit.textContent = "Sending\u2026";
      sb.auth.signInWithOtp({
        email: email,
        options: {
          emailRedirectTo: location.origin + location.pathname,
          data: {
            full_name: name,
            email_consent: consent,
            consent_at: new Date().toISOString(),
            consent_source: "join-community-popup"
          }
        }
      }).then(function (res) {
        if (res.error) { err.textContent = res.error.message || "Something went wrong."; submit.disabled = false; submit.textContent = "Send me a link"; return; }
        body.innerHTML = '<h2>You\u2019re in \u2713</h2><p class="yim-msg">Welcome to the community. We\u2019ve emailed <strong>' +
          email.replace(/</g, "&lt;") + '</strong> a confirmation link \u2014 <strong>tap it to confirm your email and sign in</strong>. You can do that whenever you\u2019re ready.</p>';
      });
    });
  }

  function renderMember(user) {
    var label = (user.user_metadata && user.user_metadata.full_name) || user.email;
    body.innerHTML =
      '<h2>You\u2019re in \u2713</h2>' +
      '<p class="yim-msg">Signed in as <strong>' + String(label).replace(/</g, "&lt;") + '</strong>.<br>' +
      'Follow buttons on teacher and studio pages will now save to your account.</p>' +
      '<button class="yim-submit" id="yim-signout" style="margin-top:18px">Sign out</button>';
    body.querySelector("#yim-signout").addEventListener("click", function () {
      sb.auth.signOut().then(function () { close(); updateButton(null); });
    });
  }

  function renderLogin() {
    body.innerHTML =
      '<h2>Welcome back</h2>' +
      '<p class="sub">Enter your email and we\u2019ll send a link to sign in. No password needed.</p>' +
      '<input class="yim-field" id="yim-login-email" type="email" placeholder="Email address" autocomplete="email" required>' +
      '<div class="yim-err" id="yim-login-err"></div>' +
      '<button class="yim-submit" id="yim-login-submit">Send me a login link</button>' +
      '<p class="yim-switch">New here? <a id="yim-to-join">Join the community</a></p>';
    body.querySelector("#yim-to-join").addEventListener("click", renderSignup);
    var lsubmit = body.querySelector("#yim-login-submit");
    lsubmit.addEventListener("click", function () {
      var email = body.querySelector("#yim-login-email").value.trim().toLowerCase();
      var err = body.querySelector("#yim-login-err");
      err.textContent = "";
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { err.textContent = "Please enter a valid email."; return; }
      lsubmit.disabled = true; lsubmit.textContent = "Sending\u2026";
      sb.auth.signInWithOtp({
        email: email,
        options: { emailRedirectTo: location.origin + location.pathname, shouldCreateUser: false }
      }).then(function (res) {
        if (res.error) {
          err.textContent = /signup|not\s*found|not\s*allowed/i.test(res.error.message || "")
            ? "We couldn\u2019t find an account for that email \u2014 try joining the community instead."
            : (res.error.message || "Something went wrong.");
          lsubmit.disabled = false; lsubmit.textContent = "Send me a login link"; return;
        }
        body.innerHTML = '<h2>Check your email</h2><p class="yim-msg">We\u2019ve sent a sign-in link to <strong>' +
          email.replace(/</g, "&lt;") + '</strong>. Tap it to sign in.</p>';
      });
    });
  }

  btn.addEventListener("click", function () {
    sb.auth.getUser().then(function (res) {
      var user = res.data && res.data.user;
      if (user) renderMember(user); else renderSignup();
      overlay.classList.add("open");
    });
  });

  loginBtn.addEventListener("click", function () { renderLogin(); overlay.classList.add("open"); });

  function updateButton(user) {
    if (user) {
      var name = (user.user_metadata && user.user_metadata.full_name) || "My Community";
      btn.textContent = name.split(" ")[0] || "My Community";
      loginBtn.style.display = "none";
    } else {
      btn.textContent = "Join the Community";
      loginBtn.style.display = "";
    }
  }

  // On sign-in (incl. returning via magic link): record consent, refresh button.
  sb.auth.onAuthStateChange(function (event, session) {
    var user = session && session.user;
    updateButton(user);
    if (event === "SIGNED_IN" && user) {
      var m = user.user_metadata || {};
      sb.from("profiles").update({
        full_name: m.full_name || null,
        email_consent: !!m.email_consent,
        consent_at: m.consent_at || null,
        consent_source: m.consent_source || null
      }).eq("id", user.id).then(function () { /* consent recorded (backup to the DB trigger) */ });
      renderMember(user);
      overlay.classList.add("open");
    }
  });

  // Reflect existing session on load.
  sb.auth.getUser().then(function (res) { updateButton(res.data && res.data.user); });
})();
