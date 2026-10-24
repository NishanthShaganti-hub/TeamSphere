/**
 * TeamSphere Client-Side Script
 * Accessible, Vanilla JavaScript interactions (modals, toasts, chips, mobile nav).
 */

document.addEventListener("DOMContentLoaded", () => {
  initMobileNav();
  initSearchShortcut();
  initCharCounters();
  initDismissableAlerts();
});

/**
 * Mobile Navigation Drawer Toggle
 */
function initMobileNav() {
  const toggleBtn = document.getElementById("nav-toggle-btn");
  const navMenu = document.getElementById("nav-menu");

  if (!toggleBtn || !navMenu) return;

  toggleBtn.addEventListener("click", () => {
    const isExpanded = toggleBtn.getAttribute("aria-expanded") === "true";
    toggleBtn.setAttribute("aria-expanded", String(!isExpanded));
    navMenu.classList.toggle("is-open", !isExpanded);
  });

  // Close when clicking outside
  document.addEventListener("click", (event) => {
    if (!navMenu.contains(event.target) && !toggleBtn.contains(event.target) && navMenu.classList.contains("is-open")) {
      navMenu.classList.remove("is-open");
      toggleBtn.setAttribute("aria-expanded", "false");
    }
  });
}

/**
 * Focus the page search when "/" is pressed outside an editable control.
 */
function initSearchShortcut() {
  const search = document.getElementById("project-search") || document.getElementById("student-search");
  if (!search) return;

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    const isEditing = target instanceof HTMLElement
      && (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

    if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !isEditing) {
      event.preventDefault();
      search.focus();
    }
  });
}

/**
 * Floating Toast Alerts
 */
window.showToast = function(message, type = "info", duration = 3500) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type === "error" ? "toast-error" : ""}`;
  toast.setAttribute("role", "status");
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 250);
  }, duration);
};

/**
 * Accessible Modal Controller
 */
let lastActiveElement = null;

window.openModal = function(modalId) {
  const backdrop = document.getElementById(modalId);
  if (!backdrop) return;

  lastActiveElement = document.activeElement;
  backdrop.classList.add("is-active");
  backdrop.setAttribute("aria-hidden", "false");

  // Focus first focusable element
  const focusable = backdrop.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
  if (focusable.length > 0) {
    focusable[0].focus();
  }

  // Keyboard navigation & Esc listener
  const handleKeyDown = (e) => {
    if (e.key === "Escape") {
      window.closeModal(modalId);
    }
  };

  backdrop._keydownHandler = handleKeyDown;
  document.addEventListener("keydown", handleKeyDown);
};

window.closeModal = function(modalId) {
  const backdrop = document.getElementById(modalId);
  if (!backdrop) return;

  backdrop.classList.remove("is-active");
  backdrop.setAttribute("aria-hidden", "true");

  if (backdrop._keydownHandler) {
    document.removeEventListener("keydown", backdrop._keydownHandler);
    delete backdrop._keydownHandler;
  }

  if (lastActiveElement && typeof lastActiveElement.focus === "function") {
    lastActiveElement.focus();
  }
};

/**
 * Helper to get the CSRF token from meta tag
 */
window.getCsrfToken = function() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
};

/**
 * CSRF-aware fetch wrapper
 */
window.fetchWithCsrf = async function(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const csrfToken = window.getCsrfToken();
  if (csrfToken && !headers.has("X-CSRFToken")) {
    headers.set("X-CSRFToken", csrfToken);
  }

  return fetch(url, {
    ...options,
    headers,
  });
};

/**
 * Character Counters for textareas
 */
function initCharCounters() {
  const textareas = document.querySelectorAll("textarea[data-counter]");
  textareas.forEach((textarea) => {
    const counterId = textarea.getAttribute("data-counter");
    const counterEl = document.getElementById(counterId);
    const max = textarea.getAttribute("maxlength");

    if (counterEl && max) {
      const updateCount = () => {
        const remaining = max - textarea.value.length;
        counterEl.textContent = `${textarea.value.length} / ${max} characters`;
      };
      textarea.addEventListener("input", updateCount);
      updateCount();
    }
  });
}

/**
 * Dismissable Alerts
 */
function initDismissableAlerts() {
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.remove();
      }
    });
  });
}

/**
 * Chips Input for Skills and Interests
 */
window.initChipsInput = function(containerId, hiddenInputId, maxChips = 10, maxChar = 30) {
  const container = document.getElementById(containerId);
  const hiddenInput = document.getElementById(hiddenInputId);
  if (!container || !hiddenInput) return;

  let chips = hiddenInput.value ? hiddenInput.value.split(",").map(s => s.trim().toLowerCase()).filter(Boolean) : [];

  const textInput = container.querySelector(".chips-input");

  function renderChips() {
    // Remove existing chip tags
    container.querySelectorAll(".chip").forEach(c => c.remove());

    chips.forEach((chipText, index) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = chipText;

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "chip-remove";
      removeBtn.innerHTML = "&times;";
      removeBtn.setAttribute("aria-label", `Remove ${chipText}`);
      removeBtn.addEventListener("click", () => {
        chips.splice(index, 1);
        hiddenInput.value = chips.join(",");
        renderChips();
      });

      chip.appendChild(removeBtn);
      container.insertBefore(chip, textInput);
    });

    hiddenInput.value = chips.join(",");
  }

  function addChip(raw) {
    const clean = raw.trim().toLowerCase().replace(/\s+/g, " ");
    if (!clean) return;
    if (clean.length > maxChar) {
      window.showToast(`Tag must be under ${maxChar} characters`, "error");
      return;
    }
    if (chips.length >= maxChips) {
      window.showToast(`Maximum ${maxChips} tags allowed`, "error");
      return;
    }
    if (!chips.includes(clean)) {
      chips.push(clean);
      renderChips();
    }
  }

  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        addChip(textInput.value);
        textInput.value = "";
      } else if (e.key === "Backspace" && textInput.value === "" && chips.length > 0) {
        chips.pop();
        renderChips();
      }
    });

    textInput.addEventListener("blur", () => {
      if (textInput.value) {
        addChip(textInput.value);
        textInput.value = "";
      }
    });
  }

  // Ensure any typed text is saved even if user clicks Save without pressing Enter
  const parentForm = container.closest("form");
  if (parentForm) {
    parentForm.addEventListener("submit", () => {
      if (textInput && textInput.value) {
        // Split by comma if user typed comma-separated text
        textInput.value.split(",").forEach(part => addChip(part));
        textInput.value = "";
      }
    });
  }

  renderChips();
};
