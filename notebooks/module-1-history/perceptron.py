"""
ДЗ 2 модуля 1 — собрать однослойный перцептрон, как у Розенблатта,
и научить его отличать треугольник от квадрата.

Запуск:
    python perceptron.py

Зависимости (одной командой):
    pip install numpy matplotlib

Ожидаемый результат:
    - в консоли финальная точность ≥ 90%
    - рядом появится файл training.png с кривой обучения
    - после bonus-эксперимента распечатается строка про XOR
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 1. Генератор картинок 8×8: треугольники vs квадраты.
#    Картинки вернутся как одномерные массивы из 64 нулей и единиц.
# ---------------------------------------------------------------------------

GRID = 8
N_FEATURES = GRID * GRID  # 64


def _blank() -> np.ndarray:
    return np.zeros((GRID, GRID), dtype=np.int8)


def make_triangle(rng: random.Random) -> np.ndarray:
    """Случайный простой треугольник (равнобедренный, плотный)."""
    img = _blank()
    size = rng.randint(4, 6)
    top_row = rng.randint(0, GRID - size)
    top_col = rng.randint(0, GRID - size)
    for r in range(size):
        # на r-й строке закрашиваем ширину 2r+1, центрированную
        half = r
        center = top_col + size // 2
        for c in range(center - half, center + half + 1):
            if 0 <= c < GRID:
                img[top_row + r, c] = 1
    return img.flatten()


def make_square(rng: random.Random) -> np.ndarray:
    """Случайный закрашенный квадрат."""
    img = _blank()
    size = rng.randint(3, 5)
    top_row = rng.randint(0, GRID - size)
    top_col = rng.randint(0, GRID - size)
    img[top_row : top_row + size, top_col : top_col + size] = 1
    return img.flatten()


def make_dataset(n_per_class: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Возвращает X (n×64) и y (n) — 1 = треугольник, 0 = квадрат."""
    rng = random.Random(seed)
    triangles = [make_triangle(rng) for _ in range(n_per_class)]
    squares = [make_square(rng) for _ in range(n_per_class)]
    X = np.array(triangles + squares, dtype=np.float32)
    y = np.array([1] * n_per_class + [0] * n_per_class, dtype=np.float32)
    # перемешать
    perm = rng.sample(range(len(X)), len(X))
    return X[perm], y[perm]


# ---------------------------------------------------------------------------
# 2. Перцептрон. Это место — для тебя.
# ---------------------------------------------------------------------------


class Perceptron:
    """Однослойный перцептрон Розенблатта.

    Веса хранятся как numpy-массив длины N_FEATURES.
    Порог хранится отдельно (его тоже можно учить — но в этой
    реализации зафиксируем 0 ради простоты, веса справятся).
    """

    def __init__(self, n_features: int = N_FEATURES, lr: float = 0.1) -> None:
        self.weights: np.ndarray = np.zeros(n_features, dtype=np.float32)
        self.lr: float = lr  # шаг обучения (как сильно крутить потенциометры)

    # -----------------------------------------------------------------------
    # TODO 1. predict(x): вернуть 1 если взвешенная сумма > 0, иначе 0.
    #
    # Это ровно то, что делал Mark I:
    #   sum_input = w · x   (скалярное произведение)
    #   output = 1, если sum_input > 0, иначе 0
    # -----------------------------------------------------------------------
    def predict(self, x: np.ndarray) -> int:
        # PASTE: одну строку с np.dot и сравнением.
        raise NotImplementedError("Реализуй predict — см. TODO 1.")

    # -----------------------------------------------------------------------
    # TODO 2. train_step(x, y_true): сделать ОДИН шаг обучения.
    #
    # Правило перцептрона (как электромоторы у Mark I):
    #   y_pred = self.predict(x)
    #   error = y_true - y_pred
    #   self.weights += self.lr * error * x
    #
    # Если error = 0 — не трогаем (правильно ответили).
    # Если error = +1 — увеличиваем веса там, где входы были «1».
    # Если error = -1 — уменьшаем там же.
    # -----------------------------------------------------------------------
    def train_step(self, x: np.ndarray, y_true: float) -> None:
        # PASTE: реализуй три строки выше.
        raise NotImplementedError("Реализуй train_step — см. TODO 2.")

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> float:
        """Вернуть точность (доля правильных ответов от 0 до 1)."""
        preds = np.array([self.predict(x) for x in X])
        return float((preds == y).mean())


