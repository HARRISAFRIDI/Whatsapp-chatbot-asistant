import unittest
from types import SimpleNamespace
from unittest.mock import patch

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent import generate_reply


class AgentTests(unittest.TestCase):
    def test_generate_reply_extracts_text_from_content_blocks(self) -> None:
        result = {
            "messages": [
                SimpleNamespace(
                    content=[
                        {"type": "text", "text": "Hello "},
                        {"type": "image", "extras": {}},
                        {"type": "text", "text": "there!"},
                    ]
                )
            ]
        }
        with patch("app.agent.get_agent") as get_agent:
            get_agent.return_value.invoke.return_value = result

            reply = generate_reply("Say hello.")

        self.assertEqual(reply, "Hello there!")

    def test_generate_reply_sends_question_to_llm_as_general_assistant(self) -> None:
        result = {
            "messages": [
                SimpleNamespace(content="The answer is 42.")
            ]
        }
        with patch("app.agent.get_agent") as get_agent:
            get_agent.return_value.invoke.return_value = result

            reply = generate_reply("What is the answer?")

        messages = get_agent.return_value.invoke.call_args.args[0]["messages"]
        self.assertIsInstance(messages[0], SystemMessage)
        self.assertIn("Answer the user's questions directly", messages[0].content)
        self.assertIsInstance(messages[1], HumanMessage)
        self.assertEqual(messages[1].content, "What is the answer?")
        self.assertEqual(reply, "The answer is 42.")

    def test_generate_reply_rejects_content_without_text(self) -> None:
        result = {
            "messages": [
                SimpleNamespace(content=[{"type": "image", "extras": {}}])
            ]
        }
        with patch("app.agent.get_agent") as get_agent:
            get_agent.return_value.invoke.return_value = result

            with self.assertRaisesRegex(RuntimeError, "empty or unsupported response"):
                generate_reply("Say hello.")


if __name__ == "__main__":
    unittest.main()
