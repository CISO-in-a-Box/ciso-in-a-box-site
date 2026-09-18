/* Site-owned copy buttons for /use-with-ai/.
 *
 * Buttons carry data-copy-target="#id"; the text copied is the
 * textContent of that element's <code> block (or the element itself
 * when it is a prompt block), so what is copied is the exact decoded
 * text rendered by the page. No framework, no dependencies.
 */
(function () {
  "use strict";

  function targetElement(button) {
    var id = button.getAttribute("data-copy-target");
    if (!id) return null;
    var root = document.getElementById(id);
    if (!root) return null;
    var code = root.querySelector("code, pre");
    return code || root;
  }

  function showStatus(button, message, ok) {
    var original = button.getAttribute("data-original-text") || button.textContent;
    button.setAttribute("data-original-text", original);
    button.textContent = message;
    button.classList.remove("copy-ok", "copy-fail");
    button.classList.add(ok ? "copy-ok" : "copy-fail");
    setTimeout(function () {
      button.textContent = button.getAttribute("data-original-text");
      button.classList.remove("copy-ok", "copy-fail");
    }, 2500);
  }

  function copyWithExecCommand(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (err) {
      ok = false;
    }
    document.body.removeChild(textarea);
    return ok;
  }

  function handleClick(event) {
    var button = event.target.closest(".copy-btn");
    if (!button) return;
    var target = targetElement(button);
    if (!target) return;
    var text = target.textContent;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText(text)
        .then(function () {
          showStatus(button, "Copied!", true);
        })
        .catch(function () {
          var ok = copyWithExecCommand(text);
          showStatus(button, ok ? "Copied!" : "Copy failed — select the text manually", ok);
        });
    } else {
      var ok = copyWithExecCommand(text);
      showStatus(button, ok ? "Copied!" : "Copy failed — select the text manually", ok);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.addEventListener("click", handleClick);
  });
})();