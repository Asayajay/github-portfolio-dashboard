/*
 * Horizontal bar chart, one bar per repo, magnitude = hygiene percent
 * (0-100). Color is a status tier (good/warning/serious/critical), not a
 * categorical identity -- there's no legend because each bar carries its
 * own label and percentage directly, so color is reinforcement, not the
 * only signal.
 */

function statusColorFor(percent, styles) {
  if (percent >= 100) return styles.getPropertyValue("--status-good").trim();
  if (percent >= 60) return styles.getPropertyValue("--status-warning").trim();
  if (percent > 0) return styles.getPropertyValue("--status-serious").trim();
  return styles.getPropertyValue("--status-critical").trim();
}

function drawHealthChart(canvas, repos) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = canvas.clientWidth || 800;
  const rowHeight = 26;
  const padding = { top: 8, bottom: 8, left: 10, right: 60 };
  const cssHeight = padding.top + padding.bottom + repos.length * rowHeight;

  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.height = `${cssHeight}px`;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const styles = getComputedStyle(document.body);
  const ink = styles.getPropertyValue("--text-primary").trim();
  const mutedInk = styles.getPropertyValue("--text-muted").trim();

  const labelWidth = 220;
  const trackLeft = padding.left + labelWidth;
  const trackWidth = cssWidth - trackLeft - padding.right;

  repos.forEach((repo, i) => {
    const y = padding.top + i * rowHeight;
    const barHeight = 14;
    const barY = y + (rowHeight - barHeight) / 2;

    // Repo name, right-aligned against the track.
    ctx.fillStyle = mutedInk;
    ctx.font = "500 12px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    const truncated = repo.label.length > 30 ? repo.label.slice(0, 29) + "…" : repo.label;
    ctx.fillText(truncated, padding.left, y + rowHeight / 2);

    // Track background.
    ctx.fillStyle = styles.getPropertyValue("--gridline").trim();
    ctx.fillRect(trackLeft, barY, trackWidth, barHeight);

    // Bar.
    const barWidth = Math.max((repo.value / 100) * trackWidth, 3);
    const radius = Math.min(4, barHeight / 2);
    ctx.fillStyle = statusColorFor(repo.value, styles);
    ctx.beginPath();
    ctx.moveTo(trackLeft, barY);
    ctx.lineTo(trackLeft + barWidth - radius, barY);
    ctx.arcTo(trackLeft + barWidth, barY, trackLeft + barWidth, barY + radius, radius);
    ctx.lineTo(trackLeft + barWidth, barY + barHeight - radius);
    ctx.arcTo(trackLeft + barWidth, barY + barHeight, trackLeft + barWidth - radius, barY + barHeight, radius);
    ctx.lineTo(trackLeft, barY + barHeight);
    ctx.closePath();
    ctx.fill();

    // Direct value label past the end of the track.
    ctx.fillStyle = ink;
    ctx.font = "600 12px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(`${Math.round(repo.value)}%`, trackLeft + trackWidth + 8, y + rowHeight / 2);
  });
}
