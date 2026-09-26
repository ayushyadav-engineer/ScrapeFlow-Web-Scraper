document.addEventListener("DOMContentLoaded", () => {
  // Client-side hint only. The server independently re-validates that
  // password and confirm_password match; this never replaces that check.
  const password = document.querySelector('input[name="password"]');
  const confirm = document.querySelector('input[name="confirm_password"]');
  if (password && confirm) {
    const check = () => {
      confirm.setCustomValidity(
        confirm.value && confirm.value !== password.value ? "Passwords do not match." : ""
      );
    };
    password.addEventListener("input", check);
    confirm.addEventListener("input", check);
  }

  const slider = document.querySelector("#pages");
  const output = document.querySelector("#pagesValue");
  if (slider && output) {
    const update = () => {
      const n = Number(slider.value);
      output.textContent = `${n} ${n === 1 ? "page" : "pages"}`;
      const min = Number(slider.min);
      const max = Number(slider.max);
      const pct = ((n - min) / (max - min)) * 100;
      slider.style.setProperty("--fill", `${pct}%`);
    };
    slider.addEventListener("input", update);
    document.querySelectorAll(".step-button").forEach(btn => {
      btn.addEventListener("click", () => {
        slider.value = Math.max(Number(slider.min), Math.min(Number(slider.max), Number(slider.value) + Number(btn.dataset.step)));
        slider.dispatchEvent(new Event("input", {bubbles: true}));
      });
    });
    update();
  }

  const canvas = document.querySelector("#activityChart");
  if (canvas) {
    let data = [];
    try { data = JSON.parse(canvas.dataset.activity || "[]"); } catch (_) { data = []; }
    const ctx = canvas.getContext("2d");
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 600;
    const height = canvas.clientHeight || 190;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(222, 232, 234, .12)";
    ctx.lineWidth = 1;
    for (let y = 22; y < height - 20; y += 36) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); }
    const values = data.map(item => Number(item.count) || 0);
    if (!values.length) return;
    const max = Math.max(1, ...values);
    const padX = 18, padY = 24;
    const step = values.length > 1 ? (width - padX * 2) / (values.length - 1) : 0;
    const points = values.map((value, i) => ({
      x: padX + i * step,
      y: height - padY - ((value / max) * (height - padY * 2))
    }));
    ctx.beginPath();
    points.forEach((point, i) => i ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y));
    ctx.strokeStyle = "#D2AF37";
    ctx.lineWidth = 2;
    ctx.stroke();
    points.forEach(point => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#E8CB6B";
      ctx.fill();
    });
  }
});
