
function openModal() {
  document.getElementById("modal").classList.add("show");
  setTimeout(() => {
    document.getElementById("playerName").focus();
  }, 100);
}

function closeModal() {
  document.getElementById("modal").classList.remove("show");
}

async function launchGame() {
  const name = document.getElementById("playerName").value.trim();

  if (!name) {
    alert("Enter your name");
    return;
  }

  const res = await fetch("/api/launch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ name })
  });

  const data = await res.json();

  if (!res.ok) {
    alert(data.detail || "Failed to launch");
    return;
  }

  closeModal();
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && document.getElementById("modal").classList.contains("show")) {
    launchGame();
  }
});

const medals = ['🥇', '🥈', '🥉'];

const avatarColors = [
  { bg: '#11101b', color: '#3C3489' },
  { bg: '#11101b', color: '#085041' },
  { bg: '#11101b', color: '#633806' },
  { bg: '#11101b', color: '#993C1D' },
  { bg: '#11101b', color: '#0C447C' },
];

async function fetchLeaderboard() {
  try {
    const res = await fetch('/api/leaderboard');
    const data = await res.json();
    renderLeaderboard(data);
  } catch (err) {
    console.error('Failed to fetch leaderboard:', err);
  }
}

function renderLeaderboard(players) {
  const body = document.getElementById('lb-body');

  if (!players || players.length === 0) {
    body.innerHTML = '<div class="lb-empty">No scores yet. Be the first!</div>';
    return;
  }

  body.innerHTML = players.map((p, i) => {
    const av = avatarColors[i % avatarColors.length];
    const rank = medals[i] || `${i + 1}`;
    const initials = p.name.slice(0, 2).toUpperCase();
    return `
      <div class="lb-row">
        <span class="rank">${rank}</span>
        <div class="player">
          <div class="avatar" style="background:${av.bg}; color:${av.color};">${initials}</div>
          <span class="player-name">${p.name}</span>
        </div>
        <span class="time-val">${p.best_time_str}</span>
      </div>
    `;
  }).join('');
}

// load on page open, then refresh every 10 seconds
fetchLeaderboard();
setInterval(fetchLeaderboard, 10000);