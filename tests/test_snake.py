from __future__ import annotations

import unittest

from smalloldgames.engine.input import InputState
from smalloldgames.games.snake import SnakeScene


class SnakeTests(unittest.TestCase):
    def test_snake_moves_down_initially(self) -> None:
        scene = SnakeScene(lambda: None, seed=42)
        head_before = scene.snake[0]
        scene._step()
        head_after = scene.snake[0]
        self.assertEqual(head_after, (head_before[0], head_before[1] - 1))

    def test_snake_eats_food_and_grows(self) -> None:
        scene = SnakeScene(lambda: None, seed=42)
        scene.food = (10, 9)  # Directly in front of head (initially at 10,10 moving 0,-1)
        initial_length = len(scene.snake)
        scene._step()
        self.assertEqual(len(scene.snake), initial_length + 1)
        self.assertEqual(scene.score, 10)
        self.assertNotEqual(scene.food, (10, 9))  # New food should have spawned

    def test_snake_dies_on_wall(self) -> None:
        scene = SnakeScene(lambda: None, seed=42)
        scene.snake = [(0, 0)]
        scene.direction = (-1, 0)
        scene.next_direction = (-1, 0)
        scene._step()
        self.assertTrue(scene.game_over)

    def test_snake_dies_on_self(self) -> None:
        scene = SnakeScene(lambda: None, seed=42)
        scene.snake = [(10, 10), (11, 10), (11, 11), (10, 11)]
        scene.direction = (0, 1)
        scene.next_direction = (0, 1)
        scene._step()
        self.assertTrue(scene.game_over)

    def test_snake_cannot_reverse_directly(self) -> None:
        scene = SnakeScene(lambda: None, seed=42)
        scene.direction = (0, -1)
        inputs = InputState()
        import glfw

        inputs.on_key(glfw.KEY_UP, glfw.PRESS)  # Try to go UP while going DOWN
        scene._handle_input(inputs)
        self.assertEqual(scene.next_direction, (0, -1))  # Should still be DOWN


if __name__ == "__main__":
    unittest.main()
