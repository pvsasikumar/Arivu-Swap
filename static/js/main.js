// Auto-dismiss alerts
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-8px)';
    alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    setTimeout(() => alert.remove(), 400);
  }, 4000);
});

// Navbar scroll effect
const navbar = document.querySelector('.navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.style.borderBottomColor = window.scrollY > 10 ? 'rgba(108,71,255,0.2)' : 'var(--border)';
  });
}

// Skill card entrance animation
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      entry.target.style.animationDelay = (i * 0.05) + 's';
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.skill-card, .step, .cat-card, .stat-card').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(16px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});

// ── Core time formatter ───────────────────────────────────────────
function formatTime(timestamp) {
  if (!timestamp) return "";
  timestamp = timestamp.trim().replace(" ", "T");
  const hasOffset = /[Z+\-]\d*$/.test(timestamp) || timestamp.endsWith("Z");
  if (!hasOffset) timestamp += "Z";
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Apply times to any unformatted .msg-time elements ─────────────
function applyMsgTimes(container = document) {
  container.querySelectorAll(".msg-time:not([data-formatted])").forEach(el => {
    const t = el.getAttribute("data-time");
    if (t) {
      el.innerText = formatTime(t);
      el.setAttribute("data-formatted", "true"); // prevent double processing
    }
  });
}

// ── On page load ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  setTimeout(() => {
    document.querySelectorAll('.skill-card, .step, .cat-card, .stat-card').forEach(el => {
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    });
  }, 100);

  applyMsgTimes(); // format times on initial load

});

// ── MutationObserver: auto-format times on new messages ───────────
const chatObserver = new MutationObserver(() => {
  applyMsgTimes(); // runs only on unformatted elements due to :not([data-formatted])
});

const chatContainer = document.querySelector('.chat-box, .messages, .chat-container');
if (chatContainer) {
  chatObserver.observe(chatContainer, { childList: true, subtree: true });
}