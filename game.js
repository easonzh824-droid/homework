const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d");
const scoreEl = document.querySelector("#score");
const bestScoreEl = document.querySelector("#best-score");
const restartButton = document.querySelector("#restart-button");
const overlay = document.querySelector("#overlay");
const overlayTitle = document.querySelector("#overlay-title");
const overlayText = document.querySelector("#overlay-text");

const gridSize = 24;
const tileCount = canvas.width / gridSize;
const initialSpeed = 140;
const bestScoreKey = "snake-best-score";

let snake;
let food;
let direction;
let queuedDirection;
let score;
let bestScore = Number(localStorage.getItem(bestScoreKey) || 0);
let gameLoopId = null;
let isRunning = false;
let isStarted = false;
let isGameOver = false;

bestScoreEl.textContent = bestScore;

function resetGame() {
  snake = [
    { x: 10, y: 12 },
    { x: 9, y: 12 },
    { x: 8, y: 12 },
  ];
  direction = { x: 1, y: 0 };
  queuedDirection = { ...direction };
  score = 0;
  food = spawnFood();
  isRunning = false;
  isStarted = false;
  isGameOver = false;
  scoreEl.textContent = score;
  showOverlay("按方向鍵開始", "用鍵盤方向鍵或 WASD 控制移動。");
  draw();
}

function spawnFood() {
  while (true) {
    const position = {
      x: Math.floor(Math.random() * tileCount),
      y: Math.floor(Math.random() * tileCount),
    };

    const overlapsSnake = snake?.some((segment) => segment.x === position.x && segment.y === position.y);
    if (!overlapsSnake) {
      return position;
    }
  }
}

function startGame() {
  if (isGameOver) {
    resetGame();
  }

  if (isRunning) {
    return;
  }

  isRunning = true;
  isStarted = true;
  hideOverlay();
  scheduleNextTick();
}

function togglePause() {
  if (!isStarted || isGameOver) {
    return;
  }

  isRunning = !isRunning;
  if (isRunning) {
    hideOverlay();
    scheduleNextTick();
    return;
  }

  clearTimeout(gameLoopId);
  showOverlay("已暫停", "按 Space 繼續遊戲。");
}

function scheduleNextTick() {
  clearTimeout(gameLoopId);
  const speed = Math.max(70, initialSpeed - Math.floor(score / 5) * 8);
  gameLoopId = setTimeout(gameTick, speed);
}

function gameTick() {
  if (!isRunning) {
    return;
  }

  direction = queuedDirection;
  const head = {
    x: snake[0].x + direction.x,
    y: snake[0].y + direction.y,
  };

  const hitWall =
    head.x < 0 ||
    head.x >= tileCount ||
    head.y < 0 ||
    head.y >= tileCount;
  const hitSelf = snake.some((segment) => segment.x === head.x && segment.y === head.y);

  if (hitWall || hitSelf) {
    endGame();
    return;
  }

  snake.unshift(head);

  if (head.x === food.x && head.y === food.y) {
    score += 1;
    scoreEl.textContent = score;
    if (score > bestScore) {
      bestScore = score;
      localStorage.setItem(bestScoreKey, String(bestScore));
      bestScoreEl.textContent = bestScore;
    }
    food = spawnFood();
  } else {
    snake.pop();
  }

  draw();
  scheduleNextTick();
}

function endGame() {
  isRunning = false;
  isGameOver = true;
  clearTimeout(gameLoopId);
  showOverlay("遊戲結束", `本局得分 ${score}，按重新開始再玩一次。`);
}

function drawGrid() {
  ctx.strokeStyle = "rgba(92, 66, 35, 0.08)";
  ctx.lineWidth = 1;

  for (let index = 1; index < tileCount; index += 1) {
    const offset = index * gridSize;

    ctx.beginPath();
    ctx.moveTo(offset, 0);
    ctx.lineTo(offset, canvas.height);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, offset);
    ctx.lineTo(canvas.width, offset);
    ctx.stroke();
  }
}

function drawSnake() {
  snake.forEach((segment, index) => {
    const isHead = index === 0;
    const padding = isHead ? 2 : 3;
    ctx.fillStyle = isHead ? "#14532d" : "#2f7d32";
    ctx.beginPath();
    ctx.roundRect(
      segment.x * gridSize + padding,
      segment.y * gridSize + padding,
      gridSize - padding * 2,
      gridSize - padding * 2,
      6
    );
    ctx.fill();
  });
}

function drawFood() {
  const centerX = food.x * gridSize + gridSize / 2;
  const centerY = food.y * gridSize + gridSize / 2;

  ctx.fillStyle = "#ef4444";
  ctx.beginPath();
  ctx.arc(centerX, centerY, gridSize * 0.26, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,0.7)";
  ctx.beginPath();
  ctx.arc(centerX - 3, centerY - 3, gridSize * 0.08, 0, Math.PI * 2);
  ctx.fill();
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();
  drawFood();
  drawSnake();
}

function setDirection(nextDirection) {
  const isReversing =
    nextDirection.x === -direction.x &&
    nextDirection.y === -direction.y;

  if (isReversing) {
    return;
  }

  queuedDirection = nextDirection;
  startGame();
}

function showOverlay(title, text) {
  overlayTitle.textContent = title;
  overlayText.textContent = text;
  overlay.classList.remove("hidden");
}

function hideOverlay() {
  overlay.classList.add("hidden");
}

document.addEventListener("keydown", (event) => {
  const key = event.key.toLowerCase();
  const directionMap = {
    arrowup: { x: 0, y: -1 },
    w: { x: 0, y: -1 },
    arrowdown: { x: 0, y: 1 },
    s: { x: 0, y: 1 },
    arrowleft: { x: -1, y: 0 },
    a: { x: -1, y: 0 },
    arrowright: { x: 1, y: 0 },
    d: { x: 1, y: 0 },
  };

  if (key === " ") {
    event.preventDefault();
    togglePause();
    return;
  }

  const nextDirection = directionMap[key];
  if (!nextDirection) {
    return;
  }

  event.preventDefault();
  setDirection(nextDirection);
});

restartButton.addEventListener("click", () => {
  clearTimeout(gameLoopId);
  resetGame();
});

resetGame();
