def get_qna_prompt(question: str) -> str:
    """
    Format the tutor prompt for Q&A questions.
    """
    return (
        f"You are an expert tutor. Please answer the following student question. "
        f"Provide a clear, detailed, and educational response using clean Markdown.\n\n"
        f"Structure your response strictly matching this layout:\n"
        f"# Topic\n\n"
        f"## Overview\n\n"
        f"[Provide a short introduction about the topic/question]\n\n"
        f"---\n\n"
        f"## Key Concepts\n\n"
        f"- [Key point 1]\n"
        f"- [Key point 2]\n"
        f"- [Key point 3]\n\n"
        f"---\n\n"
        f"## Detailed Explanation\n\n"
        f"[Explain the answer in detail. Use inline code, headers, bold text, bullet points, or tables as appropriate]\n\n"
        f"---\n\n"
        f"## Example\n\n"
        f"[Provide a code block or concrete example illustrating the concept]\n\n"
        f"---\n\n"
        f"## Real-world Applications\n\n"
        f"[Explain how this is used in practice]\n\n"
        f"---\n\n"
        f"## Summary\n\n"
        f"[Summarize the final takeaways]\n\n"
        f"Question: {question}"
    )


def get_explain_prompt(concept: str, level: str) -> str:
    """
    Format the prompt for explaining academic concepts tailored to difficulty level.
    """
    return (
        f"You are an expert educator. Explain the concept of '{concept}' at an '{level}' educational level. "
        f"Structure your response strictly matching this layout, keeping the language tailored to '{level}':\n"
        f"# {concept}\n\n"
        f"## Overview\n\n"
        f"[Provide a short introduction to the concept at '{level}' level]\n\n"
        f"---\n\n"
        f"## Key Concepts\n\n"
        f"- [Key point 1]\n"
        f"- [Key point 2]\n"
        f"- [Key point 3]\n\n"
        f"---\n\n"
        f"## Detailed Explanation\n\n"
        f"[Provide a detailed explanation appropriate for '{level}'. Use headings, tables, or lists where helpful]\n\n"
        f"---\n\n"
        f"## Example\n\n"
        f"[Provide an example or code block suitable for '{level}' level]\n\n"
        f"---\n\n"
        f"## Real-world Applications\n\n"
        f"[Describe practical real-world use cases]\n\n"
        f"---\n\n"
        f"## Summary\n\n"
        f"[Summarize key takeaways for '{level}' level]\n"
    )


def get_summarize_prompt(text: str, length: str) -> str:
    """
    Format the prompt for note summarizer.
    """
    return (
        f"Summarize the following text to a {length} length summary using clean Markdown. "
        f"Structure your response strictly matching this layout:\n"
        f"# Summary of the Notes\n\n"
        f"## Overview\n\n"
        f"[A brief overview of the input notes]\n\n"
        f"---\n\n"
        f"## Key Concepts\n\n"
        f"- [Core point 1]\n"
        f"- [Core point 2]\n"
        f"- [Core point 3]\n\n"
        f"---\n\n"
        f"## Detailed Explanation\n\n"
        f"[A detailed summary of the main arguments/concepts from the notes]\n\n"
        f"---\n\n"
        f"## Example\n\n"
        f"[An example, analogy, or case study from the text (or an illustrative one if not explicit)]\n\n"
        f"---\n\n"
        f"## Real-world Applications\n\n"
        f"[How these concepts apply in real-world scenarios]\n\n"
        f"---\n\n"
        f"## Summary\n\n"
        f"[Concluding takeaways]\n\n"
        f"Text to summarize:\n{text}"
    )


def get_quiz_prompt(topic: str, num_questions: int) -> str:
    """
    Format the prompt for generating structured MCQ quizzes.
    """
    return (
        f"Generate a list of {num_questions} Multiple Choice Questions (MCQs) about the topic: '{topic}'.\n"
        f"Format the output strictly as a JSON list of objects, containing exactly these keys: \n"
        f"[\n"
        f"  {{\n"
        f"    \"id\": 1,\n"
        f"    \"question_text\": \"Question text here\",\n"
        f"    \"options\": [\n"
        f"      {{\"label\": \"A\", \"text\": \"Option A\"}},\n"
        f"      {{\"label\": \"B\", \"text\": \"Option B\"}},\n"
        f"      {{\"label\": \"C\", \"text\": \"Option C\"}},\n"
        f"      {{\"label\": \"D\", \"text\": \"Option D\"}}\n"
        f"    ],\n"
        f"    \"correct_answer\": \"A\"\n"
        f"  }}\n"
        f"]\n"
        f"Do not include any extra markdown formatting or explanations."
    )


def get_roadmap_prompt(topic: str) -> str:
    """
    Format the prompt for generating step-by-step personalized learning roadmaps.
    """
    return (
        f"Create a step-by-step personalized learning roadmap for learning the topic: '{topic}'.\n"
        f"Format the output strictly as a JSON list of objects containing details of each step, exactly like this:\n"
        f"[\n"
        f"  {{\n"
        f"    \"step_number\": 1,\n"
        f"    \"title\": \"Step Title\",\n"
        f"    \"description\": \"Brief description of what to learn in this step.\",\n"
        f"    \"resources\": [\"URL or resource name 1\", \"URL or resource name 2\"]\n"
        f"  }}\n"
        f"]\n"
        f"Do not include any extra markdown formatting or explanations."
    )
