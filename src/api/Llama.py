import torch
import transformers


class Llama3:
    def __init__(self, model_path):
        self.model_id = model_path
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.model_id,
            model_kwargs={
                "torch_dtype": torch.float16,
                "device_map": "auto",  # This will automatically use GPU if available
            },
        )
        # Ensure EOS token ID is set correctly
        self.terminators = [
            self.pipeline.tokenizer.eos_token_id,
        ]

    def get_response(
        self, query, message_history=[], max_tokens=4096, temperature=0.6, top_p=0.9
    ):
        user_prompt = message_history + [{"role": "user", "content": query}]
        prompt = self.pipeline.tokenizer.apply_chat_template(
            user_prompt, tokenize=False, add_generation_prompt=True
        )
        outputs = self.pipeline(
            prompt,
            max_new_tokens=max_tokens,
            eos_token_id=self.terminators,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )
        response = outputs[0]["generated_text"][len(prompt):]
        return response, user_prompt + [{"role": "assistant", "content": response}]

    def description_info(self, descriptions):
        degree_results = []
        experience_results = []
        for description in descriptions:
            prompt_degree = (
                "From the following job description, extract the minimum degree requirement.\n"
                "- Your answer should be one word (e.g., 'Bachelor's', 'Master's', 'PhD', 'Diploma', etc.) or 'NA' if not mentioned.\n"
                "- Do not provide a range of degrees or any other additional context.\n"
                "- Do not add any extra words; respond with only one word or 'NA'.\n"
                f"Job Description: {description}\n"
                "Degree Requirement: "
            )

            degree_response, _ = self.get_response(prompt_degree)
            degree_results.append(degree_response)

            prompt_experience = (
                "From the following job description, extract the minimum number of years of work experience required.\n"
                "- Your answer should be a single number (e.g., '3', '5', '0') or 'NA' if not mentioned.\n"
                "- Do not provide a range of numbers (e.g., '3-5 years').\n"
                "- Do not add any extra words or context; respond with only one number or 'NA'.\n"
                f"Job Description: {description}\n"
                "Years of Experience: "
            )

            experience_response, _ = self.get_response(prompt_experience)
            experience_results.append(experience_response)

        return degree_results, experience_results
