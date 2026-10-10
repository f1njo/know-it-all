import random
import unittest

from questions import BANK, DIFFICULTIES, SUBJECTS, Question, Session, make_test, normalize


class QuestionBankTests(unittest.TestCase):
    def test_every_subject_and_difficulty_has_distinct_valid_questions(self):
        for subject in SUBJECTS:
            for difficulty in DIFFICULTIES:
                with self.subTest(subject=subject, difficulty=difficulty):
                    questions = make_test(subject, difficulty, random.Random(17))
                    self.assertGreaterEqual(len(questions), 8)
                    self.assertEqual(len(questions), len({q.prompt for q in questions}))
                    for q in questions:
                        self.assertEqual(len(q.options), 4)
                        self.assertEqual(len({normalize(x) for x in q.options}), 4)
                        self.assertIn(q.answer, q.options)
                        self.assertTrue(q.prompt and q.explanation)

    def test_many_arithmetic_tests_terminate_with_nonnegative_options(self):
        for seed in range(100):
            for level in DIFFICULTIES:
                questions = make_test('Математика', level, random.Random(seed))
                self.assertEqual(len(questions), 10)
                for q in questions:
                    self.assertTrue(all(int(x) >= 0 for x in q.options))

    def test_arithmetic_examples_have_correct_answers(self):
        for seed in range(20):
            for level in DIFFICULTIES:
                for q in make_test('Математика', level, random.Random(seed)):
                    if q.prompt.endswith('= ?'):
                        expression = q.prompt[:-3].replace('−', '-').replace('×', '*').replace('÷', '/')
                        self.assertEqual(eval(expression, {'__builtins__': {}}), int(q.answer))

    def test_invalid_selection_is_rejected(self):
        for subject, difficulty in (('Музыка', 'Лёгкий'), ('Математика', 'Эксперт')):
            with self.assertRaises(ValueError):
                make_test(subject, difficulty)

    def test_input_tasks_exist(self):
        for subject in ('Математика', 'Английский', 'Информатика'):
            self.assertTrue(any(q.typed for q in make_test(subject, 'Сложный', random.Random(2))))


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.session = Session([Question('Кот?', 'cat', ('cat', 'dog', 'sun', 'pen'), 'Cat — кот.') for _ in range(4)])

    def test_scoring_streak_and_duplicate_submission(self):
        s = self.session
        self.assertFalse(s.advance())
        self.assertTrue(s.submit('  CAT  '))
        self.assertIsNone(s.submit('cat'))
        self.assertEqual((s.score, s.correct, s.streak), (10, 1, 1))
        s.advance()
        s.submit('cat')
        self.assertEqual(s.score, 22)
        s.advance()
        self.assertFalse(s.submit('dog'))
        self.assertEqual((s.score, s.streak, s.best_streak), (22, 0, 2))
        s.advance()
        s.submit('cat')
        self.assertEqual((s.score, s.correct), (32, 3))
        self.assertFalse(s.advance())
        self.assertEqual(len(s.history), 4)

    def test_empty_session_is_rejected(self):
        with self.assertRaises(ValueError):
            Session([])

    def test_full_test_can_finish_for_all_fifteen_selections(self):
        for subject in SUBJECTS:
            for difficulty in DIFFICULTIES:
                s = Session(make_test(subject, difficulty, random.Random(42)))
                for q in s.questions:
                    self.assertEqual(s.current, q)
                    self.assertTrue(s.submit(q.answer))
                    s.advance()
                self.assertEqual(s.correct, len(s.questions))
                self.assertEqual(s.score, sum(10 + 2 * i for i in range(len(s.questions))))


if __name__ == '__main__':
    unittest.main()