# ---------------------------------------------------------------------------
# 3. Тренировка + замер + график.
# ---------------------------------------------------------------------------


def train_loop(
    perceptron: Perceptron,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    epochs: int = 200,
) -> list[float]:
    """Прогнать `epochs` эпох обучения, на каждой замерить test-accuracy."""
    history = []
    for _epoch in range(epochs):
        # один проход по всему train-сету
        for x, y in zip(X_train, y_train):
            perceptron.train_step(x, y)
        history.append(perceptron.evaluate(X_test, y_test))
    return history


def plot_history(history: list[float], filename: str) -> None:
    plt.figure(figsize=(7, 4))
    plt.plot(history, color="#7f5cca", linewidth=2)
    plt.axhline(y=0.9, color="#10b981", linestyle="--", alpha=0.6, label="цель: 90%")
    plt.xlabel("эпоха")
    plt.ylabel("точность на тесте")
    plt.title("Перцептрон Розенблатта: треугольник vs квадрат")
    plt.ylim(0.4, 1.02)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=120)
    plt.close()


def run_main_experiment() -> None:
    print("=" * 60)
    print("Эксперимент 1: треугольник vs квадрат")
    print("=" * 60)
    X_train, y_train = make_dataset(n_per_class=80, seed=42)
    X_test, y_test = make_dataset(n_per_class=40, seed=7)

    p = Perceptron()
    history = train_loop(p, X_train, y_train, X_test, y_test, epochs=200)

    final_acc = history[-1]
    print(f"финальная точность на тесте: {final_acc:.1%}")

    out_path = Path(__file__).parent / "training.png"
    plot_history(history, str(out_path))
    print(f"график сохранён: {out_path.name}")


# ---------------------------------------------------------------------------
# 4. БОНУС: то самое ограничение 1969 года.
# ---------------------------------------------------------------------------


def make_xor_like_dataset(n_per_class: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Картинки, у которых классы не разделимы линейно.

    Класс 1: треугольник в верхнем-левом углу ИЛИ квадрат в нижнем-правом.
    Класс 0: треугольник в нижнем-правом ИЛИ квадрат в верхнем-левом.

    Это XOR-подобная задача: пиксели сами по себе не отличают классы.
    Однослойный перцептрон обязан проиграть.
    """
    rng = random.Random(seed)
    X, y = [], []

    def shifted(shape_fn, dr, dc):
        img = _blank()
        # маленькая фигура, конкретный угол
        size = 3
        for r in range(size):
            for c in range(size):
                if shape_fn == "triangle" and c <= r:
                    img[dr + r, dc + c] = 1
                elif shape_fn == "square":
                    img[dr + r, dc + c] = 1
        return img.flatten()

    for _ in range(n_per_class):
        # класс 1
        if rng.random() < 0.5:
            X.append(shifted("triangle", 0, 0))
        else:
            X.append(shifted("square", 5, 5))
        y.append(1)
        # класс 0
        if rng.random() < 0.5:
            X.append(shifted("triangle", 5, 5))
        else:
            X.append(shifted("square", 0, 0))
        y.append(0)
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def run_xor_experiment() -> None:
    print()
    print("=" * 60)
    print("Эксперимент 2: XOR-подобная задача (тот самый потолок 1969-го)")
    print("=" * 60)
    X_train, y_train = make_xor_like_dataset(n_per_class=80, seed=42)
    X_test, y_test = make_xor_like_dataset(n_per_class=40, seed=7)

    p = Perceptron()
    history = train_loop(p, X_train, y_train, X_test, y_test, epochs=200)

    final_acc = history[-1]
    print(f"финальная точность на тесте: {final_acc:.1%}")
    print(
        "если ≈50% — это и есть тот самый потолок, который зафиксировали\n"
        "Минский и Пейперт в книге Perceptrons (1969). Однослойная сеть\n"
        "не разделяет XOR-подобные данные, нужен ещё один обучаемый слой."
    )


if __name__ == "__main__":
    run_main_experiment()
    run_xor_experiment()
